from django.contrib import admin
from .models import Document, Page, Image, DeepSeekOCRSettings, DoclingPreset


class PageInline(admin.TabularInline):
    model = Page
    extra = 0
    readonly_fields = ['sqid', 'processing_status', 'created_at']
    fields = ['page_number', 'processing_status', 'created_at']


class ImageInline(admin.TabularInline):
    model = Image
    extra = 0
    readonly_fields = ['sqid']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'page_count', 'processing_status', 'processing_progress', 'created_at']
    list_filter = ['processing_status', 'group', 'created_at']
    search_fields = ['title', 'group__name']
    readonly_fields = ['sqid', 'processing_status', 'processed_pages', 'processing_progress', 'created_at', 'updated_at']
    inlines = [PageInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'group', 'original_pdf', 'thumbnail', 'ocr_model', 'docling_preset')
        }),
        ('Processing', {
            'fields': ('page_count', 'processing_status', 'processed_pages', 'processing_progress'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['document', 'page_number', 'processing_status', 'created_at']
    list_filter = ['processing_status', 'document__group', 'created_at']
    search_fields = ['document__title', 'text_markdown_clean']
    readonly_fields = ['sqid', 'created_at', 'updated_at']
    inlines = [ImageInline]

    fieldsets = (
        (None, {
            'fields': ('document', 'page_number', 'page_pdf', 'processing_status')
        }),
        ('Content', {
            'fields': ('ocr_markdown_raw', 'text_markdown_clean'),
            'classes': ('collapse',)
        }),
        ('DeepSeek OCR Data', {
            'fields': ('ocr_references', 'bbox_visualization'),
            'classes': ('collapse',)
        }),
        ('Docling Data', {
            'fields': ('docling_json', 'docling_json_override'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['page', 'width', 'height', 'caption', 'created_at']
    list_filter = ['page__document__group', 'created_at']
    search_fields = ['page__document__title', 'caption']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('page', 'image_file', 'caption', 'width', 'height')
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeepSeekOCRSettings)
class DeepSeekOCRSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_model', 'updated_at']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('DeepSeek OCR Settings', {
            'fields': ('default_model', 'default_prompt')
        }),
        ('Advanced', {
            'fields': ('settings_json',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of default settings
        if obj and obj.name == 'default':
            return False
        return super().has_delete_permission(request, obj)


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

