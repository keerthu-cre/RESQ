from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('', 'Select Blood Group'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    student_id = models.CharField(max_length=50, blank=True, help_text="e.g. SC-84920")
    phone_number = models.CharField(max_length=25, blank=True, help_text="Your mobile contact")
    dormitory_block = models.CharField(max_length=100, blank=True, help_text="e.g. West Campus, Hall B, Room 304")
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    medical_allergies = models.TextField(blank=True, help_text="Allergies, chronic conditions, regular medications")
    emergency_notes = models.TextField(blank=True, help_text="Notes for first responders (e.g. asthma inhaler in bag)")
    
    # Accessibility preferences
    dark_mode = models.BooleanField(default=False)
    high_contrast = models.BooleanField(default=False)
    large_text = models.BooleanField(default=False)
    reduce_motion = models.BooleanField(default=False)
    voice_assist = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.student_id or 'No ID'})"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts', null=True, blank=True)
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=80, help_text="e.g. Campus Police, Medical Unit, Parent, Roommate")
    phone_number = models.CharField(max_length=25)
    is_primary = models.BooleanField(default=False)
    is_campus_service = models.BooleanField(default=False, help_text="Official 24/7 campus safety hotline")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_campus_service', '-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.phone_number}"


class Incident(models.Model):
    INCIDENT_TYPES = [
        ('EMERGENCY', 'Emergency SOS'),
        ('MEDICAL', 'Medical Emergency'),
        ('ACCIDENT', 'Accident'),
        ('FIRE', 'Fire'),
        ('PHYSICAL_THREAT', 'Physical Threat'),
        ('SUSPICIOUS', 'Suspicious Activity'),
        ('INFRASTRUCTURE', 'Unsafe Infrastructure'),
        ('OTHER', 'Other'),
    ]

    URGENCY_LEVELS = [
        ('LOW', 'Low Urgency'),
        ('MEDIUM', 'Medium Urgency'),
        ('HIGH', 'High Urgency'),
        ('CRITICAL', 'Critical Urgency'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Response'),
        ('ACCEPTED', 'Team Accepted'),
        ('ON_THE_WAY', 'Team On The Way'),
        ('ARRIVED', 'Team Arrived'),
        ('RESOLVED', 'Resolved'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incidents')
    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPES, default='EMERGENCY')
    description = models.TextField(blank=True)
    location_name = models.CharField(max_length=255, default="Main Campus Grounds")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    urgency = models.CharField(max_length=15, choices=URGENCY_LEVELS, default='CRITICAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    image = models.ImageField(upload_to='incidents/', null=True, blank=True)
    
    # Response team integration fields
    response_team_name = models.CharField(max_length=120, null=True, blank=True)
    responder_notes = models.TextField(null=True, blank=True)
    eta_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    is_sos = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_incident_type_display()}] by {self.user.username} - {self.get_status_display()} ({self.created_at.strftime('%b %d, %H:%M')})"

    def is_active(self):
        return self.status in ['PENDING', 'ACCEPTED', 'ON_THE_WAY', 'ARRIVED']

    def mark_resolved(self, responder_note="Resolved by student ('I'm Safe')"):
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        if not self.responder_notes:
            self.responder_notes = responder_note
        self.save()
        IncidentStatusLog.objects.create(
            incident=self,
            status='RESOLVED',
            note=responder_note,
            updated_by=self.user.get_full_name() or self.user.username
        )


class IncidentStatusLog(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(max_length=20, choices=Incident.STATUS_CHOICES)
    note = models.TextField(blank=True)
    updated_by = models.CharField(max_length=120, default="System")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Incident #{self.incident.id} -> {self.status} at {self.created_at.strftime('%H:%M:%S')}"
