# from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
import os

from pagewise.models import BaseModel


def document_upload_path(instance, filename):
    """Generate upload path for documents: /{bucket_name}/{document_title}/"""
    bucket_name = instance.group.name
    # Clean filename for filesystem
    clean_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{bucket_name}/{clean_title}/{clean_title}.pdf"


def thumbnail_upload_path(instance, filename):
    """Generate upload path for thumbnails"""
    bucket_name = instance.group.name
    clean_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{bucket_name}/{clean_title}/{clean_title}-cover.jpg"


class ProcessingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Document(BaseModel):
    group = models.ForeignKey('bucket.Bucket', on_delete=models.CASCADE, related_name="documents")

    title = models.CharField(max_length=500)
    thumbnail = models.FileField(
        upload_to=thumbnail_upload_path,
        blank=True,
        null=True
    )

    original_pdf = models.FileField(upload_to=document_upload_path)
    page_count = models.PositiveIntegerField(default=0)

    # Processing status
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING
    )
    processed_pages = models.PositiveIntegerField(default=0)

    # Per-document OCR settings
    ocr_settings = models.ForeignKey(
        'OcrSettings',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text='OCR settings for this document. If null, uses global default settings.'
    )
    
    # OCRmyPDF tracking
    ocrmypdf_applied = models.BooleanField(
        default=False,
        help_text='Whether OCRmyPDF has been applied to add selectable text to the PDF'
    )

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title

    @property
    def processing_progress(self):
        """Return processing progress as percentage"""
        if self.page_count == 0:
            return 0
        return (self.processed_pages / self.page_count) * 100
    
    def get_ocr_settings(self):
        """Get OCR settings for this document (per-document or global default)"""
        if self.ocr_settings:
            return self.ocr_settings
        return OcrSettings.get_default_settings()

def page_upload_path(instance, filename):
    """Generate upload path for individual pages"""
    bucket_name = instance.document.group.name
    clean_title = "".join(c for c in instance.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{bucket_name}/{clean_title}/pages/{instance.page_number}.pdf"


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

    # PaddleOCR-VL data
    paddleocr_layout = models.JSONField(blank=True, null=True)

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
    bucket_name = instance.page.document.group.name
    clean_title = "".join(c for c in instance.page.document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{bucket_name}/{clean_title}/images/{instance.page.page_number}_{filename}"


class Image(BaseModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="images")

    image_file = models.FileField(upload_to=image_upload_path)
    caption = models.TextField(blank=True, null=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Image from {self.page}"


class OcrSettings(BaseModel):
    """OCR settings model for PaddleOCR-VL and OCRmyPDF configuration"""

    name = models.CharField(max_length=100, default="default", unique=True)

    # Ollama Server Configuration
    ollama_base_url = models.CharField(
        max_length=255,
        default='http://localhost:11434',
        help_text='Ollama server URL for hosting PaddleOCR-VL'
    )
    
    # PaddleOCR-VL Model Settings
    paddleocr_model = models.CharField(
        max_length=100,
        default='paddleocr-vl',
        help_text='Name of the PaddleOCR-VL model in Ollama'
    )

    # OCRmyPDF Settings
    use_ocrmypdf = models.BooleanField(
        default=False,
        help_text='Apply OCRmyPDF to add selectable text to PDF'
    )
    ocrmypdf_language = models.CharField(
        max_length=10,
        default='eng',
        help_text='Language for OCRmyPDF (e.g., eng, deu, fra)'
    )
    ocrmypdf_compression = models.BooleanField(
        default=True,
        help_text='Enable compression in OCRmyPDF to reduce file size'
    )

    # Processing settings
    language = models.CharField(max_length=10, default='en')
    
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
                'ollama_base_url': 'http://localhost:11434',
                'paddleocr_model': 'paddleocr-vl',
                'use_ocrmypdf': False,
                'ocrmypdf_language': 'eng',
                'ocrmypdf_compression': True,
                'language': 'en',
            }
        )
        return settings


# Keep DoclingSettings for backward compatibility during migration
# DEPRECATED: This model is maintained for backward compatibility only.
# New implementations should use OcrSettings instead.
# Migration path: Create equivalent OcrSettings and update Document.ocr_settings references.
# This model may be removed in a future major version (v2.0+).
class DoclingSettings(BaseModel):
    """DEPRECATED: Legacy model for Docling configuration - use OcrSettings instead"""

    name = models.CharField(max_length=100, default="default", unique=True)

    # OCR Settings
    ocr_engine = models.CharField(
        max_length=50,
        choices=[
            ('tesseract', 'Tesseract'),
            ('easyocr', 'EasyOCR'),
            ('doctr', 'DocTR'),
        ],
        default='tesseract'
    )

    # Layout settings
    detect_tables = models.BooleanField(default=True)
    detect_figures = models.BooleanField(default=True)
    ignore_headers_footers = models.BooleanField(default=True)

    # Processing settings
    language = models.CharField(max_length=10, default='en')
    confidence_threshold = models.FloatField(default=0.7)

    # Advanced settings JSON for additional configuration
    settings_json = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Docling Settings (Legacy)"
        verbose_name_plural = "Docling Settings (Legacy)"

    def __str__(self):
        return f"Docling Settings: {self.name}"

    @classmethod
    def get_default_settings(cls):
        """Get or create default settings"""
        settings, _ = cls.objects.get_or_create(
            name='default',
            defaults={
                'ocr_engine': 'tesseract',
                'detect_tables': True,
                'detect_figures': True,
                'ignore_headers_footers': True,
                'language': 'en',
                'confidence_threshold': 0.7,
            }
        )
        return settings

