import csv
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.core.paginator import Paginator

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import CustomUser
from accounts.serializers import CustomUserSerializer
from teams.models import ResponseTeam
from teams.serializers import ResponseTeamSerializer
from incidents.models import Incident, IncidentStatusLog
from incidents.serializers import IncidentDetailSerializer
from incidents.permissions import IsAdminRole
from realtime.broadcasts import broadcast_incident_status_updated

from .forms import CustomUserCreationForm, CustomUserEditForm, ResponseTeamForm, IncidentActionForm


# ==========================================
# DRF Admin REST APIs
# ==========================================

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only DRF ViewSet for User Management:
    GET/POST/PUT/DELETE /api/admin/users/
    """
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        status_param = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        if role:
            qs = qs.filter(role=role)
        if status_param:
            qs = qs.filter(status=status_param)
        if search:
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return qs


class AdminTeamViewSet(viewsets.ModelViewSet):
    """
    Admin-only DRF ViewSet for Response Team Management:
    GET/POST/PUT/DELETE /api/admin/teams/
    """
    queryset = ResponseTeam.objects.all().select_related('user').order_by('-cases_handled')
    serializer_class = ResponseTeamSerializer
    permission_classes = [IsAdminRole]


class AdminAnalyticsAPIView(APIView):
    """
    GET /api/admin/analytics/
    Returns aggregated metrics:
    - total_incidents
    - incidents_by_type
    - avg_response_time
    - incidents_by_day (last 30 days)
    - top_zones_by_incident_count
    - team_leaderboard
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_incidents = Incident.objects.count()
        today_incidents = Incident.objects.filter(created_at__gte=today_start).count()
        pending_incidents = Incident.objects.filter(status='pending').count()
        active_teams_count = ResponseTeam.objects.filter(availability_status='on-duty').count()

        # Avg response time across all teams or resolved incidents
        avg_resp = ResponseTeam.objects.filter(cases_handled__gt=0).aggregate(Avg('avg_response_time'))['avg_response_time__avg'] or 0.0

        # Incidents by Type
        type_counts = Incident.objects.values('incident_type').annotate(count=Count('id')).order_by('-count')
        incidents_by_type = {item['incident_type']: item['count'] for item in type_counts}

        # Incidents by Status
        status_counts = Incident.objects.values('status').annotate(count=Count('id')).order_by('status')
        incidents_by_status = {item['status']: item['count'] for item in status_counts}

        # Incidents by Day (Last 30 days)
        incidents_by_day = []
        for i in range(29, -1, -1):
            day_date = (now - timedelta(days=i)).date()
            count = Incident.objects.filter(created_at__date=day_date).count()
            incidents_by_day.append({
                'date': day_date.strftime('%b %d'),
                'count': count
            })

        # Top Zones by Incident Count
        # Derive zone from assigned_team or address
        zones_counts = ResponseTeam.objects.values('zone').annotate(
            incident_count=Count('assigned_incidents')
        ).order_by('-incident_count')[:5]

        top_zones = [
            {'zone': z['zone'], 'count': z['incident_count']}
            for z in zones_counts
        ]

        # Team Leaderboard (sorted by cases handled & avg response time)
        teams = ResponseTeam.objects.select_related('user').order_by('-cases_handled', 'avg_response_time')[:10]
        team_leaderboard = [
            {
                'id': t.id,
                'name': t.name,
                'zone': t.zone,
                'availability_status': t.availability_status,
                'cases_handled': t.cases_handled,
                'avg_response_time': round(t.avg_response_time, 1)
            }
            for t in teams
        ]

        return Response({
            'total_incidents': total_incidents,
            'today_incidents': today_incidents,
            'pending_incidents': pending_incidents,
            'active_teams_count': active_teams_count,
            'avg_response_time': round(avg_resp, 1),
            'incidents_by_type': incidents_by_type,
            'incidents_by_status': incidents_by_status,
            'incidents_by_day': incidents_by_day,
            'top_zones_by_incident_count': top_zones,
            'team_leaderboard': team_leaderboard
        })


