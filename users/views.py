from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.utils import timezone
from django.urls import reverse_lazy
# Your app-specific imports (adjust if models/forms are in different apps)
from .decorators import admin_required
from .forms import PartyForm, CandidateForm, CustomUserChangeForm, VoterRegistrationForm , CampaignForm
from .models import Party, Candidate, Voter, Vote, Election,Campaign
from elections.models import Election
from elections.forms import ElectionForm
from django.contrib.auth.decorators import login_required
from elections.models import Election

from django.contrib.admin.views.decorators import staff_member_required

from django.core.paginator import Paginator

def home_view(request):
    return render(request, 'home.html')


def login_page(request):
    if request.user.is_authenticated:
        return redirect('users_home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            # Redirect based on role if you have a role field
            # Example:
            # if hasattr(user, 'role'):
            #     if user.role == 'admin':
            #         return redirect('admin_dashboard')
            #     elif user.role == 'voter':
            #         return redirect('voter_dashboard')
            #     elif user.role == 'candidate':
            #         return redirect('candidate_dashboard')
            return redirect('users_home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')


def register_page(request):
    if request.user.is_authenticated:
        return redirect('users_home')

    User = get_user_model()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')  # Optional: if you have role selection
        full_name = request.POST.get('full_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'register.html')

        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'register.html')

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email or '',  # Allow empty if not required
                password=password1
            )
            if hasattr(user, 'role') and role:
                user.role = role
            if hasattr(user, 'full_name') and full_name:
                user.full_name = full_name
            user.save()

            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, 'An error occurred during registration.')
            print(e)  # For debugging; remove in production

    return render(request, 'register.html')


@admin_required  # Assuming you have this decorator
def admin_dashboard(request):
    total_voters = Voter.objects.count()
    active_elections = Election.objects.filter(is_active=True).count()
    total_candidates = Candidate.objects.count()
    
    # Safe import for Vote model (in case it's in another app)
    try:
        from elections.models import Vote
        votes_cast = Vote.objects.count()
    except:
        votes_cast = 0

    pending_verifications = Candidate.objects.filter(is_approved=False).count()
    results_ready = Election.objects.filter(end_date__lt=timezone.now(), is_active=False).count()

    context = {
        'total_voters': total_voters,
        'active_elections': active_elections,
        'total_candidates': total_candidates,
        'votes_cast': votes_cast,
        'pending_verifications': pending_verifications,
        'results_ready': results_ready,
    }

    return render(request, "dashboards/admin_dashboard.html", context)


def voter_dashboard(request):
    return render(request, "dashboards/voter_dashboard.html")


@login_required
def candidate_dashboard(request):
    if request.user.profile.role != 'candidate':
        return redirect('user_dashboard')  # or voter dashboard

    context = {
        'user': request.user
    }
    return render(request, 'dashboards/candidate_dashboard.html', context)


@login_required
def candidate_campaign(request):
    if request.user.profile.role != 'candidate':
        return redirect('user_dashboard')

    campaign, created = Campaign.objects.get_or_create(
        candidate=request.user
    )

    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            return redirect('candidate_dashboard')
    else:
        form = CampaignForm(instance=campaign)

    return render(request, 'campaign/candidate_campaign.html', {
        'form': form
    })

def view_campaigns(request):
    campaigns = Campaign.objects.select_related('candidate')
    return render(request, 'campaign/view_campaigns.html', {
        'campaigns': campaigns
    })

@login_required
def candidate_elections(request):
    elections = Election.objects.filter(is_active=True)
    return render(request, 'voter/elections_list.html', {
        'elections': elections
    })

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('users_home')

def voter_profile(request):
    """Display voter profile and verification status."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please complete your voter registration.')
        return redirect('voter_register')
    
    from .models import Vote
    user_votes = Vote.objects.filter(voter=voter).select_related('election', 'candidate')
    
    ctx = {
        'voter': voter,
        'user_votes': user_votes,
        'unread_notifications': voter.notifications.filter(is_read=False).count(),
    }
    return render(request, 'voter/profile.html', ctx)

def voter_elections_list(request):
    """Show active and upcoming elections available to voters."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please register as a voter first.')
        return redirect('voter_register')
    
    # Check if voter is verified
    if not voter.is_verified:
        messages.warning(
            request,
            "⚠️ Verification Required: Your account is not yet verified. "
            "You can view elections but cannot vote until verified by authorities."
        )

    # Get active and upcoming elections
    now = timezone.now()
    elections = Election.objects.filter(is_active=True).order_by('start_date')
    
    # Get elections where voter has already voted
    voted_elections = Vote.objects.filter(voter=voter).values_list('election_id', flat=True)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(elections, 10)
    page_obj = paginator.get_page(page)
    
    context = {
        'voter': voter,
        'elections': page_obj,
        'page_obj': page_obj,
        'voted_elections': list(voted_elections),
    }
    return render(request, 'voter/elections_list.html', context)



