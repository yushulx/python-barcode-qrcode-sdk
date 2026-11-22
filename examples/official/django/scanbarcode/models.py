from django.db import models

# Create your models here.
class Image(models.Model):
    name = models.CharField(max_length=30)
    data = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.name