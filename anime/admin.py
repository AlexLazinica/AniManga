from django.contrib import admin
from anime.models import Anime, Studio, User, Tag, Episode
from anime.models import Manga, Author, LikeManga, ReadStatusManga, RateManga, Manga_Tag, Chapter

# Anime
admin.site.register(Anime)
admin.site.register(Studio)
admin.site.register(User)
admin.site.register(Tag)
admin.site.register(Episode)

# Manga
admin.site.register(Manga)
admin.site.register(Author)
admin.site.register(LikeManga)
admin.site.register(ReadStatusManga)
admin.site.register(RateManga)
admin.site.register(Manga_Tag)
admin.site.register(Chapter)
