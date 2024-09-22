from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from djoser import views
from djoser import serializers as ds
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (CreateModelMixin,
                                   RetrieveModelMixin,
                                   ListModelMixin)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny

from . import serializers
from .filters import IngredientFilter
from recipes.models import User, Tag, Ingredient


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
            return serializers.SubscriptionsSerializer
        return serializers.GetUserSerializer

    def perform_create(self, serializer):
        print('tut')
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
    def subscribe(self, request, pk=None, *args, **kwargs):
        # Добавить лимит recipes_limit к полю recipes
        sub_user = get_object_or_404(User, pk=kwargs['id'])
        if request.method == 'POST':
            serializer = self.get_serializer(sub_user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
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
