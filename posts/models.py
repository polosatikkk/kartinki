from django.db import models


class Hello(models.Model):
    hello_world = models.CharField(max_length=50)
