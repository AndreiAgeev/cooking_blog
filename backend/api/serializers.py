import base64

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import User, Tag, Ingredient


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            mediatype, imgstr = data.split(';base64,')
            extension = mediatype.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name='avatar.' + extension
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


class SubscriptionsSerializer(GetUserSerializer):
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
        user = self.context['request'].user
        sub_user = self.instance
        if sub_user == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        elif sub_user.user_subscribers.filter(subscriber=user):
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
