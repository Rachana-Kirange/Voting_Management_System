from django.contrib import admin
from .models import BackupRecord


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ('filename', 'performed_by', 'success', 'created_at', 'size')
    readonly_fields = ('filename', 'performed_by', 'created_at', 'size', 'note', 'success')
    list_filter = ('success', 'performed_by')
from django.contrib import admin

# Register your models here.
