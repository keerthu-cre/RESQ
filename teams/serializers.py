from rest_framework import serializers
from .models import ResponseTeam
from accounts.models import CustomUser
from accounts.serializers import CustomUserSerializer

class ResponseTeamSerializer(serializers.ModelSerializer):
    user_details = CustomUserSerializer(source='user', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='responder'),
        source='user',
        write_only=True,
        required=False
    )

    class Meta:
        model = ResponseTeam
        fields = [
            'id', 'user', 'user_id', 'user_details', 'name', 'zone',
            'incident_types', 'availability_status', 'cases_handled',
            'avg_response_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ResponseTeamStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseTeam
        fields = ['availability_status']
