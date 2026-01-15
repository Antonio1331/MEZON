from django.shortcuts import redirect, render, get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.translation import gettext as _

from shop.models import Product
from .models import Order, OrderItem

DELIVERY_FEE = 5000


def _get_cart(request):
    # {product_id(str): qty(int)}
    cart = request.session.get("cart", {})
    return cart if isinstance(cart, dict) else {}


def _save_cart(request, cart: dict):
    request.session["cart"] = cart
    request.session.modified = True


def _cart_count(cart: dict) -> int:
    try:
        return sum(int(v) for v in cart.values())
    except Exception:
        return 0


def _build_cart_context(cart: dict):
    """Готовит items/total и флаг has_oos (out of stock)."""
    ids = [int(k) for k in cart.keys()] if cart else []
    products = list(Product.objects.filter(id__in=ids)) if ids else []

    items = []
    total = 0
    has_oos = False

    for p in products:
        qty = int(cart.get(str(p.id), 0) or 0)
        if qty <= 0:
            continue

        # "нет в наличии" если stock <= 0 или заказано больше чем остаток
        if (p.stock or 0) <= 0 or qty > (p.stock or 0):
            has_oos = True

        line = qty * p.price
        total += line
        items.append({"p": p, "qty": qty, "line": line})

    return {
        "items": items,
        "total": total,
        "has_oos": has_oos,
        "delivery_fee": DELIVERY_FEE,
    }


@require_POST
def add_to_cart(request, product_id):
    """Добавить 1 шт. в корзину. НЕ даём увеличить qty выше остатка."""
    product = get_object_or_404(Product, id=product_id)

    cart = _get_cart(request)
    pid = str(product_id)
    current_qty = int(cart.get(pid, 0) or 0)

    stock = int(product.stock or 0)
    if stock <= 0:
        return JsonResponse({
            "ok": False,
            "cart_count": _cart_count(cart),
            "error": _("Товара нет в наличии"),
        }, status=409)

    if current_qty + 1 > stock:
        return JsonResponse({
            "ok": False,
            "cart_count": _cart_count(cart),
            "error": _("Нельзя добавить больше, чем есть в наличии (%(stock)s)") % {"stock": stock},
        }, status=409)

    cart[pid] = current_qty + 1
    _save_cart(request, cart)
    return JsonResponse({"ok": True, "cart_count": _cart_count(cart)})


def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    pid = str(product_id)
    if pid in cart:
        cart.pop(pid)
        _save_cart(request, cart)
    return redirect("cart")


def cart(request):
    cart = _get_cart(request)
    ctx = _build_cart_context(cart)
    return render(request, "orders/cart.html", ctx)


def checkout(request):
    cart = _get_cart(request)
    if not cart:
        return redirect("cart")

    # Чтобы не оформить заказ при нулевом остатке даже с UI-обходом
    ctx = _build_cart_context(cart)
    if request.method == "GET":
        return render(request, "orders/checkout.html", ctx)

    # POST
    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()
    comment = request.POST.get("comment", "").strip()

    if not name or not phone or not address:
        ctx["error"] = _("Заполните имя, телефон и адрес.")
        return render(request, "orders/checkout.html", ctx)

    # Если есть out-of-stock — сразу назад
    if ctx.get("has_oos"):
        ctx["error"] = _("В корзине есть товары, которых нет в наличии. Удалите их и попробуйте снова.")
        return render(request, "orders/checkout.html", ctx)

    lat = request.POST.get("lat")
    lng = request.POST.get("lng")
    lat = float(lat) if lat else None
    lng = float(lng) if lng else None

    ids = [int(k) for k in cart.keys()]

    with transaction.atomic():
        # Лочим строки товаров, чтобы не было гонки между покупками
        products = list(Product.objects.select_for_update().filter(id__in=ids))

        # Повторная проверка наличия внутри транзакции (must-have)
        for p in products:
            qty = int(cart.get(str(p.id), 0) or 0)
            if qty <= 0:
                continue
            if (p.stock or 0) < qty:
                ctx = _build_cart_context(cart)
                ctx["error"] = _("Недостаточно товара: %(name)s. В наличии: %(stock)s") % {
                    "name": p.name,
                    "stock": p.stock,
                }
                return render(request, "orders/checkout.html", ctx)

        order = Order.objects.create(
            customer_name=name,
            phone=phone,
            address=address,
            comment=comment,
            total=0,
            status="new",
            lat=lat,
            lng=lng,
        )

        total = 0
        for p in products:
            qty = int(cart.get(str(p.id), 0) or 0)
            if qty <= 0:
                continue

            p.stock = int(p.stock or 0) - qty
            if p.stock < 0:
                # На всякий случай (не должно случиться из-за проверок выше)
                raise ValueError("Stock went negative")
            p.save(update_fields=["stock"])

            OrderItem.objects.create(
                order=order,
                product=p,
                qty=qty,
                price_at_time=p.price,
            )
            total += qty * p.price

        order.total = total + DELIVERY_FEE
        order.save(update_fields=["total"])

    # очистить корзину
    _save_cart(request, {})
    return redirect("success", order_id=order.id)


