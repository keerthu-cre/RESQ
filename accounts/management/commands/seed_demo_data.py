import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser
from teams.models import ResponseTeam
from incidents.models import Incident, IncidentStatusLog

class Command(BaseCommand):
    help = 'Seeds database with realistic demo accounts, response teams, and 20+ incidents.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Flushing and seeding RESQ demo database..."))

        # Clean existing demo records
        IncidentStatusLog.objects.all().delete()
        Incident.objects.all().delete()
        ResponseTeam.objects.all().delete()
        CustomUser.objects.all().delete()

        # 1. Admin Account
        admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@resq.edu',
            password='admin123',
            first_name='Campus',
            last_name='Security Admin',
            role='admin',
            phone='+1-555-0100',
            status='active'
        )
        self.stdout.write(self.style.SUCCESS(f"Created Admin: {admin_user.username} (admin123)"))

        # 2. Responders & Teams
        responders_data = [
            {
                'username': 'responder_alpha',
                'first_name': 'Marcus',
                'last_name': 'Vance',
                'phone': '+1-555-0201',
                'team_name': 'Alpha Tactical Patrol',
                'zone': 'North Academic Complex',
                'types': ['security', 'harassment'],
                'status': 'on-duty',
                'cases': 12,
                'avg_time': 4.1
            },
            {
                'username': 'responder_medic',
                'first_name': 'Dr. Sarah',
                'last_name': 'Jenkins',
                'phone': '+1-555-0202',
                'team_name': 'Campus EMS Unit 1',
                'zone': 'Hostel & Residential Block',
                'types': ['medical'],
                'status': 'busy',
                'cases': 18,
                'avg_time': 3.2
            },
            {
                'username': 'responder_fire',
                'first_name': 'Chief Robert',
                'last_name': 'Torres',
                'phone': '+1-555-0203',
                'team_name': 'Fire & Hazmat Squad',
                'zone': 'Science & Labs Complex',
                'types': ['fire', 'other'],
                'status': 'on-duty',
                'cases': 6,
                'avg_time': 5.4
            },
            {
                'username': 'responder_night',
                'first_name': 'Elena',
                'last_name': 'Reyes',
                'phone': '+1-555-0204',
                'team_name': 'Night Safety Escort',
                'zone': 'Library & Student Union',
                'types': ['security', 'harassment', 'other'],
                'status': 'on-duty',
                'cases': 15,
                'avg_time': 3.9
            },
            {
                'username': 'responder_delta',
                'first_name': 'David',
                'last_name': 'Kim',
                'phone': '+1-555-0205',
                'team_name': 'Delta Multi-Hazard Unit',
                'zone': 'Sports Arena & South Gate',
                'types': ['medical', 'security', 'fire', 'other'],
                'status': 'off-duty',
                'cases': 9,
                'avg_time': 6.2
            },
        ]

        created_teams = []
        for r_info in responders_data:
            user = CustomUser.objects.create_user(
                username=r_info['username'],
                email=f"{r_info['username']}@resq.edu",
                password='password123',
                first_name=r_info['first_name'],
                last_name=r_info['last_name'],
                role='responder',
                phone=r_info['phone'],
                status='active'
            )
            team = ResponseTeam.objects.create(
                user=user,
                name=r_info['team_name'],
                zone=r_info['zone'],
                incident_types=r_info['types'],
                availability_status=r_info['status'],
                cases_handled=r_info['cases'],
                avg_response_time=r_info['avg_time']
            )
            created_teams.append(team)
            self.stdout.write(self.style.SUCCESS(f"Created Responder Team: {team.name} ({user.username})"))

        # 3. 15 Student / Campus Users
        students = []
        student_names = [
            ('alex_rivera', 'Alex', 'Rivera', '+1-555-0301'),
            ('priya_sharma', 'Priya', 'Sharma', '+1-555-0302'),
            ('jordan_lee', 'Jordan', 'Lee', '+1-555-0303'),
            ('taylor_swift', 'Taylor', 'Smith', '+1-555-0304'),
            ('mohammed_ali', 'Mohammed', 'Ali', '+1-555-0305'),
            ('emily_clark', 'Emily', 'Clark', '+1-555-0306'),
            ('lucas_silva', 'Lucas', 'Silva', '+1-555-0307'),
            ('zoe_dupont', 'Zoe', 'Dupont', '+1-555-0308'),
            ('ethan_hunt', 'Ethan', 'Wright', '+1-555-0309'),
            ('chloe_bennett', 'Chloe', 'Bennett', '+1-555-0310'),
            ('sam_wilson', 'Sam', 'Wilson', '+1-555-0311'),
            ('maya_patel', 'Maya', 'Patel', '+1-555-0312'),
            ('daniel_craig', 'Daniel', 'Craig', '+1-555-0313'),
            ('olivia_wilde', 'Olivia', 'Wilde', '+1-555-0314'),
            ('noah_cent', 'Noah', 'Cent', '+1-555-0315'),
        ]

        for uname, fname, lname, phone in student_names:
            s_user = CustomUser.objects.create_user(
                username=uname,
                email=f"{uname}@campus.edu",
                password='password123',
                first_name=fname,
                last_name=lname,
                role='user',
                phone=phone,
                status='active'
            )
            students.append(s_user)

        self.stdout.write(self.style.SUCCESS(f"Created {len(students)} Student Accounts (password: password123)"))

        # 4. Realistic Incident Seed List (22 Incidents across past 14 days)
        incidents_seed = [
            # Recent & Pending (today)
            {
                'days_ago': 0,
                'hours_ago': 0.2,
                'type': 'medical',
                'desc': 'Student passed out during lecture in Auditorium 3B, shallow breathing.',
                'address': 'Auditorium 3B, North Academic Complex',
                'lat': 12.9716, 'lng': 77.5946,
                'status': 'pending',
                'team': None,
            },
            {
                'days_ago': 0,
                'hours_ago': 0.8,
                'type': 'security',
                'desc': 'Unauthorized person loitering near female dormitories after curfew.',
                'address': 'Dormitory Block C Entrance, Hostel Zone',
                'lat': 12.9720, 'lng': 77.5950,
                'status': 'pending',
                'team': None,
            },
            {
                'days_ago': 0,
                'hours_ago': 1.5,
                'type': 'fire',
                'desc': 'Electrical spark and burning smell detected in Chemistry Lab 204.',
                'address': 'Chemistry Dept Room 204, Science Complex',
                'lat': 12.9735, 'lng': 77.5960,
                'status': 'in-progress',
                'team': created_teams[2], # Fire squad
            },
            {
                'days_ago': 0,
                'hours_ago': 2.0,
                'type': 'medical',
                'desc': 'Sprained ankle with severe swelling on the main basketball court.',
                'address': 'Outdoor Basketball Courts, Sports Arena',
                'lat': 12.9705, 'lng': 77.5930,
                'status': 'accepted',
                'team': created_teams[1], # EMS
            },
            {
                'days_ago': 1,
                'hours_ago': 6,
                'type': 'harassment',
                'desc': 'Verbal harassment and stalking report near the dark pathway behind the Library.',
                'address': 'Pine Walkway behind Central Library',
                'lat': 12.9725, 'lng': 77.5955,
                'status': 'resolved',
                'team': created_teams[3], # Night safety
                'duration': 18
            },
            {
                'days_ago': 1,
                'hours_ago': 14,
                'type': 'medical',
                'desc': 'Severe allergic reaction to cafeteria food, student having trouble breathing.',
                'address': 'Central Cafeteria Main Hall',
                'lat': 12.9718, 'lng': 77.5948,
                'status': 'resolved',
                'team': created_teams[1], # EMS
                'duration': 8
            },
            {
                'days_ago': 2,
                'hours_ago': 4,
                'type': 'security',
                'desc': 'Bicycle theft witnessed in front of Engineering Hall B.',
                'address': 'Engineering Hall B Bicycle Stands',
                'lat': 12.9730, 'lng': 77.5962,
                'status': 'resolved',
                'team': created_teams[0], # Alpha patrol
                'duration': 22
            },
            {
                'days_ago': 2,
                'hours_ago': 18,
                'type': 'other',
                'desc': 'Main water line burst causing flooding on ground floor hallway.',
                'address': 'Civil Engineering Wing, Ground Floor',
                'lat': 12.9732, 'lng': 77.5958,
                'status': 'resolved',
                'team': created_teams[2],
                'duration': 35
            },
            {
                'days_ago': 3,
                'hours_ago': 8,
                'type': 'fire',
                'desc': 'Trash bin ignited near cafeteria dumpster area.',
                'address': 'Rear Loading Dock, Central Cafeteria',
                'lat': 12.9719, 'lng': 77.5947,
                'status': 'resolved',
                'team': created_teams[2],
                'duration': 12
            },
            {
                'days_ago': 4,
                'hours_ago': 10,
                'type': 'medical',
                'desc': 'Student fainted due to heat exhaustion during athletics practice.',
                'address': 'Main Sports Track, South Gate',
                'lat': 12.9702, 'lng': 77.5928,
                'status': 'resolved',
                'team': created_teams[4], # Delta
                'duration': 14
            },
            {
                'days_ago': 5,
                'hours_ago': 2,
                'type': 'harassment',
                'desc': 'Hostile confrontation in library study room 4.',
                'address': 'Central Library 2nd Floor, Room 4',
                'lat': 12.9726, 'lng': 77.5954,
                'status': 'resolved',
                'team': created_teams[3],
                'duration': 9
            },
            {
                'days_ago': 6,
                'hours_ago': 16,
                'type': 'security',
                'desc': 'Suspicious backpack left unattended in student union lounge.',
                'address': 'Student Union Lobby',
                'lat': 12.9722, 'lng': 77.5951,
                'status': 'resolved',
                'team': created_teams[0],
                'duration': 15
            },
            {
                'days_ago': 7,
                'hours_ago': 5,
                'type': 'medical',
                'desc': 'Deep laceration from broken glassware in Biology lab.',
                'address': 'Bio-Tech Lab 102, Science Complex',
                'lat': 12.9734, 'lng': 77.5961,
                'status': 'resolved',
                'team': created_teams[1],
                'duration': 11
            },
            {
                'days_ago': 8,
                'hours_ago': 12,
                'type': 'security',
                'desc': 'Trespasser spotted scaling perimeter fence near South Gate.',
                'address': 'Perimeter Fence Section 4, South Gate',
                'lat': 12.9701, 'lng': 77.5925,
                'status': 'resolved',
                'team': created_teams[0],
                'duration': 25
            },
            {
                'days_ago': 9,
                'hours_ago': 9,
                'type': 'other',
                'desc': 'Power outage and trapped students in Elevator #2, Admin Tower.',
                'address': 'Administration Tower, Floor 4',
                'lat': 12.9724, 'lng': 77.5952,
                'status': 'resolved',
                'team': created_teams[4],
                'duration': 28
            },
            {
                'days_ago': 10,
                'hours_ago': 15,
                'type': 'medical',
                'desc': 'Asthma attack in hostel room 312.',
                'address': 'Boys Hostel 2, Room 312',
                'lat': 12.9721, 'lng': 77.5949,
                'status': 'resolved',
                'team': created_teams[1],
                'duration': 7
            },
            {
                'days_ago': 11,
                'hours_ago': 20,
                'type': 'fire',
                'desc': 'Smoke detector activated in Server Room B.',
                'address': 'IT Center Basement Server Room',
                'lat': 12.9728, 'lng': 77.5956,
                'status': 'resolved',
                'team': created_teams[2],
                'duration': 19
            },
            {
                'days_ago': 12,
                'hours_ago': 11,
                'type': 'harassment',
                'desc': 'Verbal dispute in parking lot near North Complex.',
                'address': 'North Academic Parking Lot B',
                'lat': 12.9715, 'lng': 77.5944,
                'status': 'rejected',
                'team': created_teams[0],
            },
            {
                'days_ago': 13,
                'hours_ago': 7,
                'type': 'security',
                'desc': 'Broken window found on ground floor faculty office.',
                'address': 'Faculty Block A, Room 108',
                'lat': 12.9717, 'lng': 77.5945,
                'status': 'resolved',
                'team': created_teams[0],
                'duration': 30
            },
            {
                'days_ago': 14,
                'hours_ago': 14,
                'type': 'medical',
                'desc': 'Seizure reported in Computer Science Library reading room.',
                'address': 'CS Dept Library, 1st Floor',
                'lat': 12.9731, 'lng': 77.5959,
                'status': 'resolved',
                'team': created_teams[1],
                'duration': 6
            },
            {
                'days_ago': 14,
                'hours_ago': 19,
                'type': 'other',
                'desc': 'Fallen tree branch blocking emergency ambulance driveway.',
                'address': 'Hospital Road Emergency Access Gate',
                'lat': 12.9712, 'lng': 77.5940,
                'status': 'resolved',
                'team': created_teams[4],
                'duration': 40
            },
            {
                'days_ago': 3,
                'hours_ago': 14,
                'type': 'security',
                'desc': 'False alarm triggered by maintenance testing.',
                'address': 'Physics Annex Hallway',
                'lat': 12.9733, 'lng': 77.5960,
                'status': 'rejected',
                'team': created_teams[0],
            }
        ]

        now = timezone.now()
        for idx, item in enumerate(incidents_seed, 1):
            reporter = random.choice(students)
            created_time = now - timedelta(days=item['days_ago'], hours=item['hours_ago'])
            
            resolved_time = None
            if item['status'] == 'resolved':
                resolved_time = created_time + timedelta(minutes=item.get('duration', 15))

            incident = Incident.objects.create(
                reported_by=reporter,
                incident_type=item['type'],
                description=item['desc'],
                address=item['address'],
                location_lat=item['lat'],
                location_lng=item['lng'],
                status=item['status'],
                assigned_team=item['team'],
                created_at=created_time,
                resolved_at=resolved_time
            )
            # Force timestamp
            Incident.objects.filter(id=incident.id).update(created_at=created_time, resolved_at=resolved_time)

            # Create realistic status progression logs
            IncidentStatusLog.objects.create(
                incident=incident,
                status='pending',
                updated_by=reporter,
                timestamp=created_time,
                notes='Incident reported by user via SOS app.'
            )

            if item['status'] in ['accepted', 'in-progress', 'resolved', 'rejected'] and item['team']:
                accept_time = created_time + timedelta(minutes=2)
                IncidentStatusLog.objects.create(
                    incident=incident,
                    status='accepted',
                    updated_by=item['team'].user,
                    timestamp=accept_time,
                    notes=f"Accepted by {item['team'].name} for dispatch."
                )

            if item['status'] in ['in-progress', 'resolved']:
                prog_time = created_time + timedelta(minutes=5)
                IncidentStatusLog.objects.create(
                    incident=incident,
                    status='in-progress',
                    updated_by=item['team'].user if item['team'] else admin_user,
                    timestamp=prog_time,
                    notes='Responders arrived on scene and assessing situation.'
                )

            if item['status'] == 'resolved':
                IncidentStatusLog.objects.create(
                    incident=incident,
                    status='resolved',
                    updated_by=item['team'].user if item['team'] else admin_user,
                    timestamp=resolved_time,
                    notes='Situation brought under control and verified safe.'
                )
            elif item['status'] == 'rejected':
                rej_time = created_time + timedelta(minutes=10)
                IncidentStatusLog.objects.create(
                    incident=incident,
                    status='rejected',
                    updated_by=admin_user,
                    timestamp=rej_time,
                    notes='Verified as false alarm / duplicate report.'
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(incidents_seed)} Incidents and Status Logs!"))
        self.stdout.write(self.style.SUCCESS("All demo fixtures are now loaded and ready."))
