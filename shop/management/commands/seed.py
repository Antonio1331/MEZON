from django.core.management.base import BaseCommand
from shop.models import Category, Product
import random

class Command(BaseCommand):
    help = "Заполнить магазин тестовыми категориями и товарами"

    def handle(self, *args, **kwargs):
        Category.objects.all().delete()
        Product.objects.all().delete()

        categories = ["Овощи", "Фрукты", "Молочные", "Напитки", "Хлеб"]
        cat_objs = []

        for name in categories:
            c = Category.objects.create(name=name)
            cat_objs.append(c)

        products = [
            "Молоко", "Хлеб", "Яблоки", "Бананы", "Помидоры",
            "Огурцы", "Сок", "Йогурт", "Сыр", "Вода"
        ]

        for i in range(30):
            Product.objects.create(
                category=random.choice(cat_objs),
                name=random.choice(products) + f" #{i+1}",
                description="Свежий продукт высокого качества",
                price=random.randint(3000, 25000),
                stock=random.randint(5, 100),
                is_active=True
            )

        self.stdout.write(self.style.SUCCESS("✔ Магазин заполнен тестовыми данными"))
