from django.contrib import admin
from .models import Document, Page, Image


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
    list_display = ['title', 'pond', 'page_count', 'processing_status', 'processing_progress', 'created_at']
    list_filter = ['processing_status', 'pond', 'created_at']
    search_fields = ['title', 'pond__name']
    readonly_fields = ['sqid', 'processing_status', 'processed_pages', 'processing_progress', 'created_at', 'updated_at']
    inlines = [PageInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'pond', 'original_pdf', 'thumbnail', 'docling_preset', 'ocr_preset')
        }),
        ('Processing', {
            'fields': ('page_count', 'processing_status', 'processed_pages', 'processing_progress'),
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
        }),
    )


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['document', 'page_number', 'processing_status', 'created_at']
    list_filter = ['processing_status', 'document__pond', 'created_at']
    search_fields = ['document__title', 'text_markdown_clean']
    readonly_fields = ['sqid', 'created_at', 'updated_at']
    inlines = [ImageInline]

    fieldsets = (
        (None, {
            'fields': ('document', 'page_number', 'page_pdf', 'processing_status')
        }),
        ('Content', {
            'fields': ('ocr_markdown_raw', 'text_markdown_clean'),
        }),
        ('Docling Data', {
            'fields': ('docling_json', 'docling_json_override'),
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
        }),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['page', 'width', 'height', 'caption', 'created_at']
    list_filter = ['page__document__pond', 'created_at']
    search_fields = ['page__document__title', 'caption']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('page', 'image_file', 'caption', 'width', 'height')
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
        }),
    )


