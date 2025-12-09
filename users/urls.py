from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='users_home'),   # corrected
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_page, name='register'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('voter-dashboard/', views.voter_dashboard, name='voter_dashboard'),
    path('candidate-dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    # officer dashboard removed (not part of project requirements)
    # Admin management UI for parties and candidates
    path('manage/parties/', views.party_list, name='party_list'),
    path('manage/parties/add/', views.party_create, name='party_add'),
    path('manage/parties/<int:pk>/edit/', views.party_edit, name='party_edit'),
    path('manage/parties/<int:pk>/delete/', views.party_delete, name='party_delete'),

    path('manage/candidates/', views.candidate_list, name='candidate_list'),
    path('manage/candidates/add/', views.candidate_create, name='candidate_add'),
    path('manage/candidates/<int:pk>/edit/', views.candidate_edit, name='candidate_edit'),
    path('manage/candidates/<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
    path('manage/candidates/<int:pk>/approve/', views.candidate_approve, name='candidate_approve'),
    path('manage/candidates/<int:pk>/unapprove/', views.candidate_unapprove, name='candidate_unapprove'),
    # Elections management
    path('manage/elections/', views.election_list, name='election_list'),
    path('manage/elections/add/', views.election_create, name='election_add'),
    path('manage/elections/<int:pk>/edit/', views.election_edit, name='election_edit'),
    path('manage/elections/<int:pk>/delete/', views.election_delete, name='election_delete'),
    # User management
    path('manage/users/', views.user_list, name='user_list'),
    path('manage/users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('manage/users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('manage/audit/', views.audit_logs, name='audit_list'),
    path('manage/backups/', views.backups_list, name='backups_list'),
    path('manage/backups/create/', views.create_backup_view, name='backups_create'),
    path('manage/results/', views.results_overview, name='results_overview'),
    path('manage/results/<int:pk>/', views.results_for_election, name='results_for_election'),
    
    # Voter workflow URLs
    path('voter/profile/', views.voter_profile, name='voter_profile'),
    path('voter/register/', views.voter_register, name='voter_register'),
    path('voter/elections/', views.voter_elections_list, name='voter_elections_list'),
    path('voter/elections/<int:election_id>/vote/', views.voter_cast_vote, name='voter_cast_vote'),
    path('voter/elections/<int:election_id>/confirmation/', views.voter_vote_confirmation, name='voter_vote_confirmation'),
    path('voter/results/', views.voter_view_results, name='voter_view_results'),
    path('voter/results/<int:election_id>/', views.voter_view_results, name='voter_view_results_election'),
    path('voter/notifications/', views.voter_notifications, name='voter_notifications'),
]
