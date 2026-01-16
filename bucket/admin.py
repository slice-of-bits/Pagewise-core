from django.contrib import admin
from .models import Bucket


@admin.register(Bucket)
class BucketAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['sqid', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Metadata', {
            'fields': ('sqid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
