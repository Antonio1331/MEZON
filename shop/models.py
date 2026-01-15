from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import get_language


def _lang_key() -> str:
    """Return language key used by translated model fields."""
    lang = (get_language() or "ru").lower()
    # support uz_Latn / uz-latn
    if lang.startswith("uz") and ("latn" in lang or "uz_latn" in lang or "uz-latn" in lang):
        return "uz_latn"
    if lang.startswith("uz"):
        return "uz"
    return "ru"


class Category(models.Model):
    name_ru = models.CharField(max_length=200)
    name_uz = models.CharField(max_length=200, blank=True, default="")
    name_uz_latn = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    @property
    def name(self) -> str:
        key = _lang_key()
        val = getattr(self, f"name_{key}", "") or ""
        return val or self.name_ru

    def __str__(self) -> str:
        return self.name_ru


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name_ru = models.CharField(max_length=200)
    name_uz = models.CharField(max_length=200, blank=True, default="")
    name_uz_latn = models.CharField(max_length=200, blank=True, default="")

    description_ru = models.TextField(blank=True, default="")
    description_uz = models.TextField(blank=True, default="")
    description_uz_latn = models.TextField(blank=True, default="")

    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    # Критично: не позволяем отрицательные остатки.
    stock = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to="products/", blank=True, null=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ("-id",)

    @property
    def name(self) -> str:
        key = _lang_key()
        val = getattr(self, f"name_{key}", "") or ""
        return val or self.name_ru

    @property
    def description(self) -> str:
        key = _lang_key()
        val = getattr(self, f"description_{key}", "") or ""
        return val or self.description_ru

    @property
    def in_stock(self) -> bool:
        return int(self.stock or 0) > 0

    def can_purchase(self, qty: int = 1) -> bool:
        try:
            qty = int(qty)
        except Exception:
            qty = 1
        return qty > 0 and int(self.stock or 0) >= qty

    def __str__(self) -> str:
        return self.name_ru
