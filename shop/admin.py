from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name_ru",
        "name_uz",
        "name_uz_latn",
        "product_count",
    )
    list_display_links = ("id", "name_ru")              # name_ru — кликабельная ссылка
    list_editable = ("name_uz", "name_uz_latn")         # редактировать можно только эти два
    search_fields = ("name_ru", "name_uz", "name_uz_latn")
    ordering = ("name_ru",)

    @admin.display(description="Товаров")
    def product_count(self, obj):
        return obj.products.count() or "—"

    # Если у вас есть поле image в модели Category, можно добавить в fieldsets:
    fieldsets = (
        (None, {
            'fields': ('name_ru', 'name_uz', 'name_uz_latn'),
        }),
        ('Дополнительно', {
            'fields': ('image',),
            'classes': ('collapse',),
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thumb",
        "name_ru",
        "category",
        "price",
        "stock",
        "in_stock_badge",
        # "old_price_display",    # убрано пока — нет old_price
        # "is_on_sale_badge",     # убрано — нет is_on_sale
    )
    list_display_links = ("id", "name_ru")

    # Только те поля, которые реально есть в модели и уже в list_display
    list_editable = ("price", "stock", "category")

    list_filter = ("category",)  # только существующее поле
    search_fields = ("name_ru", "name_uz", "name_uz_latn")
    # ordering = ("-created_at",)          # убрано — нет created_at
    # readonly_fields = ("created_at", "updated_at")  # убрано — нет этих полей

    fieldsets = (
        (None, {
            "fields": (
                "name_ru", "name_uz", "name_uz_latn",
                "category",
            )
        }),
        (_("Цены и наличие"), {
            "fields": ("price", "stock"),
        }),
        (_("Изображение"), {
            "fields": ("image",),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Фото")
    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px; height:48px; object-fit:cover; border-radius:6px;" />',
                obj.image.url
            )
        return "—"

    @admin.display(description=_("Наличие"))
    def in_stock_badge(self, obj):
        stock = obj.stock or 0
        if stock > 0:
            return format_html(
                '<span style="color:#16a34a; font-weight:600;">В наличии ({})</span>',
                stock
            )
        return format_html(
            '<span style="color:#ef4444; font-weight:600;">Нет в наличии</span>'
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category")