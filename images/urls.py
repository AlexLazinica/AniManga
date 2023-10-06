from django.urls import path
from . import views

urlpatterns = [
    path('anime-images/', views.anime_images, name='anime_images'),
    path('manga-images/', views.manga_images, name='manga_images'),
]
