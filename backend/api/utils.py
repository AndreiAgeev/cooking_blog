from django.db.models import F, Sum

from recipes.models import RecipeComposition, User


def save_ingredients(recipe, ingredients):
    recipe_compositions = [
        RecipeComposition(
            recipe=recipe,
            ingredient=ingredient['ingredient'],
            amount=ingredient['amount']
        )
        for ingredient in ingredients
    ]
    RecipeComposition.objects.bulk_create(recipe_compositions)


def get_obj_list(instance, request, action):
    if action == 'favorite':
        return User.objects.filter(
            favorites=instance,
            id=request.user.id
        )
    elif action == 'shopping_cart':
        return User.objects.filter(
            shopping_cart=instance,
            id=request.user.id
        )


def get_ingredients(queryset):
    ingredients = (
        RecipeComposition.objects
        .filter(recipe__in=queryset)
        .values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        )
        .annotate(amount=Sum('amount'))
    )
    return list(ingredients)
