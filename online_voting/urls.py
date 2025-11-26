from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# Temporary dashboard views (we'll replace later)
def admin_dashboard(request):
    return HttpResponse("Admin Dashboard")

def voter_dashboard(request):
    return HttpResponse("Voter Dashboard")

def candidate_dashboard(request):
    return HttpResponse("Candidate Dashboard")

def officer_dashboard(request):
    return HttpResponse("Poll Officer Dashboard")


urlpatterns = [
    path('admin/', admin.site.urls),

    # include users app URLs
    path('users/', include('users.urls')),

    # dashboards
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('voter_dashboard/', voter_dashboard, name='voter_dashboard'),
    path('candidate_dashboard/', candidate_dashboard, name='candidate_dashboard'),
    path('officer_dashboard/', officer_dashboard, name='officer_dashboard'),
]
