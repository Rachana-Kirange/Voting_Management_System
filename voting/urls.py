from django.urls import path
from . import views

urlpatterns = [
    path('vote/<int:election_id>/', views.vote, name='vote'),
]
