from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count

from .models import Party, Candidate, Voter, Vote, Election, Campaign, Notification
from .forms import VoterRegistrationForm, CampaignForm


def home_view(request):
    return render(request, 'home.html')

def login_page(request):
    if request.user.is_authenticated:
        # Redirect admins to the default Django admin panel
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/admin/')
        return redirect('users_home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Check role after login
            if user.is_superuser or user.is_staff:
                return redirect('/admin/')
            return redirect('users_home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')



# def register_page(request):
#     if request.user.is_authenticated:
#         return redirect('users_home')

#     User = get_user_model()

#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         role = request.POST.get('role')  
#         full_name = request.POST.get('full_name')
#         password1 = request.POST.get('password1')
#         password2 = request.POST.get('password2')

#         if password1 != password2:
#             messages.error(request, 'Passwords do not match.')
#             return render(request, 'register.html')

#         if User.objects.filter(username=username).exists():
#             messages.error(request, 'Username already taken.')
#             return render(request, 'register.html')

#         try:
#             user = User.objects.create_user(
#                 username=username, email=email or '', password=password1
#             )
#             if hasattr(user, 'role') and role:
#                 user.role = role
#             if hasattr(user, 'full_name') and full_name:
#                 user.full_name = full_name
#             user.save()

#             messages.success(request, 'Account created! Please log in.')
#             return redirect('login')
#         except Exception as e:
#             messages.error(request, 'An error occurred during registration.')
#             print(e)

#     return render(request, 'register.html')
# users/views.py

def register_page(request):
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
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'register.html')

        try:
            # 1. Create the User
            user = User.objects.create_user(
                username=username, email=email or '', password=password1
            )
            if hasattr(user, 'role') and role:
                user.role = role
            if hasattr(user, 'full_name') and full_name:
                user.full_name = full_name
            user.save()

            # 2. Automatically create the Profile based on Role
            if role == 'candidate':
                # FIX: Get or create a default "Independent" party to satisfy the database rule
                default_party, created = Party.objects.get_or_create(
                    name="Independent", 
                    defaults={'name': "Independent"} # Add other required fields if Party has them
                )

                Candidate.objects.create(
                    user=user, 
                    name=full_name if full_name else username,
                    age=25,  # Default age
                    area="Pending Assignment",
                    party=default_party # ✅ ASSIGN THE PARTY HERE
                )

            elif role == 'voter':
                import uuid
                Voter.objects.create(
                    user=user,
                    voter_id=str(uuid.uuid4())[:10].upper()
                )

            messages.success(request, 'Account created! Please log in.')
            return redirect('login')

        except Exception as e:
            # If an error happens (like missing Party fields), print it and delete the user
            print(f"Registration Error: {e}")
            if 'user' in locals():
                user.delete() # Clean up the broken user
            messages.error(request, f'Registration failed: {e}')

    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('users_home')



@login_required
def candidate_dashboard(request):
    # 1. Check if user is a candidate
    if hasattr(request.user, 'role') and request.user.role != 'candidate':
        return redirect('users_home')

    # 2. Get the Candidate profile
    try:
        candidate = get_object_or_404(Candidate, user=request.user)
    except:
        # If profile is missing, redirect safely instead of crashing
        messages.error(request, "Candidate profile not found.")
        return redirect('users_home')

    campaigns = Campaign.objects.filter(candidate=candidate)

    # ✅ FIXED: The path now matches your file location
    # users/templates/dashboards/candidate_dashboard.html
    return render(request, 'dashboards/candidate_dashboard.html', {
        'candidate': candidate,
        'campaigns': campaigns
    })

@login_required
def my_campaigns(request):
    candidate = Candidate.objects.get(user=request.user)
    campaigns = Campaign.objects.filter(candidate=candidate)
    return render(request, 'candidate/campaign/my_campaigns.html', {'campaigns': campaigns})

@login_required
def create_campaign(request):
    candidate = Candidate.objects.get(user=request.user)
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.candidate = candidate
            campaign.save()
            return redirect('my_campaigns')
    else:
        form = CampaignForm()
    return render(request, 'candidate/campaign/create_campaign.html', {'form': form})

def view_campaigns(request):
    campaigns = Campaign.objects.select_related('candidate')
    return render(request, 'campaign/view_campaigns.html', {'campaigns': campaigns})

@login_required
def candidate_elections(request):
    elections = Election.objects.all()
    return render(request, 'candidate/elections.html', {'elections': elections})



def voter_dashboard(request):
    return render(request, "dashboards/voter_dashboard.html")

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
            messages.success(request, "Registration submitted. Await verification.")
            return redirect('voter_dashboard')
    else:
        form = VoterRegistrationForm()
    return render(request, 'users/voter_register.html', {'form': form})

def voter_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please complete your voter registration.')
        return redirect('voter_register')
    
    user_votes = Vote.objects.filter(voter=voter).select_related('election', 'candidate')
    
    ctx = {
        'voter': voter,
        'user_votes': user_votes,
        'unread_notifications': voter.notifications.filter(is_read=False).count(),
    }
    return render(request, 'voter/profile.html', ctx)

