
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import CustomUser, Voter, Notification
from .forms import CustomUserCreationForm, CustomUserChangeForm

@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = (
        'username',
        'email',
        'role',
        'is_admin_approved',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'role',
        'is_admin_approved',
        'is_staff',
        'is_active',
    )

    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'full_name', 'password')
        }),

        ('Role & Approval', {
            'fields': ('role', 'is_admin_approved')
        }),

        ('Permissions', {
            'fields': (
                'is_staff',
                'is_active',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),

        ('Important dates', {
            'fields': ('last_login',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'full_name',
                'role',
                'password1',
                'password2',
            ),
        }),
    )
    actions = ['approve_candidates', 'reject_candidates']

    def approve_candidates(self, request, queryset):
        queryset.filter(role='candidate').update(is_admin_approved=True)
        self.message_user(request, "Selected candidates have been APPROVED.")

    def reject_candidates(self, request, queryset):
        queryset.filter(role='candidate').update(is_admin_approved=False)
        self.message_user(request, "Selected candidates have been REJECTED.")

    approve_candidates.short_description = "Approve selected candidates"
    reject_candidates.short_description = "Reject selected candidates"



@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'voter_id', 'verification_status')
    list_filter = ('verification_status',)
    search_fields = ('user__username', 'voter_id')
    actions = ['verify_voters']

    def verify_voters(self, request, queryset):
        queryset.update(verification_status='verified')
        self.message_user(request, "Selected voters have been verified.")
    verify_voters.short_description = "Mark selected voters as Verified"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('voter', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('voter__user__username', 'title')