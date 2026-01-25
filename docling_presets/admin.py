from django.contrib import admin
from docling_presets.models import DoclingPreset


@admin.register(DoclingPreset)
class DoclingPresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'pipeline_type', 'ocr_engine', 'created_at']
    list_filter = ['is_default', 'pipeline_type', 'ocr_engine', 'created_at']
    search_fields = ['name']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'is_default', 'pipeline_type')
        }),
        ('OCR Settings', {
            'fields': ('ocr_engine', 'force_ocr', 'ocr_languages'),
        }),
        ('VLM Settings', {
            'fields': ('vlm_model',),
        }),
        ('Picture Description', {
            'fields': ('enable_picture_description', 'picture_description_prompt'),
            'classes': ('collapse',)
        }),
        ('Table Structure', {
            'fields': ('enable_table_structure', 'table_former_mode'),
            'classes': ('collapse',)
        }),
        ('Enrichments', {
            'fields': ('enable_code_enrichment', 'enable_formula_enrichment'),
            'classes': ('collapse',)
        }),
        ('Layout Filters', {
            'fields': ('filter_orphan_clusters', 'filter_empty_clusters'),
            'classes': ('collapse',)
        }),
        ('Advanced', {
            'fields': ('advanced_settings',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

