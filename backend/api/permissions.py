from rest_framework import permissions


class UserStaffOrReadOnly(permissions.BasePermission):
    """Даёт следующие доступы:
    1) для анонимных пользовтелей только возможность просмотра контента;
    2) для аутентифицированных пользователей - просмотр контента, создание
       и редактирование своего контента;
    3) для админов - всё выше + редактирование любого контента
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_staff
            or request.user.is_superuser
        )
