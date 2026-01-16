from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name_ru", "name_uz", "name_uz_latn")
    search_fields = ("name_ru", "name_uz", "name_uz_latn")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "thumb", "name_ru", "category", "price", "stock", "in_stock_badge")
    list_display_links = ("id", "name_ru")
    list_filter = ("category",)
    search_fields = ("name_ru", "name_uz", "name_uz_latn")
    list_editable = ("price", "stock")

    @admin.display(description="Фото")
    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )
        return "—"

    @admin.display(description="Наличие")
    def in_stock_badge(self, obj):
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            "#16a34a" if (obj.stock or 0) > 0 else "#ef4444",
            "В наличии" if (obj.stock or 0) > 0 else "Нет",
        )
