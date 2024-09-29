import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов в базу данных'
    filename = 'ingredients.csv'

    def handle(self, *args, **kwargs):
        with open(f'../data/{self.filename}') as csvfile:
            reader = csv.DictReader(csvfile)
            Ingredient.objects.bulk_create(
                Ingredient(**data) for data in reader
            )
        self.stdout.write(
            self.style.SUCCESS(
                'Данные успешно загружены в БД'
            )
        )
