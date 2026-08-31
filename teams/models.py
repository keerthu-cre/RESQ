from django.db import models
from django.conf import settings

class ResponseTeam(models.Model):
    AVAILABILITY_CHOICES = [
        ('on-duty', 'On Duty'),
        ('off-duty', 'Off Duty'),
        ('busy', 'Busy / Dispatched'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='response_team',
        limit_choices_to={'role': 'responder'}
    )
    name = models.CharField(max_length=100, help_text="Team or Unit Name, e.g. Alpha Rescue, Fire Unit 1")
    zone = models.CharField(max_length=100, help_text="Assigned campus sector/zone")
    incident_types = models.JSONField(
        default=list,
        help_text="List of handled incident types, e.g. ['medical', 'fire']"
    )
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='on-duty'
    )
    cases_handled = models.IntegerField(default=0)
    avg_response_time = models.FloatField(
        default=0.0,
        help_text="Average response time in minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-cases_handled', 'name']

    def __str__(self):
        return f"{self.name} ({self.zone}) - {self.get_availability_status_display()}"
