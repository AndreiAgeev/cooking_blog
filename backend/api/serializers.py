import base64
from collections import defaultdict

from django.db.models import F, Sum
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import User, Tag, Ingredient, Recipe, RecipeComposition


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            mediatype, imgstr = data.split(';base64,')
            extension = mediatype.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name='image.' + extension
            )
            return super().to_internal_value(data)


class GetUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        try:
            obj.user_subscribers.get(subscriber=user)
            return True
        except ObjectDoesNotExist:
            return False


class PostUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password', 'id')


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class SubscriptionSerializer(GetUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(GetUserSerializer.Meta):
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar',
                  'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name',
                            'last_name', 'avatar', 'is_subscribed')

    def get_recipes(self, obj):
        return list()

    def get_recipes_count(self, obj):
        return 0

    def validate(self, attrs):
        subscriber_list = User.objects.filter(
            subscribers=self.context['request'].user,
            id=self.instance.id
        )
        if self.instance == self.context['request'].user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        elif (self.context['request'].method == 'DELETE'
                and not subscriber_list):
            raise serializers.ValidationError(
                'Вы не подписаны на данного пользователя'
            )
        elif (self.context['request'].method == 'POST'
              and subscriber_list):
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя'
            )
        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.subscribers.add(self.context['request'].user)
        return instance


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

# Наверное забыл убрать - нигде не испольуется
# class RecipeCompositionSerializer(serializers.ModelSerializer):
#     ingredient = IngredientSerializer(read_only=True)

#     class Meta:
#         model = RecipeComposition
#         fields = ['ingredient', 'amount']


class IngredientInputSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient', required=True
    )
    amount = serializers.IntegerField(min_value=1, required=True)
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeComposition
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('name', 'measurement_unit')

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = GetUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_null=False,
        required=True,
    )
    ingredients = IngredientInputSerializer(many=True, source='composition')
    image = Base64ImageField(allow_null=False, allow_empty_file=False)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart')

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Укажите теги')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться')
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Добавьте изображение')
        return value

    def validate_ingredients(self, value):
        print(value)
        id_list = list()
        for obj in value:
            if obj['ingredient'] in id_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться'
                )
            id_list.append(obj['ingredient'])
        return value

    def get_is_favorited(self, obj):
        return False

    def get_is_in_shopping_cart(self, obj):
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        return representation

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('composition')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.short_link = base64.b64encode(str(recipe.id).encode()).decode()
        recipe.save()
        recipe.tags.add(*tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('composition')
        recipe = super().update(instance, validated_data)
        recipe.tags.set(tags)
        recipe.composition.all().delete()
        self.save_ingredients(recipe, ingredients)
        return recipe

    def save_ingredients(self, recipe, ingredients):
        recipe_compositions = [
            RecipeComposition(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeComposition.objects.bulk_create(recipe_compositions)


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('short_link',)
        read_only_fields = ('short_link',)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['short-link'] = (
            self.context['request'].get_host()
            + '/s/'
            + response.pop('short_link')
        )
        return response


class FavoriteRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

    def get_obj_list(self, action):
        if action == 'favorite':
            return User.objects.filter(
                favorites=self.instance,
                id=self.context['request'].user.id
            )
        elif action == 'shopping_cart':
            return User.objects.filter(
                shopping_cart=self.instance,
                id=self.context['request'].user.id
            )

    def validate(self, attrs):
        VIEW_ACTION_NAME = {
            'favorite': 'избранном',
            'shopping_cart': 'списке покупок'
        }
        obj_list = self.get_obj_list(self.context['view'].action)
        if (self.context['request'].method == 'DELETE'
                and not obj_list):
            raise serializers.ValidationError(
                "Данный рецепт не находится в "
                 f"{VIEW_ACTION_NAME[self.context['view'].action]}"
            )
        elif (self.context['request'].method == 'POST'
                and obj_list):
            raise serializers.ValidationError(
                "Данный рецепт уже находится в "
                f"{VIEW_ACTION_NAME[self.context['view'].action]}"
            )
        return super().validate(attrs)

    def update(self, instance, validated_data):
        if self.context['request'].method == 'POST':
            if self.context['view'].action == 'favorite':
                self.context['request'].user.favorites.add(instance)
            elif self.context['view'].action == 'shopping_cart':
                self.context['request'].user.shopping_cart.add(instance)

        elif self.context['request'].method == 'DELETE':
            if self.context['view'].action == 'favorite':
                self.context['request'].user.favorites.remove(instance)
            elif self.context['view'].action == 'shopping_cart':
                self.context['request'].user.shopping_cart.remove(instance)
        return instance


class AggregatedIngredientsSerializer(serializers.Serializer):
    name = serializers.CharField()
    measurement_unit = serializers.CharField()
    amount = serializers.IntegerField()


class ShoppingCartSerializer(serializers.Serializer):
    ingredients = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        ingredients = (
            RecipeComposition.objects
            .filter(recipe__in=obj)
            .values(
                name=F('ingredient__name'),
                measurement_unit=F('ingredient__measurement_unit')
            )
            .annotate(amount=Sum('amount'))
        )
        return AggregatedIngredientsSerializer(
            list(ingredients), many=True
        ).data
