from django.db import models

# Create your models here.

class Hello(models.Model):
    hello_world = models.CharField(max_length=50)
