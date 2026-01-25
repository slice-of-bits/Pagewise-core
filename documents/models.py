# from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
import os

from docpond.models import BaseModel


def document_upload_path(instance, filename):
    """Generate upload path for documents: /{pond_name}/{document_title}/"""
    pond_name = instance.pond.name
    # Clean filename for filesystem
    clean_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{pond_name}/{clean_title}/{clean_title}.pdf"


def thumbnail_upload_path(instance, filename):
    """Generate upload path for thumbnails"""
    pond_name = instance.pond.name
    clean_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{pond_name}/{clean_title}/{clean_title}-cover.jpg"


class ProcessingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Document(BaseModel):
    pond = models.ForeignKey('ponds.Pond', on_delete=models.CASCADE, related_name="documents")

    title = models.CharField(max_length=500)
    thumbnail = models.FileField(
        upload_to=thumbnail_upload_path,
        blank=True,
        null=True
    )

    original_pdf = models.FileField(upload_to=document_upload_path)
    page_count = models.PositiveIntegerField(default=0)

    # Docling preset (if using docling for processing)
    docling_preset = models.ForeignKey(
        'docling_presets.DoclingPreset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Docling preset to use for processing"
    )

    # OCR preset (if using OCRmyPDF for preprocessing)
    ocr_preset = models.ForeignKey(
        'ocr_presets.OcrPreset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="OCR preset to use for preprocessing (runs before page splitting)"
    )

    # Processing status
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING
    )
    processed_pages = models.PositiveIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title

    @property
    def processing_progress(self):
        """Return processing progress as percentage"""
        if self.page_count == 0:
            return 0
        return (self.processed_pages / self.page_count) * 100

def page_upload_path(instance, filename):
    """Generate upload path for individual pages: /{pond}/{book-name}/{page-number}/page-{number}.pdf"""
    pond_name = instance.document.pond.name
    clean_title = "".join(c for c in instance.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{pond_name}/{clean_title}/{instance.page_number}/page-{instance.page_number}.pdf"


def bbox_visualization_upload_path(instance, filename):
    """Generate upload path for bbox visualization: /{pond}/{book-name}/{page-number}/page-{number}-bbox.jpg"""
    pond_name = instance.document.pond.name
    clean_title = "".join(c for c in instance.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{pond_name}/{clean_title}/{instance.page_number}/page-{instance.page_number}-bbox.jpg"


def page_image_upload_path(instance, filename):
    """Generate upload path for page image: /{pond}/{book-name}/{page-number}/page-{number}.jpg"""
    pond_name = instance.document.pond.name
    clean_title = "".join(c for c in instance.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{pond_name}/{clean_title}/{instance.page_number}/page-{instance.page_number}.jpg"


class Page(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="pages")

    page_number = models.PositiveIntegerField()
    page_pdf = models.FileField(upload_to=page_upload_path)
    page_image = models.ImageField(
        upload_to=page_image_upload_path,
        blank=True,
        null=True,
        help_text="Preview image of the page"
    )

    # OCR and processing status
    ocr_markdown_raw = models.TextField(blank=True)
    text_markdown_clean = models.TextField(blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING
    )

    # Docling data
    docling_json = models.JSONField(
        blank=True,
        null=True,
        help_text="Original docling JSON output"
    )
    docling_json_override = models.JSONField(
        blank=True,
        null=True,
        help_text="Corrected/overridden docling JSON data"
    )

    # search
    # search_vector = SearchVectorField(null=True)  # PostgreSQL specific

    metadata = models.JSONField(default=dict, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("document", "page_number")
        ordering = ["page_number"]

    def __str__(self):
        return f"{self.document.title} - Page {self.page_number}"

def image_upload_path(instance, filename):
    """Generate upload path for extracted images: /{pond}/{book-name}/{page-number}/images/{image-id}.jpg"""
    pond_name = instance.page.document.pond.name
    clean_title = "".join(c for c in instance.page.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{pond_name}/{clean_title}/{instance.page.page_number}/images/{filename}"


class Image(BaseModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="images")

    image_file = models.ImageField(upload_to=image_upload_path, height_field="height", width_field="width")
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



