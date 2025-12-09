from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'role')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'role', 'is_active', 'is_staff')


from .models import Party, Candidate


class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = ('name',)


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ('name', 'age', 'party', 'area', 'user', 'elections')
