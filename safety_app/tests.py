import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from safety_app.models import UserProfile, EmergencyContact, Incident, IncidentStatusLog


class SafeCampusTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            email='test@university.edu',
            password='testpassword123',
            first_name='Jordan',
            last_name='Taylor'
        )
        self.profile = self.user.profile
        self.profile.student_id = 'SC-99881'
        self.profile.phone_number = '+1 (555) 777-8899'
        self.profile.save()

    def test_user_profile_creation_signal(self):
        """Verify UserProfile is automatically created on User creation signal."""
        self.assertIsNotNone(self.user.profile)
        self.assertEqual(self.user.profile.student_id, 'SC-99881')

    def test_login_and_dashboard_access(self):
        """Verify login flow and dashboard rendering."""
        login_success = self.client.login(username='teststudent', password='testpassword123')
        self.assertTrue(login_success)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jordan')
        self.assertContains(response, 'SC-99881')

    def test_sos_trigger_ajax(self):
        """Verify 2-second SOS trigger creates critical incident automatically."""
        self.client.login(username='teststudent', password='testpassword123')
        payload = {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'location_name': 'Science Center 2F'
        }
        response = self.client.post(
            reverse('sos_trigger'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'PENDING')

        # Verify in DB
        incident = Incident.objects.get(id=data['incident_id'])
        self.assertEqual(incident.user, self.user)
        self.assertEqual(incident.incident_type, 'EMERGENCY')
        self.assertEqual(incident.urgency, 'CRITICAL')
        self.assertEqual(incident.status, 'PENDING')
        self.assertTrue(incident.is_sos)
        self.assertEqual(incident.location_name, 'Science Center 2F')
        self.assertAlmostEqual(incident.latitude, 37.7749)

    def test_incident_reporting_view(self):
        """Verify manual incident reporting form submission."""
        self.client.login(username='teststudent', password='testpassword123')
        post_data = {
            'incident_type': 'FIRE',
            'urgency': 'HIGH',
            'location_name': 'West Dorm Kitchen',
            'description': 'Small electrical fire near the stove.',
            'latitude': 37.7741,
            'longitude': -122.4205,
        }
        response = self.client.post(reverse('incident_report'), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify incident in DB
        incident = Incident.objects.filter(user=self.user, incident_type='FIRE').first()
        self.assertIsNotNone(incident)
        self.assertEqual(incident.urgency, 'HIGH')
        self.assertEqual(incident.status, 'PENDING')

    def test_im_safe_resolution_flow(self):
        """Verify student marking I'M SAFE updates status to RESOLVED."""
        self.client.login(username='teststudent', password='testpassword123')
        incident = Incident.objects.create(
            user=self.user,
            incident_type='EMERGENCY',
            urgency='CRITICAL',
            status='ON_THE_WAY',
            location_name='Library Quad'
        )
        response = self.client.post(
            reverse('resolve_safe', kwargs={'pk': incident.id}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.status, 'RESOLVED')
        self.assertIsNotNone(incident.resolved_at)

    def test_response_simulation_api(self):
        """Verify response team simulation milestones for demo flow."""
        self.client.login(username='teststudent', password='testpassword123')
        incident = Incident.objects.create(
            user=self.user,
            incident_type='EMERGENCY',
            status='PENDING'
        )
        # Step 1: ACCEPTED
        res = self.client.post(
            reverse('simulate_response', kwargs={'pk': incident.id}),
            data=json.dumps({'target_status': 'ACCEPTED'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.status, 'ACCEPTED')
        self.assertEqual(incident.eta_minutes, 6)

        # Step 2: ON_THE_WAY
        res = self.client.post(
            reverse('simulate_response', kwargs={'pk': incident.id}),
            data=json.dumps({'target_status': 'ON_THE_WAY'}),
            content_type='application/json'
        )
        incident.refresh_from_db()
        self.assertEqual(incident.status, 'ON_THE_WAY')
        self.assertEqual(incident.eta_minutes, 3)

        # Step 3: ARRIVED
        res = self.client.post(
            reverse('simulate_response', kwargs={'pk': incident.id}),
            data=json.dumps({'target_status': 'ARRIVED'}),
            content_type='application/json'
        )
        incident.refresh_from_db()
        self.assertEqual(incident.status, 'ARRIVED')

    def test_emergency_contact_crud(self):
        """Verify adding and deleting personal emergency contacts."""
        self.client.login(username='teststudent', password='testpassword123')
        
        # Add Contact
        res = self.client.post(reverse('add_contact'), data={
            'name': 'Mom',
            'relationship': 'Parent',
            'phone_number': '+1 (555) 111-2222',
            'is_primary': True
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        contact = EmergencyContact.objects.filter(user=self.user, name='Mom').first()
        self.assertIsNotNone(contact)
        self.assertTrue(contact.is_primary)

        # Delete Contact
        res_del = self.client.post(reverse('delete_contact', kwargs={'pk': contact.id}), follow=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(EmergencyContact.objects.filter(id=contact.id).exists())

    def test_accessibility_update_api(self):
        """Verify saving accessibility preferences."""
        self.client.login(username='teststudent', password='testpassword123')
        payload = {
            'dark_mode': True,
            'high_contrast': True,
            'large_text': True,
            'reduce_motion': False,
            'voice_assist': True
        }
        res = self.client.post(
            reverse('update_accessibility'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.dark_mode)
        self.assertTrue(self.user.profile.high_contrast)
        self.assertTrue(self.user.profile.large_text)
        self.assertTrue(self.user.profile.voice_assist)
