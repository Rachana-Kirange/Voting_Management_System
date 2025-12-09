from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'target_model', 'target_repr', 'created_at')
    list_filter = ('action', 'actor')
    search_fields = ('target_model', 'target_repr')
    readonly_fields = ('actor', 'action', 'target_model', 'target_repr', 'details', 'created_at')

    def has_add_permission(self, request):
        # prevent manual creation via admin UI
        return False
from django.contrib import admin

# Register your models here.
