from django.contrib import admin
from .models import Document, Page, Image, DoclingSettings, OcrSettings


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
    list_display = ['title', 'group', 'page_count', 'processing_status', 'processing_progress', 'ocrmypdf_applied', 'created_at']
    list_filter = ['processing_status', 'group', 'ocrmypdf_applied', 'created_at']
    search_fields = ['title', 'group__name']
    readonly_fields = ['sqid', 'processing_status', 'processed_pages', 'processing_progress', 'created_at', 'updated_at']
    inlines = [PageInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'group', 'original_pdf', 'thumbnail')
        }),
        ('OCR Settings', {
            'fields': ('ocr_settings', 'ocrmypdf_applied')
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
        ('Advanced', {
            'fields': ('paddleocr_layout', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['page', 'caption', 'created_at']
    list_filter = ['page__document__group', 'created_at']
    search_fields = ['page__document__title', 'caption']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('page', 'image_file', 'caption')
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DoclingSettings)
class DoclingSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'ocr_engine', 'language', 'updated_at']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('OCR Settings', {
            'fields': ('ocr_engine', 'language', 'confidence_threshold')
        }),
        ('Layout Detection', {
            'fields': ('detect_tables', 'detect_figures', 'ignore_headers_footers')
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


@admin.register(OcrSettings)
class OcrSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'paddleocr_model', 'use_ocrmypdf', 'language', 'updated_at']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Ollama Configuration', {
            'fields': ('ollama_base_url', 'paddleocr_model')
        }),
        ('OCRmyPDF Settings', {
            'fields': ('use_ocrmypdf', 'ocrmypdf_language', 'ocrmypdf_compression')
        }),
        ('General Settings', {
            'fields': ('language',)
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

