# from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
import os

from pagewise.models import BaseModel


def document_upload_path(instance, filename):
    """Generate upload path for documents: /{group_name}/{document_title}/"""
    group_name = instance.group.name
    # Clean filename for filesystem
    clean_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{group_name}/{clean_title}/{clean_title}.pdf"


def thumbnail_upload_path(instance, filename):
    """Generate upload path for thumbnails"""
    group_name = instance.group.name
    clean_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{group_name}/{clean_title}/{clean_title}-cover.jpg"


class ProcessingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Document(BaseModel):
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name="documents")

    title = models.CharField(max_length=500)
    thumbnail = models.FileField(
        upload_to=thumbnail_upload_path,
        blank=True,
        null=True
    )

    original_pdf = models.FileField(upload_to=document_upload_path)
    page_count = models.PositiveIntegerField(default=0)

    # OCR model selection
    ocr_model = models.CharField(max_length=100, default='deepseek-ocr')

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
    """Generate upload path for individual pages"""
    group_name = instance.document.group.name
    clean_title = "".join(c for c in instance.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{group_name}/{clean_title}/pages/{instance.page_number}.pdf"


class Page(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="pages")

    page_number = models.PositiveIntegerField()
    page_pdf = models.FileField(upload_to=page_upload_path)

    # OCR and processing status
    ocr_markdown_raw = models.TextField(blank=True)
    text_markdown_clean = models.TextField(blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING
    )

    # DeepSeek OCR data (replacing Docling)
    ocr_references = models.JSONField(blank=True, null=True)  # Store parsed references
    bbox_visualization = models.FileField(upload_to='bbox_visualizations/', blank=True, null=True)  # Bbox debug image
    
    # Legacy Docling data (keeping for backward compatibility)
    docling_layout = models.JSONField(blank=True, null=True)

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
    """Generate upload path for extracted images"""
    group_name = instance.page.document.group.name
    clean_title = "".join(c for c in instance.page.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{group_name}/{clean_title}/images/{instance.page.page_number}_{filename}"


class Image(BaseModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="images")

    image_file = models.FileField(upload_to=image_upload_path)
    caption = models.TextField(blank=True, null=True)
    
    # Image dimensions
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Image from {self.page}"


class OCRSettings(BaseModel):
    """Configuration for OCR processing (DeepSeek-OCR or Docling)"""

    name = models.CharField(max_length=100, default="default", unique=True)

    # OCR Engine Selection
    ocr_backend = models.CharField(
        max_length=50,
        choices=[
            ('deepseek-ocr', 'DeepSeek OCR'),
            ('docling', 'Docling (Legacy)'),
        ],
        default='deepseek-ocr'
    )

    # DeepSeek OCR Settings
    default_model = models.CharField(max_length=100, default='deepseek-ocr')
    default_prompt = models.TextField(default='<|grounding|>Convert the document to markdown.')
    
    # Legacy Docling Settings (kept for backward compatibility)
    ocr_engine = models.CharField(
        max_length=50,
        choices=[
            ('tesseract', 'Tesseract'),
            ('easyocr', 'EasyOCR'),
            ('doctr', 'DocTR'),
        ],
        default='tesseract'
    )
    detect_tables = models.BooleanField(default=True)
    detect_figures = models.BooleanField(default=True)
    ignore_headers_footers = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')
    confidence_threshold = models.FloatField(default=0.7)

    # Advanced settings JSON for additional configuration
    settings_json = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "OCR Settings"
        verbose_name_plural = "OCR Settings"

    def __str__(self):
        return f"OCR Settings: {self.name}"

    @classmethod
    def get_default_settings(cls):
        """Get or create default settings"""
        settings, _ = cls.objects.get_or_create(
            name='default',
            defaults={
                'ocr_backend': 'deepseek-ocr',
                'default_model': 'deepseek-ocr',
                'default_prompt': '<|grounding|>Convert the document to markdown.',
                'ocr_engine': 'tesseract',
                'detect_tables': True,
                'detect_figures': True,
                'ignore_headers_footers': True,
                'language': 'en',
                'confidence_threshold': 0.7,
            }
        )
        return settings


# Keep DoclingSettings as an alias for backward compatibility
DoclingSettings = OCRSettings

