from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

from .models import Incident, IncidentStatusLog
from teams.models import ResponseTeam
from .serializers import (
    IncidentCreateSerializer,
    IncidentListSerializer,
    IncidentDetailSerializer,
    IncidentStatusUpdateSerializer,
    IncidentAcceptSerializer,
    IncidentStatusLogSerializer
)
from .permissions import IsAdminRole, IsResponderRole, IsOwnerOrAdmin
from realtime.broadcasts import (
    broadcast_incident_created,
    broadcast_incident_status_updated
)

class IncidentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Incidents:
    - Person 1 (Users): POST /api/incidents/ to report emergency, GET to view reported incidents
    - Person 2 (Responders): GET /api/incidents/, PATCH /api/incidents/<id>/accept/, PATCH /api/incidents/<id>/status/
    - Person 3 (Admin): Full management and oversight
    """
    queryset = Incident.objects.all().select_related('reported_by', 'assigned_team')

    def get_serializer_class(self):
        if self.action == 'create':
            return IncidentCreateSerializer
        elif self.action == 'retrieve':
            return IncidentDetailSerializer
        elif self.action == 'accept':
            return IncidentAcceptSerializer
        elif self.action == 'update_status':
            return IncidentStatusUpdateSerializer
        return IncidentListSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['accept', 'update_status']:
            permission_classes = [IsResponderRole]
        elif self.action in ['destroy']:
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        qs = Incident.objects.all().select_related('reported_by', 'assigned_team')

        # Filter by role if standard user (students see their own, responders & admin see all)
        if user.is_authenticated and user.role == 'user':
            qs = qs.filter(reported_by=user)

        # Query Filters
        status_param = self.request.query_params.get('status')
        type_param = self.request.query_params.get('type') or self.request.query_params.get('incident_type')
        zone_param = self.request.query_params.get('zone')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        search = self.request.query_params.get('search')

        if status_param:
            qs = qs.filter(status=status_param)
        if type_param:
            qs = qs.filter(incident_type=type_param)
        if zone_param:
            qs = qs.filter(
                Q(assigned_team__zone__icontains=zone_param) |
                Q(address__icontains=zone_param)
            )
        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                qs = qs.filter(created_at__gte=dt_from)
            except Exception:
                pass
        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                qs = qs.filter(created_at__lte=dt_to)
            except Exception:
                pass
        if search:
            qs = qs.filter(
                Q(description__icontains=search) |
                Q(address__icontains=search) |
                Q(reported_by__username__icontains=search)
            )

        return qs

    def perform_create(self, serializer):
        incident = serializer.save()
        # Broadcast real-time event to Admin dashboard WebSocket
        detailed_data = IncidentDetailSerializer(incident).data
        broadcast_incident_created(detailed_data)

    @action(detail=True, methods=['patch', 'post'], url_path='accept')
    def accept(self, request, pk=None):
        """
        PATCH/POST /api/incidents/<id>/accept/
        Used by Person 2 (Responder) or Admin to accept an incident.
        """
        incident = self.get_object()
        serializer = IncidentAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get('notes', 'Accepted by response team.')
        team_id = serializer.validated_data.get('team_id')

        assigned_team = None
        if team_id:
            try:
                assigned_team = ResponseTeam.objects.get(id=team_id)
            except ResponseTeam.DoesNotExist:
                return Response({"detail": f"Team #{team_id} not found."}, status=status.HTTP_400_BAD_REQUEST)
        elif hasattr(request.user, 'response_team'):
            assigned_team = request.user.response_team
        
        if not assigned_team and not incident.assigned_team:
            # If admin is accepting without specifying team, try finding first matching zone team or leave unassigned
            pass

        if assigned_team:
            incident.assigned_team = assigned_team
            assigned_team.availability_status = 'busy'
            assigned_team.save()

        incident.status = 'accepted'
        incident.save()

        # Log status change
        IncidentStatusLog.objects.create(
            incident=incident,
            status='accepted',
            updated_by=request.user,
            notes=notes
        )

        # Broadcast live status update
        detailed_data = IncidentDetailSerializer(incident).data
        broadcast_incident_status_updated(detailed_data)

        return Response(detailed_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch', 'post'], url_path='status')
    def update_status(self, request, pk=None):
        """
        PATCH/POST /api/incidents/<id>/status/
        Used by Person 2 (Responder) or Admin to change status:
        ["pending", "accepted", "in-progress", "resolved", "rejected"]
        """
        incident = self.get_object()
        serializer = IncidentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', f"Status changed to {new_status}")

        old_status = incident.status
        incident.status = new_status

        # If resolving, calculate resolution time and update team statistics
        if new_status == 'resolved' and not incident.resolved_at:
            incident.resolved_at = timezone.now()
            duration_minutes = (incident.resolved_at - incident.created_at).total_seconds() / 60.0
            
            if incident.assigned_team:
                team = incident.assigned_team
                prev_cases = team.cases_handled
                team.cases_handled = prev_cases + 1
                # Exponential/cumulative running average
                if prev_cases == 0:
                    team.avg_response_time = round(duration_minutes, 1)
                else:
                    team.avg_response_time = round(
                        ((team.avg_response_time * prev_cases) + duration_minutes) / (prev_cases + 1),
                        1
                    )
                team.availability_status = 'on-duty'
                team.save()

        elif new_status == 'rejected':
            if incident.assigned_team:
                team = incident.assigned_team
                team.availability_status = 'on-duty'
                team.save()

        incident.save()

        # Log status entry
        IncidentStatusLog.objects.create(
            incident=incident,
            status=new_status,
            updated_by=request.user,
            notes=notes
        )

        # Broadcast live status update
        detailed_data = IncidentDetailSerializer(incident).data
        broadcast_incident_status_updated(detailed_data)

        return Response(detailed_data, status=status.HTTP_200_OK)
