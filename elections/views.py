from django.shortcuts import render
from .models import Election

def election_list(request):
    elections = Election.objects.filter(is_active=True)
    return render(request, 'elections/election_list.html', {
        'elections': elections
    })
