from django.db.models import Prefetch
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.mixins import (ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from . import serializers, utils
from .filters import IngredientFilter, RecipeFilter
from .paginators import LimitPagination
from .permissions import UserStaffOrReadOnly
from recipes.models import Ingredient, Recipe, RecipeComposition, Tag, User


class UserViewSet(DjoserUserViewSet):
    """
    ViewSet, отвечающий за работу с пользователями.

    Наследуется от UserViewSet из библиотеки Djoser.
    - set_avatar() - обеспечивает функцию изменения аватара;
    - subscriptions() - обеспечивает функцию просмотра подписок пользователя;
    - subscribe() - обеспечивает функцию дабавления/удаления подписок на
      других пользователей.
    """
    pagination_class = LimitPagination

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if self.action == 'subscriptions':
            return (
                User.objects.filter(subscribers=user)
                .prefetch_related('recipes')
            )
        return queryset

    def get_serializer_class(self):
        super().get_serializer_class()
        if self.action == 'create':
            return serializers.PostUserSerializer
        elif self.action == 'me':
            return serializers.GetUserSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        elif self.action == 'set_avatar':
            return serializers.AvatarSerializer
        elif self.action == 'subscriptions' or self.action == 'subscribe':
            return serializers.SubscriptionSerializer
        return serializers.GetUserSerializer

    def get_permissions(self):
        if (self.action == 'me' and self.request
                and self.request.method == 'GET'):
            self.permission_classes = settings.PERMISSIONS.user_me_get
        return super().get_permissions()

    def perform_create(self, serializer):
        password = serializer.validated_data['password']
        serializer.save(password=make_password(password))

    @action(['put', 'delete'], detail=False, url_path='me/avatar')
    def set_avatar(self, request, *args, **kwargs):
        return self.post_delete(request, *args, **kwargs)

    @action(['get'], detail=False, url_path='subscriptions')
    def subscriptions(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(['post', 'delete'], detail=True,)
    def subscribe(self, request, *args, **kwargs):
        return self.post_delete(request, *args, **kwargs)

    def post_delete(self, request, *args, **kwargs):
        if self.action == 'subscribe':
            instance = get_object_or_404(User, pk=kwargs['id'])
        elif self.action == 'set_avatar':
            instance = request.user

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if request.method in 'POST':
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'PUT':
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """ViewSet для тегов."""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """ViewSet для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """
    ViewSet, отвечающий за работу с рецептами.

    Даёт возможность просмтотра, создания, изменения и удаления рецептов.
    - get_short_link() - возвращает короткую ссылку на рецепт;
    - favorite() - добавляет рецепт в список избранногопользователя;
    - shopping_cart() - добавляет рецепт в список покупок пользователя;
    - download_shopping_cart() - возвращает пользователю текстовый файл
      формата .txt, содержащий список ингредиентов всех рецептов, находящихся
      у пользователя в списке покупок.
    """
    queryset = (
        Recipe.objects.all()
        .select_related('author')
        .prefetch_related(
            'tags',
            Prefetch(
                'composition',
                queryset=RecipeComposition.objects.select_related('ingredient')
            )
        )
    )
    permission_classes = (UserStaffOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPagination

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'get_short_link':
            return serializers.ShortLinkSerializer
        elif self.action == 'favorite' or self.action == 'shopping_cart':
            return serializers.FavoriteRecipeSerializer
        elif self.action == 'download_shopping_cart':
            return serializers.DownloadShoppingCartSerializer
        return serializers.RecipeSerializer

    @action(['get'], detail=True, url_path='get-link')
    def get_short_link(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @action(['post', 'delete'], detail=True, url_path='favorite')
    def favorite(self, request, *args, **kwargs):
        return self.post_delete(request, *args, **kwargs)

    @action(['post', 'delete'], detail=True, url_path='shopping_cart')
    def shopping_cart(self, request, *args, **kwargs):
        return self.post_delete(request, *args, **kwargs)

    @action(['get'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request, *args, **kwargs):
        shopping_cart = (
            request.user.shopping_cart
            .all()
            .prefetch_related('composition__ingredient')
        )
        ingredients = utils.get_ingredients(shopping_cart)
        serializer = self.get_serializer(ingredients, many=True)
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        for ingredient in serializer.data:
            response.write(
                f"{ingredient['name']}, "
                f"{ingredient['measurement_unit']} - {ingredient['amount']}\n"
            )
        return response

    # def get_ingredients(self, queryset):
    #     ingredients = (
    #         RecipeComposition.objects
    #         .filter(recipe__in=queryset)
    #         .values(
    #             name=F('ingredient__name'),
    #             measurement_unit=F('ingredient__measurement_unit')
    #         )
    #         .annotate(amount=Sum('amount'))
    #     )
    #     return list(ingredients)

    def post_delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['pk'])
        serializer = self.get_serializer(recipe, data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            if self.action == 'favorite':
                request.user.favorites.add(recipe)
            elif self.action == 'shopping_cart':
                request.user.shopping_cart.add(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if self.action == 'favorite':
                request.user.favorites.remove(recipe)
            elif self.action == 'shopping_cart':
                request.user.shopping_cart.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def short_link_redirect(request, link):
    """Редирект на рецепт, соответствующий короткой ссылке"""
    recipe = get_object_or_404(Recipe, short_link=link)
    url = f'{request.scheme}://{request.get_host()}/recipes/{recipe.id}'
    return redirect(url)
