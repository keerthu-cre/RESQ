from django.contrib import admin
from .models import Incident, IncidentStatusLog

class IncidentStatusLogInline(admin.TabularInline):
    model = IncidentStatusLog
    extra = 0
    readonly_fields = ('status', 'updated_by', 'timestamp', 'notes')

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident_type', 'status', 'reported_by', 'assigned_team', 'address', 'created_at')
    list_filter = ('status', 'incident_type', 'created_at')
    search_fields = ('description', 'address', 'reported_by__username')
    inlines = [IncidentStatusLogInline]

@admin.register(IncidentStatusLog)
class IncidentStatusLogAdmin(admin.ModelAdmin):
    list_display = ('incident', 'status', 'updated_by', 'timestamp')
    list_filter = ('status', 'timestamp')
