from django.db import models
from django.urls import reverse

from django.db import models
from django.urls import reverse

class User(models.Model):
    email = models.EmailField(verbose_name='Email', primary_key=True)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, blank=True, null=True)

    # Anime-related fields and relationships
    likeAnime = models.ManyToManyField(
        'Anime',
        help_text='Users like what animes',
        related_name='liked_by_users_anime',
    )
    rateAnime = models.ManyToManyField(
        'RateAnime',
        help_text='User anime ratings',
        related_name='rated_by_users_anime',
    )
    watchStatusAnime = models.ManyToManyField(
        'WatchStatus',
        help_text='User anime watch statuses',
        related_name='watched_by_users_anime',
    )
    watchProgressAnime = models.ManyToManyField(
        'WatchEpisodeProgress',
        help_text='User anime watch progress',
        related_name='progress_by_users_anime',
    )
    setTagAnime = models.ManyToManyField(
        'SetTag',
        help_text='User anime set tags',
        related_name='set_by_users_anime',
    )

    # Manga-related fields and relationships
    likeManga = models.ManyToManyField(
        'Manga',
        help_text='Users like what manga',
        related_name='liked_by_users_manga',
    )
    readStatusManga = models.ManyToManyField(
        'ReadStatusManga',
        help_text='User manga reading status',
        related_name='read_by_users_manga',
    )
    rateManga = models.ManyToManyField(
        'RateManga',
        help_text='User manga ratings',
        related_name='rated_by_users_manga',
    )

    class Meta:
        managed = False

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('user', args=[str(self.id)])
    
class Anime(models.Model):
    name = models.CharField(
        max_length=255, primary_key=True, verbose_name='AnimeName')
    release_date = models.CharField(
        max_length=255, verbose_name='ReleaseDate', blank=True, null=True)
    release_year = models.IntegerField()
    episode_count = models.IntegerField(
        verbose_name='NumOfEpisodes', blank=True, null=True)

    studio = models.ManyToManyField(
        'Studio',
        db_table='AnimeMadeBy',
        help_text='Each anime can be made by lots of Studios.')

    class Meta:
        managed = False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        '''Returns the url to access a particular instance of the model.'''
        return reverse('anime-detail', args=[str(self.name)])

class RateAnime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    score = models.FloatField()

    class Meta:
        # Korisno za reprezentovanje 2 kolone zajedno u primary key
        unique_together = (('user', 'anime'), )
        managed = False


class WatchStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    status = models.IntegerField()

    class Meta:
        # Korisno za reprezentovanje 2 kolone zajedno u primary key
        unique_together = (('user', 'anime'), )
        managed = False


class Tag(models.Model): 
    name = models.CharField(max_length=255, primary_key=True)

    hasAnime = models.ManyToManyField(
        Anime, db_table='TagHasAnime', help_text='Tag has what animes')

    class Meta:
        managed = False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', args=[str(self.name)])


class Episode(models.Model):
    anime_name = models.ForeignKey(Anime, on_delete=models.CASCADE)
    episode_num = models.IntegerField()
    episode_name = models.CharField(max_length=255, blank=True, null=True)
    length = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = (('anime_name', 'episode_num'), )
        managed = False

    def __str__(self):
        return self.anime_name + ': ' + self.episode_num

    # TODO: get_absolute_url


class WatchEpisodeProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    watch_time = models.IntegerField(blank=True, null=True)
    date = models.DateField(auto_now=True, blank=True, null=True)
    status = models.IntegerField(help_text='Same as status in WatchStatus')

    class Meta:
        unique_together = (('user', 'episode'), )
        managed = False

class SetTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    class Meta:
        unique_together = (('user', 'tag'), )
        managed = False

class LikeAnime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    class Meta:
        unique_together = (('user', 'anime'), )
        managed = False



class Studio(models.Model):
    name = models.CharField(
        max_length=255, primary_key=True, verbose_name='StudioName')

    # TODO: Mozda referenca za studio sajt
    #website = models.TextField(verbose_name='StudioWebsite', blank=True, null=True)
    class Meta:
        managed = False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('studio', args=[str(self.name)])

class Manga(models.Model):
    name = models.CharField(max_length=255, primary_key=True, verbose_name='MangaName')
    release_date = models.CharField(max_length=255, verbose_name='ReleaseDate', blank=True, null=True)
    release_year = models.IntegerField()
    chapter_count = models.IntegerField(verbose_name='NumOfChapters', blank=True, null=True)

    author = models.ManyToManyField('Author', db_table='MangaWrittenBy', help_text='Each manga can be written by multiple authors.')

    class Meta:
        managed = False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('manga-detail', args=[str(self.name)])

class Author(models.Model):
    name = models.CharField(max_length=255, primary_key=True, verbose_name='AuthorName')

    class Meta:
        managed = False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('author', args=[str(self.name)])

class LikeManga(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'manga'), )
        managed = False

class ReadStatusManga(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE)
    status = models.IntegerField()

    class Meta:
        unique_together = (('user', 'manga'), )
        managed = False

class RateManga(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE)
    userrate = models.FloatField()

    class Meta:
        unique_together = (('user', 'manga'), )
        managed = False

class Manga_Tag(models.Model):
    tag = models.CharField(max_length=255, primary_key=True, verbose_name='TagName')

    hasManga = models.ManyToManyField(
        Manga, db_table='MangaHasTag', help_text='Tag is associated with what manga')

    class Meta:
        managed = False

    def __str__(self):
        return self.tag

    def get_absolute_url(self):
        return reverse('tag', args=[str(self.tag)])

class LikeManga(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'manga'), )
        managed = False

class Chapter(models.Model):
    manga = models.ForeignKey('Manga', on_delete=models.CASCADE)
    chapter_num = models.IntegerField()
    chapter_title = models.CharField(max_length=255, blank=True, null=True)
    page_count = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = (('manga', 'chapter_num'), )
        managed = False

    def __str__(self):
        return f"{self.manga}: Chapter {self.chapter_num}"


