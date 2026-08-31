from django.contrib import admin
from .models import UserProfile, EmergencyContact, Incident, IncidentStatusLog


class IncidentStatusLogInline(admin.TabularInline):
    model = IncidentStatusLog
    extra = 0
    readonly_fields = ('status', 'note', 'updated_by', 'created_at')
    can_delete = False


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident_type', 'user', 'urgency', 'status', 'location_name', 'created_at', 'is_sos')
    list_filter = ('status', 'incident_type', 'urgency', 'is_sos', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'location_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [IncidentStatusLogInline]
    actions = ['mark_as_accepted', 'mark_as_on_the_way', 'mark_as_arrived', 'mark_as_resolved']

    def mark_as_accepted(self, request, queryset):
        for inc in queryset:
            inc.status = 'ACCEPTED'
            inc.save()
            IncidentStatusLog.objects.create(incident=inc, status='ACCEPTED', note='Accepted via Admin Panel', updated_by=request.user.username)
    mark_as_accepted.short_description = "Mark selected as Team Accepted"

    def mark_as_on_the_way(self, request, queryset):
        for inc in queryset:
            inc.status = 'ON_THE_WAY'
            inc.save()
            IncidentStatusLog.objects.create(incident=inc, status='ON_THE_WAY', note='En route via Admin Panel', updated_by=request.user.username)
    mark_as_on_the_way.short_description = "Mark selected as Team On The Way"

    def mark_as_arrived(self, request, queryset):
        for inc in queryset:
            inc.status = 'ARRIVED'
            inc.save()
            IncidentStatusLog.objects.create(incident=inc, status='ARRIVED', note='Arrived on scene via Admin Panel', updated_by=request.user.username)
    mark_as_arrived.short_description = "Mark selected as Team Arrived"

    def mark_as_resolved(self, request, queryset):
        for inc in queryset:
            inc.mark_resolved(responder_note="Resolved via Admin Panel")
    mark_as_resolved.short_description = "Mark selected as Resolved"


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'relationship', 'phone_number', 'user', 'is_primary', 'is_campus_service')
    list_filter = ('is_campus_service', 'is_primary')
    search_fields = ('name', 'phone_number', 'relationship')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'phone_number', 'dormitory_block', 'blood_group')
    search_fields = ('user__username', 'student_id', 'phone_number')


@admin.register(IncidentStatusLog)
class IncidentStatusLogAdmin(admin.ModelAdmin):
    list_display = ('incident', 'status', 'updated_by', 'created_at')
    list_filter = ('status', 'created_at')
