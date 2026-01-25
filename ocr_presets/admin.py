from django.contrib import admin
from ocr_presets.models import OcrPreset


@admin.register(OcrPreset)
class OcrPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'ocr_backend', 'language', 'force_ocr', 'optimize')
    list_filter = ('is_default', 'ocr_backend', 'force_ocr')
    search_fields = ('name', 'language')

    fieldsets = (
        ('Basic Settings', {
            'fields': ('name', 'is_default')
        }),
        ('OCR Settings', {
            'fields': ('force_ocr', 'skip_text', 'redo_ocr', 'ocr_backend', 'language')
        }),
        ('Optimization', {
            'fields': ('optimize', 'jpeg_quality', 'png_quality')
        }),
        ('Image Processing', {
            'fields': ('deskew', 'do_clean', 'do_clean_final', 'remove_background', 'oversample')
        }),
        ('Advanced', {
            'fields': ('rotate_pages', 'remove_vectors', 'advanced_settings'),
            'classes': ('collapse',)
        }),
    )

