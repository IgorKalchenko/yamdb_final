import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from reviews.models import Category, Comment, Genre, Review, Title, User

Models = {
    User: 'users.csv',
    Category: 'category.csv',
    Genre: 'genre.csv',
    Title: 'titles.csv',
    Review: 'review.csv',
    Comment: 'comments.csv',
    Title.genre.through: 'genre_title.csv',
}


class Command(BaseCommand):
    help = 'Импорт данных из csv-файлов'

    def handle(self, *args, **options):
        answer = input('Очистить базу данных перед импортом? [Y/N]: ').lower()
        if answer == 'y':
            User.objects.all().delete()
            Category.objects.all().delete()
            Genre.objects.all().delete()
            Title.objects.all().delete()
        elif answer == 'n':
            self.stdout.write('Операция пропущена.')
        else:
            return 'Введено некорректное значение.'
        for model, csv_file in Models.items():
            with open(
                os.path.join(settings.STATIC_ROOT, 'data', csv_file),
                'r', encoding='utf-8'
            ) as csv_file:
                reader = csv.DictReader(csv_file)
                model.objects.bulk_create(
                    model(**data) for data in reader
                )
            self.stdout.write(
                f'Выполнен импорт данных для таблицы {model.__name__}.'
            )
        return f'Выполнен импорт данных для таблицы {model.__name__}.'
