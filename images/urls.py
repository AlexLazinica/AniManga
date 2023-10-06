from django.urls import path
from . import views

urlpatterns = [
    path('anime-images/', views.anime_images, name='anime_images'),
]
