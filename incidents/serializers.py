from rest_framework import serializers
from .models import Incident, IncidentStatusLog
from accounts.serializers import CustomUserSerializer
from teams.serializers import ResponseTeamSerializer
from teams.models import ResponseTeam

class IncidentStatusLogSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    updated_by_role = serializers.CharField(source='updated_by.role', read_only=True)

    class Meta:
        model = IncidentStatusLog
        fields = ['id', 'status', 'updated_by', 'updated_by_name', 'updated_by_role', 'timestamp', 'notes']
        read_only_fields = ['id', 'timestamp']


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            'id', 'incident_type', 'description', 'location_lat',
            'location_lng', 'address', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def create(self, validated_data):
        # Automatically assign reported_by from request.user
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['reported_by'] = request.user
        incident = super().create(validated_data)
        
        # Create initial status log
        IncidentStatusLog.objects.create(
            incident=incident,
            status='pending',
            updated_by=validated_data.get('reported_by'),
            notes='Incident reported by user.'
        )
        return incident


class IncidentListSerializer(serializers.ModelSerializer):
    reported_by_details = serializers.SerializerMethodField()
    assigned_team_details = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    incident_type_display = serializers.CharField(source='get_incident_type_display', read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'incident_type', 'incident_type_display', 'description',
            'location_lat', 'location_lng', 'address', 'status', 'status_display',
            'reported_by', 'reported_by_details', 'assigned_team', 'assigned_team_details',
            'created_at', 'resolved_at'
        ]

    def get_reported_by_details(self, obj):
        if obj.reported_by:
            return {
                'id': obj.reported_by.id,
                'username': obj.reported_by.username,
                'phone': obj.reported_by.phone,
                'name': f"{obj.reported_by.first_name} {obj.reported_by.last_name}".strip() or obj.reported_by.username
            }
        return None

    def get_assigned_team_details(self, obj):
        if obj.assigned_team:
            return {
                'id': obj.assigned_team.id,
                'name': obj.assigned_team.name,
                'zone': obj.assigned_team.zone,
                'availability_status': obj.assigned_team.availability_status
            }
        return None


class IncidentDetailSerializer(serializers.ModelSerializer):
    reported_by = CustomUserSerializer(read_only=True)
    assigned_team = ResponseTeamSerializer(read_only=True)
    status_log = IncidentStatusLogSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    incident_type_display = serializers.CharField(source='get_incident_type_display', read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'reported_by', 'incident_type', 'incident_type_display',
            'description', 'location_lat', 'location_lng', 'address',
            'status', 'status_display', 'assigned_team', 'status_log',
            'created_at', 'resolved_at'
        ]


class IncidentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Incident.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)


class IncidentAcceptSerializer(serializers.Serializer):
    team_id = serializers.IntegerField(required=False, help_text="Optional: specific team ID if accepted by admin or dispatch")
    notes = serializers.CharField(required=False, allow_blank=True, default="Accepted by response team.")