# ==========================================
# Server-Rendered Admin Views & Auth
# ==========================================

def admin_check(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser or user.is_staff)


def admin_login_view(request):
    if request.user.is_authenticated and admin_check(request.user):
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.status == 'blocked':
                messages.error(request, "This account is blocked. Access denied.")
            elif admin_check(user):
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Access restricted to Administrators only.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'adminpanel/login.html')


def admin_logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('admin_login')


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def dashboard_view(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_today = Incident.objects.filter(created_at__gte=today_start).count()
    pending_count = Incident.objects.filter(status='pending').count()
    active_teams = ResponseTeam.objects.filter(availability_status='on-duty').count()
    total_teams = ResponseTeam.objects.count()

    avg_resp = ResponseTeam.objects.filter(cases_handled__gt=0).aggregate(Avg('avg_response_time'))['avg_response_time__avg'] or 0.0

    # Recent incidents for the live feed
    recent_incidents = Incident.objects.select_related('reported_by', 'assigned_team')[:20]
    on_duty_teams = ResponseTeam.objects.select_related('user').filter(availability_status='on-duty')[:6]

    context = {
        'total_today': total_today,
        'pending_count': pending_count,
        'active_teams': active_teams,
        'total_teams': total_teams,
        'avg_response_time': round(avg_resp, 1),
        'recent_incidents': recent_incidents,
        'on_duty_teams': on_duty_teams,
    }
    return render(request, 'adminpanel/dashboard.html', context)


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def incidents_list_view(request):
    qs = Incident.objects.select_related('reported_by', 'assigned_team').all()

    # Filtering
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    zone_filter = request.GET.get('zone')
    search_query = request.GET.get('q')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(incident_type=type_filter)
    if zone_filter:
        qs = qs.filter(
            Q(assigned_team__zone__icontains=zone_filter) |
            Q(address__icontains=zone_filter)
        )
    if search_query:
        qs = qs.filter(
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(reported_by__username__icontains=search_query)
        )

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'incidents': page_obj,
        'status_filter': status_filter or '',
        'type_filter': type_filter or '',
        'zone_filter': zone_filter or '',
        'search_query': search_query or '',
        'total_count': qs.count(),
    }
    return render(request, 'adminpanel/incidents.html', context)


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def incident_detail_view(request, pk):
    incident = get_object_or_404(Incident.objects.select_related('reported_by', 'assigned_team'), pk=pk)
    teams = ResponseTeam.objects.all()

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        if action_type == 'reassign':
            team_id = request.POST.get('team_id')
            if team_id:
                team = get_object_or_404(ResponseTeam, pk=team_id)
                incident.assigned_team = team
                if incident.status == 'pending':
                    incident.status = 'accepted'
                incident.save()
                IncidentStatusLog.objects.create(
                    incident=incident,
                    status=incident.status,
                    updated_by=request.user,
                    notes=f"Admin assigned/reassigned to {team.name} ({team.zone})."
                )
                broadcast_incident_status_updated(IncidentDetailSerializer(incident).data)
                messages.success(request, f"Incident assigned to {team.name}.")

        elif action_type == 'update_status':
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', f"Status updated to {new_status} by Admin.")
            if new_status in dict(Incident.STATUS_CHOICES):
                incident.status = new_status
                if new_status == 'resolved' and not incident.resolved_at:
                    incident.resolved_at = timezone.now()
                    if incident.assigned_team:
                        incident.assigned_team.cases_handled += 1
                        incident.assigned_team.availability_status = 'on-duty'
                        incident.assigned_team.save()
                incident.save()
                IncidentStatusLog.objects.create(
                    incident=incident,
                    status=new_status,
                    updated_by=request.user,
                    notes=notes
                )
                broadcast_incident_status_updated(IncidentDetailSerializer(incident).data)
                messages.success(request, f"Incident status updated to {new_status.title()}.")

        return redirect('admin_incident_detail', pk=incident.pk)

    context = {
        'incident': incident,
        'status_logs': incident.status_log.all().order_by('-timestamp'),
        'teams': teams,
    }
    return render(request, 'adminpanel/incident_detail.html', context)


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def users_list_view(request):
    qs = CustomUser.objects.all().order_by('-date_joined')

    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q')

    if role_filter:
        qs = qs.filter(role=role_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search_query:
        qs = qs.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            messages.success(request, f"User {new_user.username} created successfully.")
            return redirect('admin_users')
        else:
            messages.error(request, "Please correct errors in user creation form.")

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'users': page_obj,
        'form': form,
        'role_filter': role_filter or '',
        'status_filter': status_filter or '',
        'search_query': search_query or '',
        'total_count': qs.count(),
    }
    return render(request, 'adminpanel/users.html', context)


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def user_detail_view(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    user_incidents = Incident.objects.filter(reported_by=user_obj).order_by('-created_at')

    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user_obj.username} updated.")
            return redirect('admin_user_detail', pk=user_obj.pk)
    else:
        form = CustomUserEditForm(instance=user_obj)

    context = {
        'user_obj': user_obj,
        'user_incidents': user_incidents,
        'form': form,
    }
    return render(request, 'adminpanel/user_detail.html', context)


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def user_toggle_status_view(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    if user_obj == request.user:
        messages.error(request, "You cannot deactivate your own admin account.")
    else:
        user_obj.status = 'blocked' if user_obj.status == 'active' else 'active'
        user_obj.save()
        messages.success(request, f"User {user_obj.username} status set to {user_obj.get_status_display()}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_users'))


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def teams_list_view(request):
    teams = ResponseTeam.objects.select_related('user').all()
    form = ResponseTeamForm()

    if request.method == 'POST':
        form = ResponseTeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            messages.success(request, f"Response Team {team.name} created successfully.")
            return redirect('admin_teams')
        else:
            messages.error(request, "Error creating response team. Please check the fields.")

    context = {
        'teams': teams,
        'form': form,
    }
    return render(request, 'adminpanel/teams.html', context)


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def team_detail_view(request, pk):
    team = get_object_or_404(ResponseTeam.objects.select_related('user'), pk=pk)
    assigned_incidents = Incident.objects.filter(assigned_team=team).order_by('-created_at')

    if request.method == 'POST':
        form = ResponseTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f"Response Team {team.name} updated.")
            return redirect('admin_team_detail', pk=team.pk)
    else:
        form = ResponseTeamForm(instance=team)

    context = {
        'team': team,
        'assigned_incidents': assigned_incidents,
        'form': form,
    }
    return render(request, 'adminpanel/team_detail.html', context)


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def analytics_page_view(request):
    return render(request, 'adminpanel/analytics.html')


@login_required
@user_passes_test(admin_check, login_url='/admin-dashboard/login/')
def export_incidents_csv(request):
    """
    Exports all incidents to a CSV file download.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="resq_incidents_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Incident ID', 'Type', 'Status', 'Description', 'Address',
        'Latitude', 'Longitude', 'Reported By (Username)', 'Reported By (Phone)',
        'Assigned Team', 'Team Zone', 'Created At', 'Resolved At'
    ])

    incidents = Incident.objects.select_related('reported_by', 'assigned_team').all().order_by('-created_at')
    for inc in incidents:
        writer.writerow([
            inc.id,
            inc.get_incident_type_display(),
            inc.get_status_display(),
            inc.description,
            inc.address,
            inc.location_lat,
            inc.location_lng,
            inc.reported_by.username if inc.reported_by else '',
            inc.reported_by.phone if inc.reported_by else '',
            inc.assigned_team.name if inc.assigned_team else 'Unassigned',
            inc.assigned_team.zone if inc.assigned_team else 'N/A',
            inc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            inc.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if inc.resolved_at else 'N/A'
        ])

    return response
