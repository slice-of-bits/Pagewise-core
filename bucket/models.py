from django.db import models

from docpond.models import BaseModel


# Create your models here.
class Bucket(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
