from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def home(request):
    """Главная: категории + товары (с поиском)."""
    q = (request.GET.get("q") or "").strip()

    categories = Category.objects.all().order_by("id")
    products = Product.objects.select_related("category").all()

    if q:
        products = products.filter(
            Q(name_ru__icontains=q)
            | Q(name_uz__icontains=q)
            | Q(name_uz_latn__icontains=q)
            | Q(description_ru__icontains=q)
            | Q(description_uz__icontains=q)
            | Q(description_uz_latn__icontains=q)
        )

    return render(
        request,
        "shop/home.html",
        {
            "categories": categories,
            "products": products.order_by("-id"),
            "q": q,
        },
    )


def category(request, category_id):
    category_obj = get_object_or_404(Category, id=category_id)
    products = category_obj.products.all().order_by("-id")

    return render(
        request,
        "shop/category.html",
        {
            "category": category_obj,  # важно: в шаблоне используем category
            "products": products,
        },
    )


def product(request, product_id):
    product_obj = get_object_or_404(Product, id=product_id)
    return render(request, "shop/product.html", {"product": product_obj})
