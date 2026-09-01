from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User / Student'),
        ('responder', 'Response Team Member'),
        ('admin', 'Administrator'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def is_admin_role(self):
        return self.role == 'admin' or self.is_superuser

    def is_responder_role(self):
        return self.role == 'responder'

    def is_user_role(self):
        return self.role == 'user'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
