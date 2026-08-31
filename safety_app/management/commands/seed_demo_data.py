from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from safety_app.models import UserProfile, EmergencyContact, Incident, IncidentStatusLog
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seeds the database with initial demo student account, default campus hotlines, and sample incidents.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding demo data for SafeCampus..."))

        # 1. Create Superuser / Admin if not exists
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@safecampus.edu', 'admin123')
            admin_user.first_name = "Campus"
            admin_user.last_name = "Admin"
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Superuser created: admin / admin123"))
        else:
            self.stdout.write(self.style.WARNING("Superuser 'admin' already exists."))

        # 2. Create Demo Student User
        student, created = User.objects.get_or_create(
            username='alex.student',
            defaults={
                'email': 'alex.morris@university.edu',
                'first_name': 'Alex',
                'last_name': 'Morris',
            }
        )
        if created:
            student.set_password('safecampus123')
            student.save()
            self.stdout.write(self.style.SUCCESS("[OK] Demo Student created: alex.student / safecampus123"))
        else:
            student.set_password('safecampus123')
            student.save()
            self.stdout.write(self.style.WARNING("Demo Student 'alex.student' updated."))

        # Update Profile
        profile, _ = UserProfile.objects.get_or_create(user=student)
        profile.student_id = "SC-84920"
        profile.phone_number = "+1 (555) 392-8172"
        profile.dormitory_block = "West Hall, 3rd Floor, Room 314"
        profile.blood_group = "O+"
        profile.medical_allergies = "Mild Asthma (Carries Albuterol inhaler in backpack), Penicillin allergy"
        profile.emergency_notes = "Contact roommate Elena or mother Sarah in critical situations."
        profile.save()

        # 3. Create Default Campus Hotlines
        EmergencyContact.objects.filter(is_campus_service=True).delete()
        
        campus_services = [
            {
                'name': 'Campus Police & Security Dispatch',
                'relationship': '24/7 Campus Emergency Police',
                'phone_number': '911',
                'is_primary': True,
                'is_campus_service': True,
            },
            {
                'name': 'University Health & Medical Center',
                'relationship': 'On-Campus Urgent Medical Care',
                'phone_number': '+1-800-555-SAFE',
                'is_primary': False,
                'is_campus_service': True,
            },
            {
                'name': 'Crisis & Mental Health Helpline',
                'relationship': 'Confidential 24/7 Support Hotline',
                'phone_number': '+1-800-273-TALK',
                'is_primary': False,
                'is_campus_service': True,
            },
            {
                'name': 'Campus Night Escort & SafeRide',
                'relationship': 'Campus Transit & Walking Escort',
                'phone_number': '+1 (555) 723-3743',
                'is_primary': False,
                'is_campus_service': True,
            },
        ]
        
        for cs in campus_services:
            EmergencyContact.objects.create(user=None, **cs)
        self.stdout.write(self.style.SUCCESS("[OK] Campus 24/7 hotlines seeded."))

        # 4. Create Personal Emergency Contacts for alex.student
        EmergencyContact.objects.filter(user=student).delete()
        personal_contacts = [
            {
                'name': 'Sarah Morris',
                'relationship': 'Mother / Primary ICE',
                'phone_number': '+1 (555) 912-3849',
                'is_primary': True,
            },
            {
                'name': 'Elena Rostova',
                'relationship': 'Dorm Roommate (West 314)',
                'phone_number': '+1 (555) 642-1980',
                'is_primary': False,
            },
            {
                'name': 'David Chen',
                'relationship': 'Study Partner & Friend',
                'phone_number': '+1 (555) 831-4720',
                'is_primary': False,
            },
        ]
        for pc in personal_contacts:
            EmergencyContact.objects.create(user=student, is_campus_service=False, **pc)
        self.stdout.write(self.style.SUCCESS("[OK] Personal emergency contacts for Alex seeded."))

        # 5. Create Sample Past Incidents (Resolved) for history showcase
        Incident.objects.filter(user=student).delete()
        
        # Past Incident 1 (Resolved)
        past_inc_1 = Incident.objects.create(
            user=student,
            incident_type='INFRASTRUCTURE',
            urgency='MEDIUM',
            status='RESOLVED',
            is_sos=False,
            location_name='Library North Wing, 2nd Floor Stairwell',
            latitude=37.7749,
            longitude=-122.4194,
            description='Water leak on the stairwell causing very slippery marble floor. Risk of fall for students.',
            response_team_name='Campus Facilities & Safety Team',
            responder_notes='Hazard cones placed, floor dried, and pipe fixture repaired.',
            resolved_at=timezone.now() - timedelta(days=2)
        )
        IncidentStatusLog.objects.create(
            incident=past_inc_1,
            status='PENDING',
            note='Report submitted by student.',
            updated_by='Alex Morris',
            created_at=timezone.now() - timedelta(days=2, hours=3)
        )
        IncidentStatusLog.objects.create(
            incident=past_inc_1,
            status='ACCEPTED',
            note='Facilities Team Bravo dispatched.',
            updated_by='Campus Facilities',
            created_at=timezone.now() - timedelta(days=2, hours=2, minutes=50)
        )
        IncidentStatusLog.objects.create(
            incident=past_inc_1,
            status='RESOLVED',
            note='Repaired and verified clean by Team Bravo.',
            updated_by='Officer Daniels',
            created_at=timezone.now() - timedelta(days=2)
        )

        # Past Incident 2 (Resolved SOS)
        past_inc_2 = Incident.objects.create(
            user=student,
            incident_type='MEDICAL',
            urgency='HIGH',
            status='RESOLVED',
            is_sos=False,
            location_name='Athletic Center Gymnasium - Court 3',
            latitude=37.7758,
            longitude=-122.4180,
            description='Sprained ankle and severe swelling during basketball practice.',
            response_team_name='Sports EMT Unit',
            responder_notes='Ice compression applied, student escorted to Campus Health Clinic.',
            resolved_at=timezone.now() - timedelta(days=6)
        )
        IncidentStatusLog.objects.create(
            incident=past_inc_2,
            status='RESOLVED',
            note='Treated at Health Clinic.',
            updated_by='Sports EMT Unit',
            created_at=timezone.now() - timedelta(days=6)
        )

        self.stdout.write(self.style.SUCCESS("[OK] Sample historical incidents created."))
        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Database seeded successfully!"))
        self.stdout.write(self.style.NOTICE("Test Account: alex.student / safecampus123"))
        self.stdout.write(self.style.NOTICE("Admin Account: admin / admin123"))

