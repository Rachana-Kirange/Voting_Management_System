from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='users_home'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_page, name='register'),
    
    path('voter-dashboard/', views.voter_dashboard, name='voter_dashboard'),
    path('candidate-dashboard/', views.candidate_dashboard, name='candidate_dashboard'),

    path('voter/profile/', views.voter_profile, name='voter_profile'),
    path('voter/register/', views.voter_register, name='voter_register'),
    path('voter/elections/', views.voter_elections_list, name='voter_elections_list'),
    path('voter/notifications/', views.voter_notifications, name='voter_notifications'),
    
    path('campaigns/', views.view_campaigns, name='view_campaigns'),
    path('voter/elections/<int:election_id>/campaigns/', views.voter_view_campaigns, name='voter_view_campaigns'),
    
    path('users/vote/<int:election_id>/', views.voter_cast_vote, name='voter_cast_vote'),
    path('voter/vote-confirmation/<int:vote_id>/', views.vote_confirmation, name='vote_confirmation'),

    path('voter/results/', views.voter_view_results, name='voter_view_results'),
    path('voter/results/<int:election_id>/', views.voter_view_results_election, name='voter_view_results_election'),

    path('candidate/elections/', views.candidate_elections, name='candidate_elections'),
    path('candidate/campaigns/', views.my_campaigns, name='my_campaigns'),
    path('candidate/campaign/create/', views.create_campaign, name='create_campaign'),

    path('reset_password/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset_password_sent/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/verify-voter/<int:voter_id>/', views.verify_voter, name='verify_voter'),
    path('admin/delete-voter/<int:voter_id>/', views.delete_voter, name='delete_voter'),
    path('admin/create-election/', views.create_election, name='create_election'),
    path('admin/toggle-election/<int:election_id>/', views.toggle_election, name='toggle_election'),
    path('admin/publish-results/<int:election_id>/', views.publish_results, name='publish_results'),
]