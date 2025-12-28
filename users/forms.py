from django import forms
from .models import Voter, Campaign, Election,Candidate
from django.contrib.auth import get_user_model

User = get_user_model()

# --- 1. User Creation Form (Required for Admin) ---
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'role', 'is_active', 'is_staff')


# --- 2. Voter Registration Form ---
class VoterRegistrationForm(forms.ModelForm):
    class Meta:
        model = Voter
        # ✅ FIXED: Changed 'mobile' to 'mobile_no' to match your model
        fields = ['voter_id', 'mobile_no', 'address']
        widgets = {
            'voter_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Voter ID'}),
            'mobile_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Address'}),
        }


# --- 3. Campaign Creation Form ---
class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        # ✅ FIXED: Removed 'slogan' because it is not in your models.py
        fields = ['election', 'message']
        widgets = {
            'election': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your campaign message...'}),
        }

    def __init__(self, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)
        # Only show active elections
        self.fields['election'].queryset = Election.objects.filter(is_active=True)


# --- 4. Admin Election Form ---
class ElectionForm(forms.ModelForm):
    # Field definition
    candidates = forms.ModelMultipleChoiceField(
        queryset=Candidate.objects.none(), # Empty initially, we fill it in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date', 'is_active', 'candidates']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Election Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 20px; height: 20px;'}),
        }

    def __init__(self, *args, **kwargs):
        super(ElectionForm, self).__init__(*args, **kwargs)
        # ✅ FORCE REFRESH: Fetch all candidates every time the form loads
        self.fields['candidates'].queryset = Candidate.objects.all()
        # Optional: Custom label for the checkboxes
        self.fields['candidates'].label_from_instance = lambda obj: f"{obj.name} ({obj.party.name})"

# --- 5. Voter Profile Update Form ---from django import forms
from django.contrib.auth.models import User
from .models import Voter

class ProfileUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits")

        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits")

        return phone
