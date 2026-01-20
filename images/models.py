from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
import os

from pagewise.models import BaseModel


def image_upload_path(instance, filename):
    """Generate upload path for extracted images: /{group}/{book-name}/{page-number}/images/{filename}"""
    group_name = instance.page.document.group.name
    clean_title = "".join(c for c in instance.page.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{group_name}/{clean_title}/{instance.page.page_number}/images/{filename}"


class Image(BaseModel):
    """Image extracted from a document page"""
    page = models.ForeignKey('documents.Page', on_delete=models.CASCADE, related_name="images")

    image_file = models.ImageField(upload_to=image_upload_path, height_field="height", width_field="width")
    alt_text = models.TextField(blank=True, null=True, help_text="AI-generated alt text for the image")
    caption = models.TextField(blank=True, null=True)
    
    # Image dimensions
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Image from {self.page}"

    def clean(self):
        """Validate that image file is not empty"""
        from django.core.exceptions import ValidationError
        if not self.image_file:
            raise ValidationError("Image must have a file attached")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def filename(self):
        """Get the filename for the image based on alt text"""
        if self.alt_text:
            # Clean alt text to create a valid filename
            clean_name = "".join(c for c in self.alt_text if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_name = clean_name.replace(' ', '-')[:100]  # Limit to 100 chars
            if clean_name:
                # Get file extension
                ext = os.path.splitext(self.image_file.name)[1] or '.jpg'
                return f"{clean_name}{ext}"
        
        # Fallback to sqid if no alt text
        ext = os.path.splitext(self.image_file.name)[1] or '.jpg'
        return f"{self.sqid}{ext}"
    
    @property
    def url_path(self):
        """Get the URL path for the image: /sqid/filename.ext"""
        return f"/{self.sqid}/{self.filename}"
