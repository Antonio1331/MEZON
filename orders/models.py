from django.db import models
from shop.models import Product
import secrets

class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("processing", "В обработке"),
        ("delivering", "Доставляется"),
        ("done", "Завершён"),
        ("canceled", "Отменён"),
    ]

    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    address = models.CharField(max_length=255)
    comment = models.CharField(max_length=255, blank=True)
    total = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    public_token = models.CharField(max_length=64, unique=True, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.public_token:
            self.public_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Order #{self.id} ({self.customer_name})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    price_at_time = models.PositiveIntegerField()

    def line_total(self):
        return self.qty * self.price_at_time
