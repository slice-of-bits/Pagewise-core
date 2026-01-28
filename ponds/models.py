from django.db import models
from django.utils import timezone

from docpond.models import BaseModel
from docpond.fields import ModelSeedSqidsField


class Pond(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class PondShare(BaseModel):
    """Public share link for a pond with expiration and usage tracking"""
    sqid = ModelSeedSqidsField(min_length=12)

    pond = models.ForeignKey(Pond, on_delete=models.CASCADE, related_name="shares")
    expire_date = models.DateTimeField()
    access_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Share {self.sqid} for {self.pond.name}"

    @property
    def is_expired(self):
        """Check if the share link has expired"""
        return timezone.now() > self.expire_date

    def increment_access(self):
        """Increment the access count"""
        self.access_count += 1
        self.save(update_fields=['access_count'])

