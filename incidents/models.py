from django.db import models
from django.conf import settings
from teams.models import ResponseTeam

class Incident(models.Model):
    TYPE_CHOICES = [
        ('medical', 'Medical Emergency'),
        ('fire', 'Fire Outbreak'),
        ('security', 'Security Alert / Threat'),
        ('harassment', 'Harassment Report'),
        ('other', 'Other Incident'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending / Unassigned'),
        ('accepted', 'Accepted'),
        ('in-progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reported_incidents'
    )
    incident_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    description = models.TextField()
    location_lat = models.FloatField(help_text="Latitude coordinate")
    location_lng = models.FloatField(help_text="Longitude coordinate")
    address = models.CharField(max_length=255, help_text="Human readable landmark or building address")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_team = models.ForeignKey(
        ResponseTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.id}] {self.get_incident_type_display()} - {self.get_status_display()} ({self.address})"


class IncidentStatusLog(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='status_log'
    )
    status = models.CharField(max_length=30)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incident_updates'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Incident #{self.incident_id} -> {self.status} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
