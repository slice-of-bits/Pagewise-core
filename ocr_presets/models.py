"""
OCR Preset models for OCRmyPDF processing
"""
from django.db import models
from docpond.models import BaseModel


class OcrBackend(models.TextChoices):
    """OCR backends supported by ocrmypdf"""
    TESSERACT = 'tesseract', 'Tesseract'
    CUNEIFORM = 'cuneiform', 'Cuneiform'
    EASYOCR = 'easyocr', 'EasyOCR'


class OcrPreset(BaseModel):
    """Configuration preset for OCRmyPDF processing"""

    name = models.CharField(max_length=100, unique=True, help_text="Preset name")
    is_default = models.BooleanField(default=False, help_text="Set as default preset")

    # OCR Settings
    force_ocr = models.BooleanField(
        default=False,
        help_text="Force OCR even if document already contains text"
    )

    skip_text = models.BooleanField(
        default=False,
        help_text="Skip OCR on pages that already have text"
    )

    redo_ocr = models.BooleanField(
        default=False,
        help_text="Remove existing OCR and redo it"
    )

    ocr_backend = models.CharField(
        max_length=20,
        choices=OcrBackend.choices,
        default=OcrBackend.TESSERACT,
        help_text="OCR engine to use"
    )

    language = models.CharField(
        max_length=50,
        default='eng',
        help_text="OCR language code (e.g., 'eng', 'nld', 'eng+nld')"
    )

    # Optimization Settings
    optimize = models.IntegerField(
        default=1,
        choices=[(0, 'No optimization'), (1, 'Lossless'), (2, 'Lossy'), (3, 'Aggressive')],
        help_text="PDF optimization level"
    )

    jpeg_quality = models.IntegerField(
        default=75,
        help_text="JPEG quality for images (1-100)"
    )

    png_quality = models.IntegerField(
        default=70,
        help_text="PNG quality for images (1-100)"
    )

    # Image Processing
    deskew = models.BooleanField(
        default=False,
        help_text="Deskew pages before OCR"
    )

    do_clean = models.BooleanField(
        default=False,
        help_text="Clean pages before OCR (removes background noise)"
    )

    do_clean_final = models.BooleanField(
        default=False,
        help_text="Clean pages after OCR"
    )

    remove_background = models.BooleanField(
        default=False,
        help_text="Remove background from pages"
    )

    # DPI Settings
    oversample = models.IntegerField(
        default=0,
        help_text="Oversample images to at least this DPI (0 = no oversampling)"
    )

    # Advanced Settings
    rotate_pages = models.BooleanField(
        default=False,
        help_text="Rotate pages to correct orientation"
    )

    remove_vectors = models.BooleanField(
        default=False,
        help_text="Remove vector graphics from PDF"
    )

    # Additional arguments (JSON for custom options)
    advanced_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional OCRmyPDF arguments in JSON format"
    )

    class Meta:
        verbose_name = "OCR Preset"
        verbose_name_plural = "OCR Presets"
        ordering = ['-is_default', 'name']

    def __str__(self):
        default_marker = " (Default)" if self.is_default else ""
        return f"{self.name}{default_marker}"

    def save(self, *args, **kwargs):
        """Ensure only one preset is set as default"""
        if self.is_default:
            # Remove default flag from other presets
            OcrPreset.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
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
                    'force_ocr': False,  # Don't force OCR by default
                    'skip_text': True,   # Skip pages that already have text
                    'redo_ocr': False,   # Don't redo existing OCR by default
                    'ocr_backend': OcrBackend.TESSERACT,
                    'language': 'eng',
                    'optimize': 1,
                }
            )
        return preset

