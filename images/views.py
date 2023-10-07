from django.shortcuts import render
from animanga_user.images.api import fetch_anime_data
from animanga_user.images.api import fetch_manga_data

def anime_images(request):
    images = fetch_anime_data()
    return render(request, 'image/anime_images.html', {'images': images})

def manga_images(request):
    images = fetch_manga_data()
    return render(request, 'image/manga_images.html', {'images': images})
