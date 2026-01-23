from django.contrib import admin
from ponds.models import Pond, PondShare


@admin.register(Pond)
class PondAdmin(admin.ModelAdmin):
    list_display = ('name', 'sqid', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('sqid', 'created_at', 'updated_at')


@admin.register(PondShare)
class PondShareAdmin(admin.ModelAdmin):
    list_display = ('sqid', 'pond', 'expire_date', 'access_count', 'is_expired', 'created_at')
    list_filter = ('expire_date', 'created_at')
    search_fields = ('sqid', 'pond__name')
    readonly_fields = ('sqid', 'created_at', 'updated_at', 'is_expired')

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

