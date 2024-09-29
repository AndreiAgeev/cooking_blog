from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    email = models.EmailField('Электронная почта', max_length=254, unique=True)
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )
    subscribers = models.ManyToManyField(
        'User',
        verbose_name='Подписчики',
        through='Subscribtions',
        through_fields=('user', 'subscriber')
    )
    favorites = models.ManyToManyField(
        'Recipe',
        verbose_name='Избранное',
    )
    shopping_cart = models.ManyToManyField(
        'Recipe',
        verbose_name='Список покупок',
        related_name='in_shopping_cart'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Subscribtions(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscribers'
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscriptions'
    )


class Tag(models.Model):
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField('Слаг', max_length=32, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128, unique=True)
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeComposition'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
    )
    name = models.CharField('Название', max_length=256)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    short_link = models.SlugField('Короткая ссылка')

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeComposition(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='composition'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.RESTRICT,
        related_name='all_recipes'
    )
    amount = models.PositiveSmallIntegerField()
