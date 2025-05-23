# Generated by Django 3.2.3 on 2024-09-24 14:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20240922_1256'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='recipes/', verbose_name='Картинка')),
                ('name', models.CharField(max_length=256, verbose_name='Название')),
                ('text', models.TextField(verbose_name='Описание')),
                ('cooking_time', models.PositiveSmallIntegerField(verbose_name='Время приготовления')),
                ('short_link', models.SlugField(verbose_name='Короткая ссылка')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
            },
        ),
        migrations.AlterField(
            model_name='subscribtions',
            name='subscriber',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_subscribtions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='subscribtions',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_subscribers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='RecipeComposition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveSmallIntegerField()),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='all_recipes', to='recipes.ingredient')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='composition', to='recipes.recipe')),
            ],
        ),
        migrations.AddField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(through='recipes.RecipeComposition', to='recipes.Ingredient', verbose_name='Ингредиенты'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(to='recipes.Tag', verbose_name='Теги'),
        ),
    ]
