from django.db import models
from docpond.models import BaseModel


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

