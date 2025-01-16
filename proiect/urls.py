from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler403 = 'app_0.views.custom_403_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', include('app_0.urls')),
    path('confirma_mail/<str:cod>/', include('app_0.urls')),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)