from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Voter
from users.models import Candidate as UserCandidate  # User app Candidate
from elections.models import Election
from voting.models import Vote

@login_required
def vote(request, election_id):
    election = get_object_or_404(Election, id=election_id)

    # 🔐 Check if user already voted in this election
    if Vote.objects.filter(voter=request.user, election=election).exists():
        messages.error(request, "You have already voted in this election.")
        return redirect('election_detail', election_id=election.id)

    if request.method == "POST":
        candidate_id = request.POST.get('candidate')
        candidate = get_object_or_404(UserCandidate, id=candidate_id, elections=election)

        # Create vote
        Vote.objects.create(
            voter=request.user,
            election=election,
            candidate=candidate
        )

        messages.success(request, "Your vote has been cast successfully.")
        return redirect('election_detail', election_id=election.id)

    # GET request: show election candidates
    candidates = UserCandidate.objects.filter(elections=election)
    return render(request, 'voting/vote.html', {
        'election': election,
        'candidates': candidates
    })
