from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import CustomUser, Party, Candidate, Voter, Vote, Notification
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'full_name', 'password')}),
        ('Permissions', {
            'fields': (
                'role', 'is_staff', 'is_active',
                'is_superuser', 'groups', 'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'age', 'area')


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('user', 'voter_id', 'mobile_no', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'voter_id')
    actions = ['verify_voters']

    def verify_voters(self, request, queryset):
        queryset.update(is_verified=True)
    verify_voters.short_description = "Mark selected voters as Verified"

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate', 'date')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('voter', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('voter__user__username', 'title')
