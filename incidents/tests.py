from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import CustomUser
from teams.models import ResponseTeam
from incidents.models import Incident

class IncidentWorkflowTests(APITestCase):
    def setUp(self):
        # Student (Person 1)
        self.student = CustomUser.objects.create_user(
            username='student_alice',
            password='password123',
            role='user'
        )
        
        # Responder (Person 2)
        self.responder_user = CustomUser.objects.create_user(
            username='responder_bob',
            password='password123',
            role='responder'
        )
        self.team = ResponseTeam.objects.create(
            user=self.responder_user,
            name='Rescue Unit 1',
            zone='North Sector',
            incident_types=['medical', 'security'],
            availability_status='on-duty'
        )

        # Admin (Person 3)
        self.admin = CustomUser.objects.create_superuser(
            username='admin_boss',
            password='adminpassword',
            role='admin'
        )

    def test_person1_create_incident(self):
        self.client.force_authenticate(user=self.student)
        url = '/api/incidents/'
        data = {
            'incident_type': 'medical',
            'description': 'Student collapsed in library.',
            'location_lat': 12.9716,
            'location_lng': 77.5946,
            'address': 'Main Library, 2nd Floor'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(Incident.objects.count(), 1)
        incident = Incident.objects.first()
        self.assertEqual(incident.reported_by, self.student)
        self.assertEqual(incident.status_log.count(), 1)

    def test_person2_accept_and_resolve_incident(self):
        # Create incident
        incident = Incident.objects.create(
            reported_by=self.student,
            incident_type='medical',
            description='Injury on sports field',
            location_lat=12.9716,
            location_lng=77.5946,
            address='Sports Complex',
            status='pending'
        )

        # Person 2 accepts incident
        self.client.force_authenticate(user=self.responder_user)
        accept_url = f'/api/incidents/{incident.id}/accept/'
        response = self.client.patch(accept_url, {'notes': 'Dispatched ambulance'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        incident.refresh_from_db()
        self.assertEqual(incident.status, 'accepted')
        self.assertEqual(incident.assigned_team, self.team)
        
        self.team.refresh_from_db()
        self.assertEqual(self.team.availability_status, 'busy')

        # Person 2 resolves incident
        status_url = f'/api/incidents/{incident.id}/status/'
        response = self.client.patch(status_url, {'status': 'resolved', 'notes': 'First aid provided'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        incident.refresh_from_db()
        self.assertEqual(incident.status, 'resolved')
        self.assertIsNotNone(incident.resolved_at)

        self.team.refresh_from_db()
        self.assertEqual(self.team.cases_handled, 1)
        self.assertEqual(self.team.availability_status, 'on-duty')

    def test_admin_analytics_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        url = '/api/admin/analytics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_incidents', response.data)
        self.assertIn('incidents_by_type', response.data)
        self.assertIn('team_leaderboard', response.data)
