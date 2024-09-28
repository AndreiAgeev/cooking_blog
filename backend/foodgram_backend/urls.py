from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from api.views import short_link_redirect

urlpatterns = [
    path('s/<str:link>/', short_link_redirect),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
