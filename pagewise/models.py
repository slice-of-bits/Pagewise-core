from django.db import models
from django_sqids import SqidsField

from pagewise.fields import ModelSeedSqidsField


class BaseModel(models.Model):
    sqid = ModelSeedSqidsField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True