from django import forms
from accounts.models import CustomUser
from teams.models import ResponseTeam
from incidents.models import Incident
import json

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'status', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1-555-0199'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class CustomUserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep current password'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'status']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        new_pwd = self.cleaned_data.get('new_password')
        if new_pwd:
            user.set_password(new_pwd)
        if commit:
            user.save()
        return user


class ResponseTeamForm(forms.ModelForm):
    incident_types_text = forms.CharField(
        required=False,
        help_text="Comma-separated incident types: e.g. medical, fire, security",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'medical, fire, security'})
    )

    class Meta:
        model = ResponseTeam
        fields = ['user', 'name', 'zone', 'availability_status']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Team / Unit Name'}),
            'zone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campus Zone'}),
            'availability_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only list users with role responder who don't already have a team (or current team's user)
        if self.instance and self.instance.pk:
            self.fields['incident_types_text'].initial = ", ".join(self.instance.incident_types)
            self.fields['user'].queryset = CustomUser.objects.filter(
                role='responder'
            )
        else:
            self.fields['user'].queryset = CustomUser.objects.filter(
                role='responder',
                response_team__isnull=True
            )

    def clean_incident_types_text(self):
        text = self.cleaned_data.get('incident_types_text', '')
        if not text:
            return ['medical', 'security']
        types = [t.strip().lower() for t in text.split(',') if t.strip()]
        return types

    def save(self, commit=True):
        team = super().save(commit=False)
        team.incident_types = self.cleaned_data.get('incident_types_text', ['medical', 'security'])
        if commit:
            team.save()
        return team


class IncidentActionForm(forms.Form):
    status = forms.ChoiceField(
        choices=Incident.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    assigned_team = forms.ModelChoiceField(
        queryset=ResponseTeam.objects.all(),
        required=False,
        empty_label="-- Select Response Team --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Action notes / Reason'})
    )