def voter_view_results(request, election_id=None):
    # Get all concluded elections
    published_elections = Election.objects.filter(end_date__lte=timezone.now()).order_by('-end_date')

    election = None
    stats = None
    total_votes = 0

    if election_id:
        election = get_object_or_404(Election, pk=election_id)
        # Aggregate votes per candidate
        votes_qs = Vote.objects.filter(candidate__election=election).values(
            'candidate__name', 'candidate__party__name'
        ).annotate(votes_count=models.Count('id')).order_by('-votes_count')

        stats = [
            {'candidate__name': v['candidate__name'],
             'candidate__party__name': v['candidate__party__name'],
             'votes': v['votes_count']}
            for v in votes_qs
        ]

        total_votes = sum(v['votes'] for v in stats) if stats else 0

    context = {
        'published_elections': published_elections,
        'election': election,
        'stats': stats,
        'total_votes': total_votes,
        'now': timezone.now(),
    }
    return render(request, 'voter/view_results.html', context)

def voter_notifications(request):
    """View all voter notifications."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        return redirect('voter_register')
    
    from .models import Notification
    notifications = Notification.objects.filter(voter=voter).order_by('-created_at')
    
    # Mark as read
    if request.method == 'POST':
        Notification.objects.filter(voter=voter, is_read=False).update(is_read=True)
        messages.success(request, 'Notifications marked as read.')
        return redirect('voter_notifications')
    
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(page)
    
    ctx = {
        'voter': voter,
        'notifications': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'voter/notifications.html', ctx)

@login_required
def voter_register(request):
    if hasattr(request.user, 'voter'):
        messages.info(request, "You have already registered as a voter.")
        return redirect('voter_dashboard')

    if request.method == 'POST':
        form = VoterRegistrationForm(request.POST)
        if form.is_valid():
            voter = form.save(commit=False)
            voter.user = request.user
            voter.is_verified = False
            voter.save()
            messages.success(
                request,
                "Registration submitted. Await admin verification."
            )
            return redirect('voter_dashboard')
    else:
        form = VoterRegistrationForm()

    return render(request, 'users/voter_register.html', {'form': form})

def voter_view_results_election(request, election_id):
    election = Election.objects.get(id=election_id)

    stats = (
        Vote.objects
        .filter(election=election)
        .values(
            'candidate__name',
            'candidate__party__name'
        )
        .annotate(votes=Count('id'))
        .order_by('-votes')
    )

    published_elections = Election.objects.filter(
        end_date__lte=timezone.now()
    )

    context = {
        'election': election,
        'stats': stats,
        'published_elections': published_elections,
        'now': timezone.now(),
    }

    return render(request, 'voter/view_result.html', context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import Voter, Candidate, Election, Vote

@login_required
def voter_cast_vote(request, election_id):
    voter = get_object_or_404(Voter, user=request.user)
    election = get_object_or_404(Election, pk=election_id)

    # Ensure election is active
    now = timezone.now()
    if not (election.start_date <= now <= election.end_date):
        messages.warning(request, "Voting for this election is not currently open.")
        return redirect('voter_elections_list')

    candidates = Candidate.objects.filter(election=election, is_approved=True)

    if request.method == "POST":
        candidate_id = request.POST.get('candidate_id')
        if candidate_id:
            candidate = get_object_or_404(Candidate, pk=candidate_id)
            # Check if voter already voted
            if Vote.objects.filter(voter=voter, election=election).exists():
                messages.error(request, "You have already voted in this election.")
            else:
                Vote.objects.create(voter=voter, candidate=candidate, election=election)
                messages.success(request, f"You have successfully voted for {candidate.name}.")
            return redirect('voter_elections_list')

    context = {
        'election': election,
        'candidates': candidates,
    }
    return render(request, 'voter/cast_vote.html', context)

# ==================== PASSWORD RESET VIEWS ====================

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    from_email = None  


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


@staff_member_required
def verify_voters(request):
    voters = Voter.objects.filter(is_verified=False)
    
    if request.method == "POST":
        voter_id = request.POST.get('voter_id')
        voter = get_object_or_404(Voter, id=voter_id)
        voter.is_verified = True
        voter.save()
        messages.success(request, f'{voter.user.username} has been verified.')
        return redirect('verify_voters')
    
    return render(request, 'users/verify_voters.html', {'voters': voters})



def voter_view_results_election(request, election_id):
    election = Election.objects.get(id=election_id)

    stats = (
        Vote.objects
        .filter(election=election)
        .values(
            'candidate__name',
            'candidate__party__name'
        )
        .annotate(votes=Count('id'))
        .order_by('-votes')
    )

    published_elections = Election.objects.filter(
        end_date__lte=timezone.now()
    )

    context = {
        'election': election,
        'stats': stats,
        'published_elections': published_elections,
        'now': timezone.now(),
    }

    return render(request, 'voter/view_result.html', context)
