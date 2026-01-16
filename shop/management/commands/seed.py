from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from django.utils.text import slugify
import random

from shop.models import Category, Product


def model_has_field(model, field_name: str) -> bool:
    return any(f.name == field_name for f in model._meta.get_fields())


class Command(BaseCommand):
    help = "Seed demo categories and products"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete existing products/categories before seeding")
        parser.add_argument("--categories", type=int, default=6, help="How many categories to create")
        parser.add_argument("--per-category", type=int, default=8, help="How many products per category to create")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        if opts["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing products and categories..."))
            Product.objects.all().delete()
            Category.objects.all().delete()

        has_old_price = model_has_field(Product, "old_price")

        # ---- Categories ----
        cat_names = [
            ("Напитки", "Ичимликлар", "Ichimliklar"),
            ("Молочное", "Сут маҳсулотлари", "Sut mahsulotlari"),
            ("Снэки", "Газаклар", "Gazaklar"),
            ("Фрукты", "Мевалар", "Mevalar"),
            ("Овощи", "Сабзавотлар", "Sabzavotlar"),
            ("Хлеб", "Нон", "Non"),
            ("Сладости", "Ширинликлар", "Shirinliklar"),
            ("Бакалея", "Бакалея", "Bakaleya"),
        ]

        categories_to_make = min(opts["categories"], len(cat_names))
        categories = []

        for i in range(categories_to_make):
            ru, uz, uz_latn = cat_names[i]
            # Подстрой под твою модель Category: судя по проекту, поля name_ru/name_uz/name_uz_latn есть
            c, _ = Category.objects.get_or_create(
                name_ru=ru,
                defaults={"name_uz": uz, "name_uz_latn": uz_latn},
            )
            # если категория уже была, но нет переводов — дополним
            if not getattr(c, "name_uz", None):
                c.name_uz = uz
            if not getattr(c, "name_uz_latn", None):
                c.name_uz_latn = uz_latn
            c.save()
            categories.append(c)

        # ---- Products ----
        base_products = [
            ("Кока-Кола 1л", "Кока-Кола 1л", "Coca-Cola 1L", 17000),
            ("Молоко 1л", "Сут 1л", "Sut 1L", 12000),
            ("Йогурт", "Йогурт", "Yogurt", 9000),
            ("Чипсы", "Чипслар", "Chips", 15000),
            ("Бананы", "Банан", "Banan", 14000),
            ("Яблоки", "Олма", "Olma", 11000),
            ("Помидоры", "Помидор", "Pomidor", 16000),
            ("Огурцы", "Бодринг", "Bodring", 13000),
            ("Хлеб", "Нон", "Non", 5000),
            ("Шоколад", "Шоколад", "Shokolad", 22000),
            ("Рис 1кг", "Гуруч 1кг", "Guruch 1kg", 24000),
        ]

        desc_ru = "Свежий товар, отличный выбор для заказа онлайн."
        desc_uz = "Янги товар, онлайн буюртма учун ажойиб танлов."
        desc_uz_latn = "Yangi mahsulot, onlayn buyurtma uchun ajoyib tanlov."

        created = 0
        per_cat = max(1, opts["per_category"])

        # чтобы имена не повторялись слишком одинаково — добавим суффикс
        existing_max_id = Product.objects.aggregate(m=Max("id"))["m"] or 0
        seq = existing_max_id + 1

        for c in categories:
            for _ in range(per_cat):
                base = random.choice(base_products)
                name_ru, name_uz, name_uz_latn, base_price = base

                # небольшая рандомизация
                price = int(base_price + random.randint(-1500, 2500))
                price = max(1000, price)

                stock = random.randint(0, 40)

                # Уникализируем названия
                ru = f"{name_ru}"
                uz = f"{name_uz}"
                uzl = f"{name_uz_latn}"

                p = Product(
                    category=c,
                    name_ru=ru,
                    name_uz=uz,
                    name_uz_latn=uzl,
                    description_ru=desc_ru,
                    description_uz=desc_uz,
                    description_uz_latn=desc_uz_latn,
                    price=price,
                    stock=stock,
                )

                # Если есть old_price — сделаем “акцию” примерно для 35% товаров
                if has_old_price and random.random() < 0.35:
                    # скидка 10–30%
                    old_price = int(price * (1 + random.uniform(0.12, 0.35)))
                    try:
                        p.old_price = old_price
                    except Exception:
                        pass

                p.save()
                created += 1
                seq += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Done: categories={len(categories)}, products_created={created}"))
        if has_old_price:
            self.stdout.write(self.style.SUCCESS("ℹ old_price field detected: some products seeded as promo"))
        else:
            self.stdout.write(self.style.WARNING("ℹ old_price field NOT found: promo pricing not seeded"))
