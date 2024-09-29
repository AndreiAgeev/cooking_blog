from rest_framework.pagination import LimitOffsetPagination


class LimitOffsetPagination(LimitOffsetPagination):
    default_limit = 6
