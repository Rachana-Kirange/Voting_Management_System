from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .decorators import admin_required
from .forms import PartyForm, CandidateForm
from .models import Party, Candidate, Voter
from django.db.models import Count
from django.contrib.auth import get_user_model
from .forms import CustomUserChangeForm
from elections.models import Election
from elections.forms import ElectionForm


def home_view(request):
    return render(request, 'home.html')

def login_page(request):
    # If already authenticated, send to home hub
    if request.user.is_authenticated:
        return redirect('users_home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # After login go to the home page which acts as a central hub
            return redirect('users_home')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

def register_page(request):
    # if user is already authenticated send them to home
    if request.user.is_authenticated:
        return redirect('users_home')
    User = get_user_model()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        full_name = request.POST.get('full_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html')

        # create user and set optional attributes
        user = User.objects.create_user(username=username, email=email, password=password1)
        if hasattr(user, 'role') and role:
            user.role = role
        if hasattr(user, 'full_name') and full_name:
            user.full_name = full_name
        user.save()

        messages.success(request, 'Account created successfully — please log in')
        return redirect('login')

    return render(request, 'register.html')

def admin_dashboard(request):
    # Build quick stats for admin
    from django.utils import timezone
    from .models import Voter, Vote

    total_voters = Voter.objects.count()
    active_elections = Election.objects.filter(is_active=True).count()
    total_candidates = Candidate.objects.count()
    votes_cast = Vote.objects.count()
    pending_verifications = Candidate.objects.filter(is_approved=False).count()
    results_ready = Election.objects.filter(end_date__lt=timezone.now()).count()

    ctx = {
        'total_voters': total_voters,
        'active_elections': active_elections,
        'total_candidates': total_candidates,
        'votes_cast': votes_cast,
        'pending_verifications': pending_verifications,
        'results_ready': results_ready,
    }

    return render(request, "dashboards/admin_dashboard.html", ctx)

def voter_dashboard(request):
    return render(request, "dashboards/voter_dashboard.html")

def candidate_dashboard(request):
    return render(request, "dashboards/candidate_dashboard.html")


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('users_home')


# --- Admin CRUD for Party ---
@admin_required
def party_list(request):
    qs = Party.objects.all().order_by('name')
    q = request.GET.get('q')
    if q:
        qs = qs.filter(name__icontains=q)

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(page)

    return render(request, 'manage/party_list.html', {'parties': page_obj, 'page_obj': page_obj, 'q': q})


@admin_required
def party_create(request):
    if request.method == 'POST':
        form = PartyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party created')
            return redirect('party_list')
    else:
        form = PartyForm()
    return render(request, 'manage/party_form.html', {'form': form, 'title': 'Add Party'})


@admin_required
def party_edit(request, pk):
    obj = get_object_or_404(Party, pk=pk)
    if request.method == 'POST':
        form = PartyForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party updated')
            return redirect('party_list')
    else:
        form = PartyForm(instance=obj)
    return render(request, 'manage/party_form.html', {'form': form, 'title': 'Edit Party'})


@admin_required
def party_delete(request, pk):
    obj = get_object_or_404(Party, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Party deleted')
        return redirect('party_list')
    return render(request, 'manage/confirm_delete.html', {'object': obj, 'title': 'Delete Party'})


# --- Admin CRUD for Candidate ---
@admin_required
def candidate_list(request):
    qs = Candidate.objects.select_related('party').all().order_by('name')
    q = request.GET.get('q')
    party_id = request.GET.get('party')
    approved = request.GET.get('approved')
    if q:
        qs = qs.filter(name__icontains=q)
    if party_id:
        qs = qs.filter(party_id=party_id)
    if approved in ('1', '0'):
        qs = qs.filter(is_approved=(approved == '1'))

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page)
    parties = Party.objects.all()
    return render(request, 'manage/candidate_list.html', {'candidates': page_obj, 'page_obj': page_obj, 'q': q, 'parties': parties, 'party_id': party_id, 'approved': approved})


@admin_required
def candidate_create(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidate created')
            return redirect('candidate_list')
    else:
        form = CandidateForm()
    return render(request, 'manage/candidate_form.html', {'form': form, 'title': 'Add Candidate'})


@admin_required
def candidate_edit(request, pk):
    obj = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        form = CandidateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidate updated')
            return redirect('candidate_list')
    else:
        form = CandidateForm(instance=obj)
    return render(request, 'manage/candidate_form.html', {'form': form, 'title': 'Edit Candidate'})


@admin_required
def candidate_delete(request, pk):
    obj = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Candidate deleted')
        return redirect('candidate_list')
    return render(request, 'manage/confirm_delete.html', {'object': obj, 'title': 'Delete Candidate'})


@admin_required
def candidate_approve(request, pk):
    obj = get_object_or_404(Candidate, pk=pk)
    obj.is_approved = True
    obj.save()
    messages.success(request, f'Candidate {obj.name} approved')
    return redirect('candidate_list')


@admin_required
def candidate_unapprove(request, pk):
    obj = get_object_or_404(Candidate, pk=pk)
    obj.is_approved = False
    obj.save()
    messages.success(request, f'Candidate {obj.name} set to pending')
    return redirect('candidate_list')


# --- Admin CRUD for Elections ---
@admin_required
def election_list(request):
    qs = Election.objects.all().order_by('-start_date')
    q = request.GET.get('q')
    active = request.GET.get('active')
    if q:
        qs = qs.filter(title__icontains=q)
    if active in ('1','0'):
        qs = qs.filter(is_active=(active == '1'))

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page)
    return render(request, 'manage/election_list.html', {'elections': page_obj, 'page_obj': page_obj, 'q': q, 'active': active})


@admin_required
def election_create(request):
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Election created')
            return redirect('election_list')
    else:
        form = ElectionForm()
    return render(request, 'manage/election_form.html', {'form': form, 'title': 'Add Election'})


@admin_required
def election_edit(request, pk):
    obj = get_object_or_404(Election, pk=pk)
    if request.method == 'POST':
        form = ElectionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Election updated')
            return redirect('election_list')
    else:
        form = ElectionForm(instance=obj)
    return render(request, 'manage/election_form.html', {'form': form, 'title': 'Edit Election'})


@admin_required
def election_delete(request, pk):
    obj = get_object_or_404(Election, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Election deleted')
        return redirect('election_list')
    return render(request, 'manage/confirm_delete.html', {'object': obj, 'title': 'Delete Election'})


@admin_required
def audit_logs(request):
    from audit.models import AuditLog
    qs = AuditLog.objects.all().order_by('-created_at')
    q = request.GET.get('q')
    action = request.GET.get('action')
    if q:
        qs = qs.filter(target_model__icontains=q) | qs.filter(target_repr__icontains=q)
    if action:
        qs = qs.filter(action=action)

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(page)
    return render(request, 'manage/audit_list.html', {'logs': page_obj, 'page_obj': page_obj, 'q': q, 'action': action})


@admin_required
def backups_list(request):
    from backup.models import BackupRecord
    qs = BackupRecord.objects.all().order_by('-created_at')
    q = request.GET.get('q')
    success = request.GET.get('success')
    if q:
        qs = qs.filter(filename__icontains=q)
    if success in ('1','0'):
        qs = qs.filter(success=(success=='1'))

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(page)
    return render(request, 'manage/backup_list.html', {'records': page_obj, 'page_obj': page_obj, 'q': q, 'success': success})


@admin_required
def create_backup_view(request):
    # run the management command and return back to listings
    from django.core.management import call_command
    try:
        call_command('create_backup')
        messages.success(request, 'Backup command started')
    except Exception as e:
        messages.error(request, f'Backup failed: {e}')
    return redirect('backups_list')


@admin_required
def results_overview(request):
    elections = Election.objects.all().order_by('-start_date')
    return render(request, 'manage/results_overview.html', {'elections': elections})


@admin_required
def results_for_election(request, pk):
    election = get_object_or_404(Election, pk=pk)
    # count votes per candidate for this election
    from users.models import Vote
    stats = (
        Vote.objects.filter(election=election)
        .values('candidate__id', 'candidate__name', 'candidate__party__name')
        .annotate(votes=Count('id'))
        .order_by('-votes')
    )
    return render(request, 'manage/results_for_election.html', {'election': election, 'stats': stats})


@admin_required
def user_list(request):
    User = get_user_model()
    qs = User.objects.all().order_by('-created_at')
    q = request.GET.get('q')
    role = request.GET.get('role')
    active = request.GET.get('active')
    if q:
        qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q) | qs.filter(full_name__icontains=q)
    if role:
        qs = qs.filter(role=role)
    if active in ('1','0'):
        qs = qs.filter(is_active=(active == '1'))

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(page)
    return render(request, 'manage/user_list.html', {'users': page_obj, 'page_obj': page_obj, 'q': q, 'role': role, 'active': active})


@admin_required
def user_edit(request, pk):
    User = get_user_model()
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated')
            return redirect('user_list')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'manage/user_form.html', {'form': form, 'title': 'Edit User'})


