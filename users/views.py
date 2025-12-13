from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.utils import timezone

# Your app-specific imports (adjust if models/forms are in different apps)
from .decorators import admin_required
from .forms import PartyForm, CandidateForm, CustomUserChangeForm
from .models import Party, Candidate, Voter
from elections.models import Election
from elections.forms import ElectionForm


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


def candidate_dashboard(request):
    return render(request, "dashboards/candidate_dashboard.html")


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
    
    from django.utils import timezone
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please register as a voter first.')
        return redirect('voter_register')
    
    # Get active and upcoming elections
    now = timezone.now()
    elections = Election.objects.filter(is_active=True).order_by('start_date')
    
    # Get voters' votes for this election
    from .models import Vote
    voted_elections = Vote.objects.filter(voter=voter).values_list('election_id', flat=True)
    
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(elections, 10)
    page_obj = paginator.get_page(page)
    
    ctx = {
        'voter': voter,
        'elections': page_obj,
        'page_obj': page_obj,
        'voted_elections': list(voted_elections),
    }
    return render(request, 'voter/elections_list.html', ctx)
def voter_elections_list(request):
    """Show active and upcoming elections available to voters."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    from django.utils import timezone
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please register as a voter first.')
        return redirect('voter_register')
    
    # Get active and upcoming elections
    now = timezone.now()
    elections = Election.objects.filter(is_active=True).order_by('start_date')
    
    # Get voters' votes for this election
    from .models import Vote
    voted_elections = Vote.objects.filter(voter=voter).values_list('election_id', flat=True)
    
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(elections, 10)
    page_obj = paginator.get_page(page)
    
    ctx = {
        'voter': voter,
        'elections': page_obj,
        'page_obj': page_obj,
        'voted_elections': list(voted_elections),
    }
    return render(request, 'voter/elections_list.html', ctx)

def voter_view_results(request, election_id=None):
    """View published election results."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    from django.utils import timezone
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        return redirect('voter_register')
    
    # Get published elections (end_date passed)
    now = timezone.now()
    published = Election.objects.filter(end_date__lt=now).order_by('-end_date')
    
    if election_id:
        election = get_object_or_404(Election, pk=election_id, end_date__lt=now)
    else:
        election = published.first()
    
    if not election:
        messages.info(request, 'No published results available yet.')
        return redirect('voter_elections_list')
    
    # Get results for this election
    from .models import Vote
    from django.db.models import Count
    stats = (
        Vote.objects.filter(election=election)
        .values('candidate__id', 'candidate__name', 'candidate__party__name')
        .annotate(votes=Count('id'))
        .order_by('-votes')
    )
    
    ctx = {
        'voter': voter,
        'election': election,
        'stats': stats,
        'published_elections': published,
    }
    return render(request, 'voter/view_results.html', ctx)

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