def voter_elections_list(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please register as a voter first.')
        return redirect('voter_register')
    
    if not voter.is_verified:
        messages.warning(request, "Verification Required: You cannot vote until verified.")

    # Show active elections
    elections = Election.objects.filter(is_active=True).order_by('start_date')
    voted_elections = Vote.objects.filter(voter=voter).values_list('election_id', flat=True)
    
    paginator = Paginator(elections, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    context = {
        'voter': voter,
        'elections': page_obj,
        'page_obj': page_obj,
        'voted_elections': list(voted_elections),
    }
    return render(request, 'voter/elections_list.html', context)

@login_required
def voter_view_campaigns(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    campaigns = Campaign.objects.filter(election=election).select_related('candidate', 'candidate__party')
    voter = get_object_or_404(Voter, user=request.user)

    voter_votes = Vote.objects.filter(voter=voter, election=election)
    voted_candidate_ids = voter_votes.values_list('candidate_id', flat=True)
    
    if Vote.objects.filter(voter=voter, election=election).exists():
        messages.info(request, "You have already voted in this election.")
        return redirect('voter_elections_list')

    return render(request, 'voter/campaigns.html', {
        'election': election,
        'campaigns': campaigns,
        'voted_candidate_ids': voted_candidate_ids,
        'voter': voter 
    })

@login_required
def voter_cast_vote(request, election_id):
    if request.method != "POST":
        return redirect('voter_elections_list')

    election = get_object_or_404(Election, pk=election_id)
    voter = get_object_or_404(Voter, user=request.user)

    if not voter.is_verified:
        messages.error(request, "You are not verified to vote.")
        return redirect('voter_elections_list')

    if Vote.objects.filter(voter=voter, election=election).exists():
        messages.warning(request, "You have already voted.")
        vote = Vote.objects.get(voter=voter, election=election)
        return redirect('vote_confirmation', vote_id=vote.id)

    candidate_id = request.POST.get('candidate_id')
    candidate = get_object_or_404(Candidate, pk=candidate_id)

    vote = Vote.objects.create(voter=voter, candidate=candidate, election=election)
    Notification.objects.create(
        voter=voter, title="Vote Submitted",
        message=f"You voted in {election.title}.",
        notification_type="vote_confirmation", election=election
    )
    return redirect('vote_confirmation', vote_id=vote.id)

@login_required
def vote_confirmation(request, vote_id):
    vote = get_object_or_404(Vote, id=vote_id)
    return render(request, 'voter/vote_confirmation.html', {'vote': vote, 'election': vote.election})

def voter_notifications(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        return redirect('voter_register')
    
    notifications = Notification.objects.filter(voter=voter).order_by('-created_at')
    
    if request.method == 'POST':
        Notification.objects.filter(voter=voter, is_read=False).update(is_read=True)
        messages.success(request, 'Notifications marked as read.')
        return redirect('voter_notifications')
    
    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'voter/notifications.html', {
        'voter': voter, 'notifications': page_obj, 'page_obj': page_obj
    })



def voter_view_results(request):
    
    elections = Election.objects.filter(
        end_date__lte=timezone.now(),
        results_published=True 
    ).order_by('-end_date')

    results_data = []
    for election in elections:
        votes = (
            Vote.objects.filter(election=election)
            .values('candidate__name', 'candidate__party__name')
            .annotate(vote_count=Count('id')).order_by('-vote_count')
        )
        total_votes = sum(v['vote_count'] for v in votes)
        processed_votes = []
        for v in votes:
            percentage = round((v['vote_count'] / total_votes) * 100, 2) if total_votes > 0 else 0
            processed_votes.append({
                'candidate_name': v['candidate__name'],
                'party_name': v['candidate__party__name'],
                'votes': v['vote_count'],
                'percentage': percentage
            })
        results_data.append({'election': election, 'total_votes': total_votes, 'results': processed_votes})

    return render(request, 'voter/view_results.html', {'results_data': results_data})

def voter_view_results_election(request, election_id):

    election = get_object_or_404(Election, id=election_id)

    if not election.results_published:
        messages.error(request, "Results for this election are not yet published.")
        return redirect('voter_view_results')

    stats_queryset = (
        Vote.objects.filter(election=election)
        .values('candidate__name', 'candidate__party__name')
        .annotate(votes=Count('id')).order_by('-votes')
    )
    
    total_votes = sum(item['votes'] for item in stats_queryset)
    
    stats = []
    for item in stats_queryset:
        percentage = (item['votes'] / total_votes * 100) if total_votes > 0 else 0
        item['percentage'] = percentage
        stats.append(item)

    published_elections = Election.objects.filter(
        results_published=True
    ).order_by('-end_date')

    return render(request, 'voter/view_results.html', {
        'election': election,
        'stats': stats,            
        'total_votes': total_votes,
        'published_elections': published_elections,
        'now': timezone.now(),
    })

def voter_view_results(request):

    published_elections = Election.objects.filter(
        results_published=True
    ).order_by('-end_date')

    if not published_elections.exists():
        return render(request, 'voter/view_results.html', {
            'published_elections': [],
            'election': None
        })

    latest_election = published_elections.first()

    stats_queryset = (
        Vote.objects.filter(election=latest_election)
        .values('candidate__name', 'candidate__party__name')
        .annotate(votes=Count('id')).order_by('-votes')
    )
    
    total_votes = sum(item['votes'] for item in stats_queryset)
    
    stats = []
    for item in stats_queryset:
        percentage = (item['votes'] / total_votes * 100) if total_votes > 0 else 0
        item['percentage'] = percentage
        stats.append(item)

    context = {
        'election': latest_election,         
        'stats': stats,                      
        'total_votes': total_votes,
        'published_elections': published_elections, 
        'now': timezone.now(),
    }

    return render(request, 'voter/view_results.html', context)

@login_required
def candidate_dashboard(request):
    if hasattr(request.user, 'role') and request.user.role != 'candidate':
        messages.error(request, "Access restricted to candidates only.")
        return redirect('users_home')
    try:
        candidate = Candidate.objects.get(user=request.user)
    except Candidate.DoesNotExist:
        messages.warning(request, "Your Candidate Profile is not set up yet. Please contact the Admin.")
        return redirect('users_home')

    campaigns = Campaign.objects.filter(candidate=candidate)

    return render(request, 'dashboards/candidate_dashboard.html', {
        'candidate': candidate, 
        'campaigns': campaigns
    })

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