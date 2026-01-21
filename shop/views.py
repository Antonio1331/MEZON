from django.db.models import Q, F
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Category, Product
import json

def category(request, category_id):
    category_obj = get_object_or_404(Category, id=category_id)
    qs = category_obj.products.all()

    promo_products = qs.filter(
        old_price__isnull=False,
        old_price__gt=F("price"),
    ).order_by("-id")

    products = qs.order_by("-id")

    return render(
        request,
        "shop/category.html",
        {
            "category": category_obj,
            "promo_products": promo_products,  # ✅ добавили
            "products": products,
        },
    )

def product(request, product_id):
    product_obj = get_object_or_404(Product, id=product_id)
    return render(request, "shop/product.html", {"product": product_obj})

def home(request):
    """Главная: категории + товары (с поиском)."""
    q = (request.GET.get("q") or "").strip()

    categories = Category.objects.all().order_by("id")
    base_qs = Product.objects.select_related("category").all()

    if q:
        base_qs = base_qs.filter(
            Q(name_ru__icontains=q)
            | Q(name_uz__icontains=q)
            | Q(name_uz_latn__icontains=q)
            | Q(description_ru__icontains=q)
            | Q(description_uz__icontains=q)
            | Q(description_uz_latn__icontains=q)
        )

    promo_products = base_qs.filter(
        old_price__isnull=False,
        old_price__gt=F("price"),
    ).order_by("-id")

    products = base_qs.order_by("-id")

    return render(
        request,
        "shop/home.html",
        {
            "categories": categories,
            "promo_products": promo_products,  # ✅ добавили
            "products": products,
            "q": q,
        },
    )


@require_http_methods(["POST"])
def add_to_cart(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    product_id = data.get('product_id')
    qty = int(data.get('quantity', 1))

    if not product_id:
        return JsonResponse({'success': False, 'message': 'Не указан ID товара'}, status=400)

    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + qty
    request.session["cart"] = cart
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': f'{product.name} добавлен в корзину',
        'cart_count': sum(cart.values()),
        'added_quantity': qty,
        'product_name': product.name_ru or product.name_uz or product.name or 'Товар'
    })