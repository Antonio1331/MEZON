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


from django.db import models

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE
    )

    name_ru = models.CharField(max_length=255)
    name_uz = models.CharField(max_length=255, blank=True)
    name_uz_latn = models.CharField(max_length=255, blank=True)

    description_ru = models.TextField(blank=True)
    description_uz = models.TextField(blank=True)
    description_uz_latn = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ ДОБАВИТЬ
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    @property
    def name(self):
        lang = get_language()

        if lang == "uz":
            return self.name_uz or self.name_ru
        if lang == "uz-latn":
            return self.name_uz_latn or self.name_ru

        return self.name_ru

    def __str__(self):
        return self.name_ru