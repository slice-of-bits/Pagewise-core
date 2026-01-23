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

    # OCR model selection
    ocr_model = models.CharField(max_length=100, default='deepseek-ocr')
    
    # Docling preset (if using docling for processing)
    docling_preset = models.ForeignKey(
        'DoclingPreset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Docling preset to use for processing"
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

    # DeepSeek OCR data
    ocr_references = models.JSONField(blank=True, null=True)  # Store parsed references
    bbox_visualization = models.ImageField(upload_to=bbox_visualization_upload_path, blank=True, null=True)  # Bbox debug image

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


class DeepSeekOCRSettings(BaseModel):
    """Configuration for DeepSeek OCR processing"""

    name = models.CharField(max_length=100, default="default", unique=True)

    # DeepSeek OCR Settings
    default_model = models.CharField(max_length=100, default='deepseek-ocr')
    default_prompt = models.TextField(default='<|grounding|>Convert the document to markdown.')

    # Advanced settings JSON for additional configuration
    settings_json = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "DeepSeek OCR Settings"
        verbose_name_plural = "DeepSeek OCR Settings"

    def __str__(self):
        return f"DeepSeek OCR Settings: {self.name}"

    @classmethod
    def get_default_settings(cls):
        """Get or create default settings"""
        settings, _ = cls.objects.get_or_create(
            name='default',
            defaults={
                'default_model': 'deepseek-ocr',
                'default_prompt': '<|grounding|>Convert the document to markdown.',
            }
        )
        return settings


class PipelineType(models.TextChoices):
    """Docling pipeline types"""
    STANDARD = 'standard', 'Standard PDF Pipeline'
    VLM = 'vlm', 'Vision-Language Model Pipeline'


class OcrEngine(models.TextChoices):
    """OCR engines supported by docling"""
    AUTO = 'auto', 'Auto (Best Available)'
    EASYOCR = 'easyocr', 'EasyOCR'
    TESSERACT = 'tesseract', 'Tesseract CLI'
    RAPIDOCR = 'rapidocr', 'RapidOCR'
    OCRMAC = 'ocrmac', 'macOS Vision OCR'


class TableFormerMode(models.TextChoices):
    """TableFormer extraction modes"""
    FAST = 'fast', 'Fast Mode'
    ACCURATE = 'accurate', 'Accurate Mode'


class DoclingPreset(BaseModel):
    """Configuration preset for Docling document processing"""

    name = models.CharField(max_length=100, unique=True, help_text="Preset name")
    is_default = models.BooleanField(default=False, help_text="Set as default preset")
    
    # Pipeline Configuration
    pipeline_type = models.CharField(
        max_length=20,
        choices=PipelineType.choices,
        default=PipelineType.STANDARD,
        help_text="Pipeline type: standard PDF or VLM"
    )
    
    # OCR Settings (for standard pipeline)
    ocr_engine = models.CharField(
        max_length=20,
        choices=OcrEngine.choices,
        default=OcrEngine.AUTO,
        help_text="OCR engine to use"
    )
    force_ocr = models.BooleanField(
        default=False,
        help_text="Force full page OCR even for PDFs with text"
    )
    ocr_languages = models.JSONField(
        default=list,
        blank=True,
        help_text="List of language codes for OCR (format depends on OCR engine)"
    )
    
    # VLM Settings (for VLM pipeline)
    vlm_model = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="VLM model repo ID (e.g., 'ibm-granite/granite-docling-258M')"
    )
    
    # Picture Description Settings
    enable_picture_description = models.BooleanField(
        default=False,
        help_text="Generate descriptions for images using VLM"
    )
    picture_description_prompt = models.TextField(
        blank=True,
        default='Describe this image in a few sentences.',
        help_text="Prompt for picture description model"
    )
    
    # Table Structure Settings
    enable_table_structure = models.BooleanField(
        default=True,
        help_text="Enable table structure extraction"
    )
    table_former_mode = models.CharField(
        max_length=20,
        choices=TableFormerMode.choices,
        default=TableFormerMode.ACCURATE,
        help_text="TableFormer extraction mode"
    )
    
    # Code and Formula Enrichment
    enable_code_enrichment = models.BooleanField(
        default=False,
        help_text="Enable specialized processing for code blocks"
    )
    enable_formula_enrichment = models.BooleanField(
        default=False,
        help_text="Enable LaTeX formula recognition"
    )
    
    # Layout Filters
    filter_orphan_clusters = models.BooleanField(
        default=False,
        help_text="Filter out orphaned text clusters (e.g., page numbers, headers)"
    )
    filter_empty_clusters = models.BooleanField(
        default=True,
        help_text="Filter out empty clusters in layout"
    )
    
    # Advanced Settings (JSON for additional options)
    advanced_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Advanced pipeline options in JSON format"
    )

    class Meta:
        verbose_name = "Docling Preset"
        verbose_name_plural = "Docling Presets"
        ordering = ['-is_default', 'name']

    def __str__(self):
        default_marker = " (Default)" if self.is_default else ""
        return f"{self.name}{default_marker}"

    def save(self, *args, **kwargs):
        """Ensure only one preset is set as default"""
        if self.is_default:
            # Remove default flag from other presets
            DoclingPreset.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default_preset(cls):
        """Get the default preset or create one if none exists"""
        preset = cls.objects.filter(is_default=True).first()
        if not preset:
            preset, _ = cls.objects.get_or_create(
                name='default',
                defaults={
                    'is_default': True,
                    'pipeline_type': PipelineType.STANDARD,
                    'ocr_engine': OcrEngine.AUTO,
                    'force_ocr': True,
                    'ocr_languages': ['en'],
                }
            )
        return preset

