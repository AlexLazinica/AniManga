from django.urls import path
from anime import views


urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('signup', views.register, name='register'),
    path('animes', views.anime_display, name='anime_display'),
    path('animes/rec', views.recommend, name='recommend'),
    path('animes/fav', views.fav, name='favorite'),
    path('search/all', views.search, name='search'),
    path('search/fav', views.search_fav, name='search_fav'),
    path('search/date', views.date, name='search_date'),
    path('watchstatus', views.change_watch_status, name='status'),
    path('animes/debugjson', views.debug_json, name='debug_json'),
    path('animes/wish', views.wishlist, name='wishlist'),
    path('detail', views.detail_page, name='detail_page'),
    path('animes/popular', views.popular, name='popular'),
    path('rate', views.rate, name='rate'),
    path('status/likestatus', views.anime_like, name='like_status'),
    path('animes/watched', views.watched, name='watched'),
    path('animes/watching', views.watching, name='watching'),
    path('mangas', views.manga_display, name='manga_display'),#nadjeno
    path('mangas/rec', views.recommend_manga, name='manga_recommend'),#nadjeno
    path('mangas/fav', views.favorite_manga, name='manga_favorite'), #nadjeno
    path('search/manga/all', views.search_manga, name='search_manga'), #nadjeno
    path('search/manga/fav', views.search_fav_manga, name='search_fav_manga'), #nadjeno
    path('search/manga/date', views.date_manga, name='search_date_manga'), #nadjeno
    path('readstatus', views.change_read_status, name='read_status'), #nadjeno
    # path('mangas/debugjson', views.debug_json, name='debug_json_manga'), ne bi trebao
    path('mangas/wish', views.wishlist_manga, name='wishlist_manga'), #nadjeno
    path('detail_manga', views.detail_page_manga, name='detail_page_manga'), #nadjeno
    path('mangas/popular', views.popular_manga, name='popular_manga'), #nadjeno
    path('rate_manga', views.rate_manga, name='rate_manga'), #nadjeno
    path('status/likemangastatus', views.manga_like, name='like_manga_status'), #nadjeno
    path('mangas/read', views.read_manga, name='read_manga'), #nadjeno
]
