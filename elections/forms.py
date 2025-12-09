from django import forms
from .models import Election


class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ('title', 'description', 'election_type', 'start_date', 'end_date', 'is_active')
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
