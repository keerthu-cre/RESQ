from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ResponseTeam
from .serializers import ResponseTeamSerializer, ResponseTeamStatusUpdateSerializer
from incidents.permissions import IsAdminRole, IsResponderRole

class ResponseTeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing response teams.
    - Responders can view teams and update their own availability.
    - Admins can manage all teams.
    """
    queryset = ResponseTeam.objects.all().select_related('user')
    serializer_class = ResponseTeamSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_team', 'update_duty_status']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminRole]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        qs = super().get_queryset()
        zone = self.request.query_params.get('zone')
        status_param = self.request.query_params.get('availability_status')
        if zone:
            qs = qs.filter(zone__icontains=zone)
        if status_param:
            qs = qs.filter(availability_status=status_param)
        return qs

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_team(self, request):
        """Returns the logged-in responder's assigned team."""
        try:
            team = request.user.response_team
            serializer = self.get_serializer(team)
            return Response(serializer.data)
        except ResponseTeam.DoesNotExist:
            return Response(
                {"detail": "No response team profile linked to this user."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch', 'post'], permission_classes=[permissions.IsAuthenticated])
    def update_duty_status(self, request):
        """Allows responder to toggle on-duty / off-duty / busy."""
        try:
            team = request.user.response_team
        except ResponseTeam.DoesNotExist:
            return Response(
                {"detail": "No response team profile linked to this user."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ResponseTeamStatusUpdateSerializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ResponseTeamSerializer(team).data)
