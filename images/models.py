from django.db import models

class Image(models.Model):
    title = models.CharField(max_length=255)
    image_url = models.URLField()
    anime_or_manga = models.CharField(max_length=10)

    def __str__(self):
        return self.title
