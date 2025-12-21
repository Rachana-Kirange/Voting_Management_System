from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),

    # include users app URLs
    path('users/', include('users.urls')),

    # root: send user to the right place depending on auth status
    path('', lambda request: redirect('users_home') if request.user.is_authenticated else redirect('login')),

    path('voting/', include('voting.urls')),

    path('elections/', include('elections.urls')),

    # dashboards are provided by the users app (see users/urls.py)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
