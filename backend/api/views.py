from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from djoser import views
from djoser import serializers as ds
from rest_framework.mixins import (CreateModelMixin,
                                   RetrieveModelMixin,
                                   ListModelMixin)
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from . import serializers
from recipes.models import User


class UserViewSet(views.UserViewSet):
    http_method_names = ('get', 'post')
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        super().get_serializer_class()
        if self.action == 'create':
            return serializers.PostUserSerializer
        elif self.action == 'me':
            return serializers.GetUserSerializer
        elif self.action == 'set_password':
            return ds.SetPasswordSerializer
        return serializers.GetUserSerializer

    def perform_create(self, serializer):
        password = serializer.validated_data['password']
        serializer.save(password=make_password(password))
