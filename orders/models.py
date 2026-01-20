from django.db import models
from shop.models import Product
import secrets

class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "Yangi"),
        ("processing", "Qayta ishlanmoqda"),
        ("delivering", "Yetkazilmoqda"),
        ("done", "Tugallandi"),
        ("canceled", "Bekor qilindi"),
    ]

    PAYMENT_CASH = "cash"
    PAYMENT_CARD = "card"

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, "Naqd pul"),
        (PAYMENT_CARD, "Karta orqali"),
    ]

    customer_name = models.CharField(max_length=120, verbose_name="Mijoz ismi")
    phone = models.CharField(max_length=40, verbose_name="Telefon raqam")
    address = models.CharField(max_length=255, verbose_name="Manzil")
    comment = models.CharField(max_length=255, blank=True, verbose_name="Izoh")
    total = models.PositiveIntegerField(default=0, verbose_name="Jami summa")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Holati"
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default=PAYMENT_CASH,
        verbose_name="To'lov usuli"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    lat = models.FloatField(null=True, blank=True, verbose_name="Latitude")
    lng = models.FloatField(null=True, blank=True, verbose_name="Longitude")
    phone_verified = models.BooleanField(default=False, verbose_name="Telefon tasdiqlangan")
    public_token = models.CharField(max_length=64, unique=True, blank=True, db_index=True, verbose_name="Jamoa tokeni")
    discount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Chegirma (so'm)")

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def save(self, *args, **kwargs):
        if not self.public_token:
            self.public_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Buyurtma #{self.id} ({self.customer_name})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Buyurtma")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Mahsulot")
    qty = models.PositiveIntegerField(verbose_name="Soni")
    price_at_time = models.PositiveIntegerField(verbose_name="Narxi")

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"

    def line_total(self):
        return self.qty * self.price_at_time
