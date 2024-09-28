import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов в базу данных'
    filename = 'ingredients.json'

    def handle(self, *args, **kwargs):
        with open(f'../data/{self.filename}') as jsonfile:
            reader = json.load(jsonfile)
            Ingredient.objects.bulk_create(
                Ingredient(**data) for data in reader
            )
        self.stdout.write(
            self.style.SUCCESS(
                'Данные успешно загружены в БД'
            )
        )
