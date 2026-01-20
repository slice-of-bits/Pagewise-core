from django.contrib import admin
from .models import Document, Page, Image, OCRSettings


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
            'fields': ('title', 'group', 'original_pdf', 'thumbnail', 'ocr_model')
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
        ('Advanced', {
            'fields': ('docling_layout', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('sqid', 'created_at', 'updated_at'),
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


@admin.register(OCRSettings)
class OCRSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'ocr_backend', 'default_model', 'language', 'updated_at']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('DeepSeek OCR Settings', {
            'fields': ('ocr_backend', 'default_model', 'default_prompt')
        }),
        ('Legacy Docling Settings', {
            'fields': ('ocr_engine', 'language', 'confidence_threshold', 'detect_tables', 'detect_figures', 'ignore_headers_footers'),
            'classes': ('collapse',)
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

