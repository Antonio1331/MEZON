from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("product_thumb", "line_total_display")
    fields = ("product", "product_thumb", "qty", "price_at_time", "line_total_display")

    def product_thumb(self, obj):
        if obj.product and obj.product.image:
            return format_html(
                '<img src="{}" style="width:32px;height:32px;object-fit:cover;border-radius:6px;" />',
                obj.product.image.url
            )
        return "—"
    product_thumb.short_description = "Rasm"

    def line_total_display(self, obj):
        if obj.pk:
            return obj.qty * obj.price_at_time
        return ""
    line_total_display.short_description = "Jami"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "phone",
        "address",
        "total",
        "get_payment_method_display",  # <- добавили
        "status",
        "created_at"
    )
    list_filter = ("status", "created_at", "payment_method")
    search_fields = ("customer_name", "phone", "address", "public_token")
    readonly_fields = ("public_token", "created_at")
    inlines = (OrderItemInline,)

    def get_payment_method_display(self, obj):
        return obj.get_payment_method_display()
    get_payment_method_display.short_description = "To'lov usuli"
