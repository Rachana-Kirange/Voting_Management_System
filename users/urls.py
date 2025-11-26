from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='users_home'),   # corrected
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
]
