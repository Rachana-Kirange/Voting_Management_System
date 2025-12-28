from django.contrib import admin
from django.contrib.messages import constants as messages
from django.utils import timezone
from .models import Election
from users.models import Candidate, Party, Vote, Campaign

@admin.action(description='Publish results for selected elections')
def publish_results_action(modeladmin, request, queryset):
    count = 0
    now = timezone.now()
    
    for election in queryset:
        if election.end_date <= now:
            election.results_published = True
            election.save()
            count += 1
        else:
            modeladmin.message_user(
                request, 
                f"Skipped '{election.title}': Election has not ended yet.", 
                level=messages.WARNING
            )
    
    if count > 0:
        modeladmin.message_user(
            request, 
            f"Successfully published results for {count} election(s).",
            level=messages.SUCCESS
        )


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'election_type', 'is_active', 'results_published')
    list_filter = ('is_active', 'results_published', 'election_type')
    search_fields = ('title',)
    actions = [publish_results_action]

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'age', 'area')
    list_filter = ('party',)
    search_fields = ('name',)

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'voter', 'candidate', 'election')
    list_filter = ('election', 'candidate__party')

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'election',)
    list_filter = ('election',)