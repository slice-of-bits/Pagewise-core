from django.db import models
from django.utils import timezone

from pagewise.models import BaseModel
from pagewise.fields import ModelSeedSqidsField


class Group(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class GroupShare(BaseModel):
    """Public share link for a group with expiration and usage tracking"""
    sqid = ModelSeedSqidsField(min_length=12)

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="shares")
    expire_date = models.DateTimeField()
    access_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Share {self.sqid} for {self.group.name}"

    @property
    def is_expired(self):
        """Check if the share link has expired"""
        return timezone.now() > self.expire_date

    def increment_access(self):
        """Increment the access count"""
        self.access_count += 1
        self.save(update_fields=['access_count'])

