from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from .forms import ElectionForm
from django.db.models import Q
from django.db import transaction 
# ✅ ADD THIS LINE:
from django.contrib.admin.models import LogEntry
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
from .forms import VoterRegistrationForm, CampaignForm, ElectionForm
User = get_user_model()

def home_view(request):
    return render(request, 'home.html')

def login_page(request):
    if request.user.is_authenticated:
        # Redirect admins to the default Django admin panel
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_dashboard')
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
                return redirect('admin_dashboard')
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
            # Set common fields
            user.role = role
            user.full_name = full_name

            # 🔐 ADMIN-SPECIFIC SECURITY
            if role == 'admin':
                user.is_staff = True              # needed to mark as admin-type user
                user.is_admin_approved = False    # 🚫 superuser must approve

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



# @login_required
# def candidate_dashboard(request):

#     if hasattr(request.user, 'role') and request.user.role != 'candidate':
#         return redirect('users_home')

    
#     try:
#         candidate = get_object_or_404(Candidate, user=request.user)
#     except:
        
#         messages.error(request, "Candidate profile not found.")
#         return redirect('users_home')

#     campaigns = Campaign.objects.filter(candidate=candidate)

#     return render(request, 'dashboards/candidate_dashboard.html', {
#         'candidate': candidate,
#         'campaigns': campaigns
#     })

@login_required
def my_campaigns(request):
    candidate = get_object_or_404(Candidate, user=request.user)
    campaigns = Campaign.objects.filter(candidate=candidate)
    return render(request, 'candidate/campaign/my_campaigns.html', {'campaigns': campaigns})

@login_required
def create_campaign(request):
    user = request.user

    # 🚫 Only candidates allowed
    if user.role != 'candidate':
        messages.error(request, "Only candidates can create campaigns.")
        return redirect('users_home')

    # 🚫 Candidate not approved by admin
    if not user.is_admin_approved:
        messages.warning(
            request,
            "Your candidate account is not verified yet. Please wait for admin approval."
        )
        return redirect('candidate_dashboard')
    candidate = get_object_or_404(Candidate, user=request.user)
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.candidate = candidate
            campaign.save()
            messages.success(request, "Campaign created successfully.")
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
            # voter.is_verified = False
            voter.save()
            messages.success(request, "Registration submitted. Await verification.")
            return redirect('voter_dashboard')
    else:
        form = VoterRegistrationForm()
    return render(request, 'users/voter_register.html', {'form': form})

from .forms import ProfileUpdateForm

@login_required
def voter_profile(request):
    # ✅ Safe retrieval of Voter object
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(
            request,
            "You are not registered as a voter. Please complete voter registration first."
        )
        return redirect('voter_register')  # redirect to voter registration page

    if request.method == "POST":
        request.user.email = request.POST.get("email")
        request.user.save()

        mobile_no = request.POST.get("mobile_no")
        if mobile_no:
            voter.mobile_no = mobile_no

        voter.address = request.POST.get("address")
        voter.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("voter_profile")

    context = {
        "voter": voter,
        "user_votes": Vote.objects.filter(voter=voter),
        "unread_notifications": Notification.objects.filter(
            voter=voter, is_read=False
        ).count(),
    }

    return render(request, 'voter/profile.html', context)



