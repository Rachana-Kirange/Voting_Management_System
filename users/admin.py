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
		('Permissions', {'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'created_at')}),
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
	list_display = ('user', 'voter_id', 'mobile', 'has_voted', 'is_verified', 'verification_status')
	list_filter = ('is_verified', 'verification_status')
	search_fields = ('user__username', 'voter_id')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
	list_display = ('voter', 'candidate', 'date')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('voter', 'title', 'notification_type', 'is_read', 'created_at')
	list_filter = ('notification_type', 'is_read')
	search_fields = ('voter__user__username', 'title')