def success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/success.html", {
        "order": order,
        "delivery_fee": DELIVERY_FEE,
    })


@require_http_methods(["GET", "POST"])
def track_order(request):
    """Поиск заказа: номер + телефон."""
    if request.method == "GET":
        return render(request, "orders/track.html")

    order_id_raw = (request.POST.get("order_id") or "").strip()
    phone = (request.POST.get("phone") or "").strip()

    if not order_id_raw.isdigit() or not phone:
        return render(request, "orders/track.html", {
            "error": _("Введите номер заказа и телефон."),
        })

    order_id = int(order_id_raw)
    order = Order.objects.filter(id=order_id, phone=phone).first()

    if not order:
        return render(request, "orders/track.html", {
            "error": _("Заказ не найден. Проверьте номер и телефон."),
        })

    allowed = request.session.get("allowed_orders", [])
    if not isinstance(allowed, list):
        allowed = []
    if order_id not in allowed:
        allowed.append(order_id)
    request.session["allowed_orders"] = allowed
    request.session.modified = True

    return redirect("order_detail", order_id=order.id)


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    allowed = request.session.get("allowed_orders", [])
    can_view = isinstance(allowed, list) and (order_id in allowed)
    if not can_view:
        return redirect("track_order")

    items_qs = OrderItem.objects.select_related("product").filter(order=order)

    rows = []
    for it in items_qs:
        line = int(it.qty) * int(it.price_at_time)
        rows.append({"it": it, "line": line})

    return render(request, "orders/order_detail.html", {
        "order": order,
        "rows": rows,
        "delivery_fee": DELIVERY_FEE,
    })


@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    allowed = request.session.get("allowed_orders", [])
    can_act = isinstance(allowed, list) and (order_id in allowed)
    if not can_act:
        return redirect("track_order")

    cancelable_statuses = {"new"}
    if order.status not in cancelable_statuses:
        return redirect("order_detail", order_id=order.id)

    with transaction.atomic():
        items = list(OrderItem.objects.select_related("product").select_for_update().filter(order=order))
        for it in items:
            p = it.product
            p.stock = int(p.stock or 0) + int(it.qty or 0)
            p.save(update_fields=["stock"])

        order.status = "canceled"
        order.save(update_fields=["status"])

    return redirect("order_detail", order_id=order.id)


def order_detail_token(request, token):
    order = get_object_or_404(Order, public_token=token)
    items_qs = OrderItem.objects.select_related("product").filter(order=order)

    rows = []
    for it in items_qs:
        line = int(it.qty) * int(it.price_at_time)
        rows.append({"it": it, "line": line})

    return render(request, "orders/order_detail.html", {
        "order": order,
        "rows": rows,
        "delivery_fee": DELIVERY_FEE,
    })


@require_POST
def cancel_order_token(request, token):
    """Отмена по публичному токену + возврат остатков на склад."""
    order = get_object_or_404(Order, public_token=token)

    if order.status != "new":
        request.session["toast_msg"] = _("Этот заказ уже нельзя отменить.")
        return redirect("order_detail_token", token=token)

    with transaction.atomic():
        items = list(OrderItem.objects.select_related("product").select_for_update().filter(order=order))
        for it in items:
            p = it.product
            p.stock = int(p.stock or 0) + int(it.qty or 0)
            p.save(update_fields=["stock"])

        order.status = "canceled"
        order.save(update_fields=["status"])

    request.session["toast_msg"] = _("Заказ отменен")
    return redirect("order_detail_token", token=token)
