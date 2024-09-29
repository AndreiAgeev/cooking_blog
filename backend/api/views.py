import csv
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from djoser import views
from djoser import serializers as ds
from djoser.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.mixins import (CreateModelMixin,
                                   RetrieveModelMixin,
                                   ListModelMixin)
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny

from . import serializers
from .filters import IngredientFilter, RecipeFilter
from .permissions import UserStaffOrReadOnly
from recipes.models import User, Tag, Ingredient, Recipe


class UserViewSet(views.UserViewSet):
    pagination_class = LimitOffsetPagination

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
            return User.objects.filter(subscribers=user)
        return queryset

    def get_serializer_class(self):
        super().get_serializer_class()
        if self.action == 'create':
            return serializers.PostUserSerializer
        elif self.action == 'me':
            return serializers.GetUserSerializer
        elif self.action == 'set_password':
            return ds.SetPasswordSerializer
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
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'], detail=False, url_path='subscriptions')
    def subscriptions(self, request, *args, **kwargs):
        # Добавить лимит recipes_limit к полю recipes к пагинации
        return self.list(request, *args, **kwargs)

    @action(['post', 'delete'], detail=True,)
    def subscribe(self, request, *args, **kwargs):
        # Добавить лимит recipes_limit к полю recipes
        sub_user = get_object_or_404(User, pk=kwargs['id'])
        if request.method == 'POST':
            serializer = self.get_serializer(sub_user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            serializer = self.get_serializer(sub_user, data=request.data)
            serializer.is_valid(raise_exception=True)
            sub_user.subscribers.remove(request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (UserStaffOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'get_short_link':
            return serializers.ShortLinkSerializer
        elif self.action == 'favorite' or self.action == 'shopping_cart':
            return serializers.FavoriteRecipeSerializer
        elif self.action == 'download_shopping_cart':
            return serializers.ShoppingCartSerializer
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
        shopping_cart = request.user.shopping_cart.all().prefetch_related('composition__ingredient')
        serializer = self.get_serializer(shopping_cart)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        for ingredient in serializer.data['ingredients']:
            response.write(f"{ingredient['name']}, {ingredient['measurement_unit']} - {ingredient['amount']}\n")
        return response

    def post_delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['pk'])
        serializer = self.get_serializer(recipe, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if request.method == 'POST':
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def short_link_redirect(request, link):
    recipe = get_object_or_404(Recipe, short_link=link)
    url = reverse('recipe-detail', request=request, args=[recipe.id])
    return redirect(url)

