from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, EmergencyContact, Incident


class UserRegistrationForm(forms.ModelForm):
    student_id = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. SC-84920',
            'autocomplete': 'off'
        })
    )
    phone_number = forms.CharField(
        max_length=25, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+1 (555) 019-2834',
            'autocomplete': 'tel'
        })
    )
    dormitory_block = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. West Campus, Hall B, Room 304'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a secure password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Choose a username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'student@university.edu'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'student@university.edu'})
    )

    class Meta:
        model = UserProfile
        fields = [
            'student_id', 'phone_number', 'dormitory_block', 
            'blood_group', 'medical_allergies', 'emergency_notes'
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. SC-84920'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+1 (555) 019-2834'}),
            'dormitory_block': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. West Campus, Hall B, Room 304'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'medical_allergies': forms.Textarea(attrs={
                'class': 'form-textarea', 
                'rows': 3, 
                'placeholder': 'List known allergies (e.g. penicillin, peanuts), asthma, medications...'
            }),
            'emergency_notes': forms.Textarea(attrs={
                'class': 'form-textarea', 
                'rows': 3, 
                'placeholder': 'Special notes or instructions for first responder units...'
            }),
        }


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ['incident_type', 'urgency', 'description', 'location_name', 'latitude', 'longitude', 'image']
        widgets = {
            'incident_type': forms.Select(attrs={'class': 'form-select', 'id': 'incident_type'}),
            'urgency': forms.Select(attrs={'class': 'form-select', 'id': 'urgency'}),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea', 
                'rows': 4, 
                'id': 'description',
                'placeholder': 'Describe what is happening, who is involved, and any immediate hazards...'
            }),
            'location_name': forms.TextInput(attrs={
                'class': 'form-input', 
                'id': 'location_name',
                'placeholder': 'e.g. Science Complex - 2nd Floor Lab 204'
            }),
            'latitude': forms.HiddenInput(attrs={'id': 'id_latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'id_longitude'}),
            'image': forms.FileInput(attrs={'class': 'form-file-input', 'id': 'image_upload', 'accept': 'image/*'}),
        }


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ['name', 'relationship', 'phone_number', 'is_primary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Contact Name (e.g. Mom, Roommate)'}),
            'relationship': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Relationship (e.g. Parent, Friend, Advisor)'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+1 (555) 234-5678'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