def voter_elections_list(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        voter = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.warning(request, 'Please register as a voter first.')
        return redirect('voter_register')
    
    if voter.verification_status != 'verified':
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
    
    user = request.user

    # 🚫 Admin cannot vote
    if user.role == 'admin':
        messages.error(request, "Admins are not allowed to vote.")
        return redirect('users_home')

    # 🚫 Candidate cannot vote
    if user.role == 'candidate':
        messages.error(request, "Candidates are not allowed to vote.")
        return redirect('candidate_dashboard')

    # 🚫 Only voters allowed
    if user.role != 'voter':
        messages.error(request, "Only voters can vote.")
        return redirect('users_home')

    election = get_object_or_404(Election, pk=election_id)
    voter = get_object_or_404(Voter, user=request.user)

    if voter.verification_status != 'verified':
        messages.error(request, "You are not verified to vote.")
        return redirect('voter_elections_list')

    if Vote.objects.filter(voter=voter, election=election).exists():
        messages.warning(request, "You have already voted.")
        vote = Vote.objects.get(voter=voter, election=election)
        return redirect('vote_confirmation', vote_id=vote.id)

    candidate_id = request.POST.get('candidate_id')
    candidate = get_object_or_404(Candidate, pk=candidate_id)

    # 🚫 Candidate not approved by admin
    if not candidate.is_approved:
        messages.error(
            request,
            "This candidate is not approved by admin yet."
        )
        return redirect('voter_elections_list')
    
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



# def voter_view_results(request):
    
#     elections = Election.objects.filter(
#         end_date__lte=timezone.now(),
#         results_published=True 
#     ).order_by('-end_date')

#     results_data = []
#     for election in elections:
#         votes = (
#             Vote.objects.filter(election=election)
#             .values('candidate__name', 'candidate__party__name')
#             .annotate(vote_count=Count('id')).order_by('-vote_count')
#         )
#         total_votes = sum(v['vote_count'] for v in votes)
#         processed_votes = []
#         for v in votes:
#             percentage = round((v['vote_count'] / total_votes) * 100, 2) if total_votes > 0 else 0
#             processed_votes.append({
#                 'candidate_name': v['candidate__name'],
#                 'party_name': v['candidate__party__name'],
#                 'votes': v['vote_count'],
#                 'percentage': percentage
#             })
#         results_data.append({'election': election, 'total_votes': total_votes, 'results': processed_votes})

#     return render(request, 'voter/view_results.html', {'results_data': results_data})

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
     # 🚫 Not a candidate
    if request.user.role != 'candidate':
        messages.error(request, "Access restricted to candidates only.")
        return redirect('users_home')

    try:
        candidate = Candidate.objects.get(user=request.user)
    except Candidate.DoesNotExist:
        messages.warning(
            request,
            "Your candidate profile is not created yet. Please contact admin."
        )
        return redirect('users_home')
    #  # 🚫 Candidate exists but NOT approved
    # if not candidate.is_approved or not request.user.is_admin_approved:
    #     messages.warning(
    #         request,
    #         "Your candidate account is pending admin verification."
    #     )
    #     return render(
    #         request,
    #         'candidate/pending_approval.html'
    #     )
    campaigns = Campaign.objects.filter(candidate=candidate)

    return render(request, 'candidate/dashboard.html', {
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


@login_required
def admin_dashboard(request):

    user = request.user

    # 🚫 Not admin or superuser
    if user.role != 'admin' and not user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect('voter_dashboard')  # change if your voter dashboard name differs

    # 🚫 Admin but NOT approved by superuser
    if user.role == 'admin' and not user.is_admin_approved:
        messages.warning(
            request,
            "Your admin account is not verified yet. Please wait for superuser approval."
        )
        return redirect('voter_dashboard')  # safe page

    # ✅ Approved admin OR superuser
    total_voters = Voter.objects.count()
    total_candidates = Candidate.objects.count()
    total_elections = Election.objects.count()
    pending_voters = Voter.objects.filter(verification_status='pending')
    
    pending_admins = User.objects.filter(
    role='admin',
    is_admin_approved=False
)

    all_candidates = Candidate.objects.select_related('party', 'user')
    all_voters = Voter.objects.select_related('user')
    all_elections = Election.objects.all().order_by('-start_date')

    context = {
        'total_voters': total_voters,
        'total_candidates': total_candidates,
        'total_elections': total_elections,
        'pending_voters': pending_voters,
        'elections': all_elections,
        'all_candidates': all_candidates,
        'all_voters': all_voters,
        'pending_admins': pending_admins,

    }

    return render(request, 'dashboards/admin_dashboard.html', context)


# @login_required
# def verify_voter(request, voter_id):
#     if request.method != 'POST':
#         return redirect('admin_dashboard')

#     if not (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
#         messages.error(request, "Access Denied: Admins only.")
#         return redirect('users_home')

#     voter = get_object_or_404(Voter, id=voter_id)
#     voter.verification_status = 'verified'
#     voter.verification_date = timezone.now()

#     voter.save()
    
#     # Notify the voter
#     Notification.objects.create(
#         voter=voter,
#         title="Account Verified",
#         message="Your account has been verified. You can now vote in active elections.",
#         notification_type="alert"
#     )
#     messages.success(request, f"Voter {voter.user.username} has been verified.")
#     return redirect('admin_dashboard')

# # @login_required
# # def delete_voter(request, voter_id):
#     if request.method != 'POST':
#         return redirect('admin_dashboard')

#     if not (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
#         messages.error(request, "Access Denied: Admins only.")
#         return redirect('users_home')

#     voter = get_object_or_404(Voter, id=voter_id)
#     user = voter.user
#     voter.delete()
#     user.delete() # Delete the login account too
    
#     messages.warning(request, "Voter removed from system.")
#     return redirect('admin_dashboard')

# @login_required
# def create_election(request):
#     if not request.user.is_staff: return redirect('users_home')

#     if request.method == 'POST':
#         form = ElectionForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "New election created successfully!")
#             return redirect('admin_dashboard')
#     else:
#         form = ElectionForm()
    
#     return render(request, 'admin/create_election.html', {'form': form})

@login_required
def create_election(request):
    if not (request.user.is_superuser or request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied.")
        return redirect('users_home')

    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            
            election = form.save(commit=False)
            election.save()
            
            selected_candidates = form.cleaned_data.get('candidates')
            if selected_candidates:
                for candidate in selected_candidates:
            
                    candidate.elections.add(election)
                    
                    Campaign.objects.get_or_create(
                        candidate=candidate,
                        election=election,
                        defaults={
                            'message': f"Vote for {candidate.name}! Campaigning for {election.title}."
                        }
                    )

            messages.success(request, f"Election '{election.title}' created with {selected_candidates.count()} candidates!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ElectionForm()
    
    return render(request, 'admin/create_election.html', {'form': form})
@login_required
def toggle_election(request, election_id):
    if not (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied: Admins only.")
        return redirect('users_home')

    election = get_object_or_404(Election, id=election_id)
    election.is_active = not election.is_active # Switch True/False
    election.save()
    
    status = "Active" if election.is_active else "Closed"
    messages.info(request, f"Election is now {status}.")
    return redirect('admin_dashboard')

@login_required
def publish_results(request, election_id):
    if not (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied: Admins only.")
        return redirect('users_home')

    election = get_object_or_404(Election, id=election_id)
    election.results_published = True
    election.save()
    
    messages.success(request, f"Results for {election.title} have been published.")
    return redirect('admin_dashboard')

@login_required
def approve_candidate(request, candidate_id):
    if not (request.user.is_superuser or request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied.")
        return redirect('users_home')

    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # Approve candidate profile
    candidate.is_approved = True
    candidate.save()

    # ✅ Approve the linked user as well
    user = candidate.user
    user.is_admin_approved = True
    user.save()

    messages.success(request, f"Candidate {candidate.name} approved successfully.")
    return redirect('admin_dashboard')


@login_required
def delete_candidate(request, candidate_id):
    # Security check
    if not (request.user.is_superuser or request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied.")
        return redirect('users_home')

    candidate = get_object_or_404(Candidate, id=candidate_id)
    name = candidate.name
    # Delete the associated user account if needed, or just the candidate profile
    # Here we delete the profile
    candidate.delete()
    messages.warning(request, f"Candidate {name} has been removed.")
    return redirect('admin_dashboard')


@login_required
def delete_election(request, election_id):
    if not (request.user.is_superuser or request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied.")
        return redirect('users_home')

    election = get_object_or_404(Election, id=election_id)
    title = election.title
    election.delete()
    messages.warning(request, f"Election '{title}' has been deleted.")
    return redirect('admin_dashboard')
    
@login_required
def admin_voter_management(request):
    if not (request.user.is_superuser or request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied.")
        return redirect('users_home')

    search_query = request.GET.get('q', '')
    filter_status = request.GET.get('status', 'all')

    voters = Voter.objects.select_related('user').all().order_by('-user__created_at')

    if search_query:
        voters = voters.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(voter_id__icontains=search_query) |
            Q(mobile_no__icontains=search_query)
        )

    if filter_status == 'verified':
        voters = voters.filter(verification_status='verified')
    elif filter_status == 'pending':
        voters = voters.filter(verification_status='pending')

    paginator = Paginator(voters, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/manage_voters.html', {
        'voters': page_obj,
        'search_query': search_query,
        'filter_status': filter_status,
        'total_count': voters.count()
    })

@login_required
def verify_voter(request, voter_id):
    if not (request.user.is_superuser or request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        return redirect('users_home')
    
    voter = get_object_or_404(Voter, id=voter_id)
    voter.verification_status = 'verified'
    voter.verification_date = timezone.now()
    voter.save()
    
    Notification.objects.create(
        voter=voter, 
        title="Account Verified",
        message="Your account has been verified. You can now vote.", 
        notification_type="verification"
    )
    
    messages.success(request, f"Voter {voter.user.username} verified successfully.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_voter_management'))

@login_required
def delete_voter(request, voter_id):
    if not (request.user.is_superuser or request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access Denied.")
        return redirect('users_home')

    try:
        with transaction.atomic():
            voter = get_object_or_404(Voter, id=voter_id)
            user = voter.user
            username = user.username

            Vote.objects.filter(voter=voter).delete()
            Notification.objects.filter(voter=voter).delete()

            LogEntry.objects.filter(user_id=user.pk).delete()
            voter.delete()
            user.delete()

            messages.warning(request, f"Voter account for {username} successfully deleted.")

    except Exception as e:
        print(f"Delete Error: {e}") 
        messages.error(request, f"Could not delete voter: {e}")
    
    return redirect(request.META.get('HTTP_REFERER', 'admin_voter_management'))


@login_required
def approve_admin(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "Only superuser can approve admins.")
        return redirect('users_home')

    admin_user = get_object_or_404(User, id=user_id, role='admin')

    admin_user.is_admin_approved = True
    admin_user.save()

    messages.success(
        request,
        f"Admin access approved for {admin_user.username}"
    )
    return redirect('admin_dashboard')
