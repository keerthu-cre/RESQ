from django.contrib import admin
from .models import ResponseTeam

@admin.register(ResponseTeam)
class ResponseTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'zone', 'availability_status', 'cases_handled', 'avg_response_time')
    list_filter = ('availability_status', 'zone')
    search_fields = ('name', 'user__username', 'zone')
