from django.shortcuts import render
from .api import fetch_anime_images
from .api import fetch_manga_images

def anime_images(request):
    images = fetch_anime_images()
    return render(request, 'image/anime_images.html', {'images': images})

def manga_images(request):
    images = fetch_manga_images()
    return render(request, 'image/manga_images.html', {'images': images})