@admin_required
def user_toggle_active(request, pk):
    User = get_user_model()
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f'User {user.username} active={user.is_active}')
    return redirect('user_list')


# --- VOTER WORKFLOW VIEWS ---

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


def voter_register(request):
    """Register as a voter."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    User = get_user_model()
    user = request.user
    
    # check if already registered as voter
    if hasattr(user, 'voter'):
        return redirect('voter_profile')
    
    if request.method == 'POST':
        voter_id = request.POST.get('voter_id')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        
        # Validate voter_id uniqueness
        if Voter.objects.filter(voter_id=voter_id).exists():
            messages.error(request, 'This voter ID is already registered.')
            return render(request, 'voter/register.html')
        
        # Create voter record
        voter = Voter.objects.create(
            user=user,
            voter_id=voter_id,
            mobile=mobile,
            address=address,
            verification_status='pending'
        )
        
        # Create notification
        from .models import Notification
        Notification.objects.create(
            voter=voter,
            title='Registration Received',
            message='Your voter registration has been received and is pending verification by authorities.',
            notification_type='registration'
        )
        
        messages.success(request, 'Registration submitted. Please await verification by authorities.')
        return redirect('voter_profile')
    
    return render(request, 'voter/register.html')


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


def voter_cast_vote(request, election_id):
    """Cast a vote in an election."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    from django.utils import timezone
    from .models import Vote
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please register as a voter first.')
        return redirect('voter_register')
    
    # Check voter verification
    if not voter.is_verified:
        messages.error(request, 'You must be verified by authorities before voting.')
        return redirect('voter_elections_list')
    
    election = get_object_or_404(Election, pk=election_id, is_active=True)
    
    # Check if voter has already voted in this election
    if Vote.objects.filter(voter=voter, election=election).exists():
        messages.error(request, 'You have already voted in this election.')
        return redirect('voter_elections_list')
    
    # Check election is ongoing
    now = timezone.now()
    if now < election.start_date or now > election.end_date:
        messages.error(request, 'This election is not currently open for voting.')
        return redirect('voter_elections_list')
    
    # Get eligible candidates for this election
    candidates = election.candidates.filter(is_approved=True).select_related('party')
    
    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        candidate = get_object_or_404(Candidate, pk=candidate_id, elections=election, is_approved=True)
        
        # Create vote record
        vote = Vote.objects.create(voter=voter, candidate=candidate, election=election)
        
        # Create confirmation notification
        from .models import Notification
        Notification.objects.create(
            voter=voter,
            title='Vote Confirmation',
            message=f'Your vote for {candidate.name} in {election.title} has been recorded successfully.',
            notification_type='vote_confirmation',
            election=election
        )
        
        messages.success(request, f'Your vote for {candidate.name} has been recorded.')
        return redirect('voter_vote_confirmation', election_id=election.id)
    
    ctx = {
        'voter': voter,
        'election': election,
        'candidates': candidates,
    }
    return render(request, 'voter/cast_vote.html', ctx)


def voter_vote_confirmation(request, election_id):
    """Show vote confirmation page."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        return redirect('voter_register')
    
    from .models import Vote
    election = get_object_or_404(Election, pk=election_id)
    vote = get_object_or_404(Vote, voter=voter, election=election)
    
    ctx = {
        'voter': voter,
        'election': election,
        'vote': vote,
    }
    return render(request, 'voter/vote_confirmation.html', ctx)


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
