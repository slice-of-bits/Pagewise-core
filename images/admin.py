from django.contrib import admin
from .models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['page', 'width', 'height', 'alt_text', 'caption', 'created_at']
    list_filter = ['page__document__group', 'created_at']
    search_fields = ['page__document__title', 'alt_text', 'caption']
    readonly_fields = ['sqid', 'created_at', 'updated_at', 'filename', 'url_path']

    fieldsets = (
        (None, {
            'fields': ('page', 'image_file', 'alt_text', 'caption', 'width', 'height')
        }),
        ('URL Info', {
            'fields': ('filename', 'url_path'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
