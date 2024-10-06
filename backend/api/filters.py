from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов.

    Обеспечивает фильтрацию по вхождению введенных данных в начало
    названия ингредиента.
    """
    name = filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов.

    - Доступна фильтрация по id автора;
    - доступна фильтрация по одному или нескольким тегам по условию ИЛИ.
    - доступна фильтрация по рецептам, находящимся в избранном у пользователя.
    - доступна фильтрация по рецептам, находящимся в списке покупок
      пользователя.
    """
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.CharFilter(field_name='tags__slug', method='filter_tags')
    is_favorited = filters.NumberFilter(method='filter_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_favorited(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return self.request.user.favorites.all()
        else:
            return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return self.request.user.shopping_cart.all()
        else:
            return queryset

    def filter_tags(self, queryset, name, value):
        return queryset.filter(
            tags__slug__in=self.request.GET.getlist('tags')
        )
