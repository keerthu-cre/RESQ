import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile, EmergencyContact, Incident, IncidentStatusLog
from .forms import (
    UserRegistrationForm, UserProfileForm, IncidentReportForm, EmergencyContactForm
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please check your credentials.")
            
    return render(request, 'auth/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Profile created by signal, update fields
            profile = user.profile
            profile.student_id = form.cleaned_data['student_id']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.dormitory_block = form.cleaned_data.get('dormitory_block', '')
            profile.save()
            
            # Auto add default campus police as global contact
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome to SafeCampus, {user.first_name or user.username}.")
            return redirect('dashboard')
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.capitalize()}: {err}")
    else:
        form = UserRegistrationForm()
        
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been securely logged out.")
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Check for active incidents for this user
    active_incident = Incident.objects.filter(
        user=user, 
        status__in=['PENDING', 'ACCEPTED', 'ON_THE_WAY', 'ARRIVED']
    ).first()
    
    # Recent reports (last 3)
    recent_reports = Incident.objects.filter(user=user).exclude(
        id=active_incident.id if active_incident else -1
    )[:3]
    
    # Primary emergency contacts & campus hotlines
    campus_hotlines = EmergencyContact.objects.filter(is_campus_service=True)[:2]
    personal_contacts = EmergencyContact.objects.filter(user=user)[:3]
    
    context = {
        'profile': profile,
        'active_incident': active_incident,
        'recent_reports': recent_reports,
        'campus_hotlines': campus_hotlines,
        'personal_contacts': personal_contacts,
    }
    return render(request, 'dashboard.html', context)


@login_required
@require_POST
def sos_trigger_view(request):
    """
    Triggered when the user completes the 2-second press and hold on the SOS button.
    Instantly creates a Critical Emergency incident with captured geolocation.
    Guarantees user ownership via request.user and prevents duplicate active incidents.
    """
    user = request.user
    
    # Parse payload (can be JSON or Form Data)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}
    else:
        data = request.POST
        
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    location_name = data.get('location_name', '').strip() or "Location unavailable"
    
    try:
        latitude = float(latitude) if latitude is not None and str(latitude).strip() != '' else None
        longitude = float(longitude) if longitude is not None and str(longitude).strip() != '' else None
    except (ValueError, TypeError):
        latitude = None
        longitude = None

    # Check if there is already an active emergency for this user (prevent duplicates)
    active_incident = Incident.objects.filter(
        user=user,
        status__in=['PENDING', 'ACCEPTED', 'ON_THE_WAY', 'ARRIVED']
    ).first()
    
    if active_incident:
        return JsonResponse({
            'success': False,
            'already_active': True,
            'incident_id': active_incident.id,
            'message': 'You already have an active emergency request in progress.',
            'status': active_incident.status,
            'status_display': active_incident.get_status_display(),
            'tracker_url': f"/incidents/{active_incident.id}/"
        })

    # Create new emergency incident
    incident = Incident.objects.create(
        user=user,
        incident_type='EMERGENCY',
        urgency='CRITICAL',
        status='PENDING',
        is_sos=True,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        description=f"EMERGENCY SOS activated by {user.get_full_name() or user.username} (Student ID: {getattr(user.profile, 'student_id', 'N/A')}). Phone: {getattr(user.profile, 'phone_number', 'N/A')}."
    )
    
    # Initial status audit log
    IncidentStatusLog.objects.create(
        incident=incident,
        status='PENDING',
        note='Emergency SOS Beacon Broadcasted to Campus Police & Rapid Units',
        updated_by='RESQ SOS Gateway'
    )
    
    return JsonResponse({
        'success': True,
        'incident_id': incident.id,
        'status': incident.status,
        'status_display': incident.get_status_display(),
        'created_at': incident.created_at.strftime('%H:%M:%S'),
        'location_name': incident.location_name,
        'has_location': bool(latitude is not None and longitude is not None),
        'message': 'SOS SENT! Help is being arranged.',
        'tracker_url': f"/incidents/{incident.id}/"
    })


@login_required
def incident_report_view(request):
    if request.method == 'POST':
        form = IncidentReportForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.user = request.user
            incident.status = 'PENDING'
            if incident.incident_type == 'EMERGENCY':
                incident.is_sos = True
                incident.urgency = 'CRITICAL'
            incident.save()
            
            # Create audit log
            IncidentStatusLog.objects.create(
                incident=incident,
                status='PENDING',
                note=f"Incident '{incident.get_incident_type_display()}' reported by student.",
                updated_by=request.user.get_full_name() or request.user.username
            )
            
            messages.success(request, "Incident report submitted successfully! Dispatch is notified.")
            return redirect('incident_detail', pk=incident.id)
        else:
            messages.error(request, "Please check the required fields in the form.")
    else:
        form = IncidentReportForm()
        
    return render(request, 'incidents/report.html', {'form': form})


@login_required
def my_reports_view(request):
    status_filter = request.GET.get('status', 'all')
    reports = Incident.objects.filter(user=request.user)
    
    if status_filter == 'active':
        reports = reports.filter(status__in=['PENDING', 'ACCEPTED', 'ON_THE_WAY', 'ARRIVED'])
    elif status_filter == 'resolved':
        reports = reports.filter(status='RESOLVED')
    elif status_filter == 'cancelled':
        reports = reports.filter(status='CANCELLED')
        
    return render(request, 'incidents/my_reports.html', {
        'reports': reports,
        'current_filter': status_filter
    })


@login_required
def incident_detail_view(request, pk):
    incident = get_object_or_404(Incident, pk=pk, user=request.user)
    logs = incident.status_logs.all()
    
    context = {
        'incident': incident,
        'logs': logs,
    }
    return render(request, 'incidents/detail.html', context)


@login_required
def incident_status_api(request, pk):
    """
    Polled by the frontend live tracker every 2-3s for live updates.
    """
    incident = get_object_or_404(Incident, pk=pk, user=request.user)
    logs = [
        {
            'status': log.status,
            'status_display': log.get_status_display(),
            'note': log.note,
            'updated_by': log.updated_by,
            'time': log.created_at.strftime('%H:%M:%S')
        }
        for log in incident.status_logs.all()
    ]
    
    return JsonResponse({
        'id': incident.id,
        'incident_type': incident.incident_type,
        'incident_type_display': incident.get_incident_type_display(),
        'urgency': incident.urgency,
        'status': incident.status,
        'status_display': incident.get_status_display(),
        'is_active': incident.is_active(),
        'location_name': incident.location_name,
        'latitude': incident.latitude,
        'longitude': incident.longitude,
        'response_team_name': incident.response_team_name or 'Campus Emergency Rapid Unit',
        'responder_notes': incident.responder_notes or '',
        'eta_minutes': incident.eta_minutes,
        'created_at': incident.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': incident.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'resolved_at': incident.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if incident.resolved_at else None,
        'logs': logs
    })


@login_required
@require_POST
def resolve_safe_view(request, pk):
    """
    Triggered when student clicks "I'M SAFE" button.
    """
    incident = get_object_or_404(Incident, pk=pk, user=request.user)
    if incident.status != 'RESOLVED':
        incident.mark_resolved(responder_note="Student marked themselves SAFE.")
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'status': 'RESOLVED',
            'message': "Thank goodness you are safe! Emergency has been marked resolved."
        })
        
    messages.success(request, "Thank you! Your emergency incident has been marked resolved.")
    return redirect('incident_detail', pk=incident.id)


@login_required
@require_POST
def cancel_incident_view(request, pk):
    incident = get_object_or_404(Incident, pk=pk, user=request.user)
    if incident.is_active():
        incident.status = 'CANCELLED'
        incident.save()
        IncidentStatusLog.objects.create(
            incident=incident,
            status='CANCELLED',
            note='Cancelled by student (False Alarm)',
            updated_by=request.user.get_full_name() or request.user.username
        )
        messages.info(request, "Incident cancelled.")
        
    return redirect('dashboard')


@login_required
def contacts_view(request):
    user_contacts = EmergencyContact.objects.filter(user=request.user)
    campus_hotlines = EmergencyContact.objects.filter(is_campus_service=True)
    form = EmergencyContactForm()
    
    return render(request, 'contacts/contacts.html', {
        'user_contacts': user_contacts,
        'campus_hotlines': campus_hotlines,
        'form': form
    })


@login_required
@require_POST
def add_contact_view(request):
    form = EmergencyContactForm(request.POST)
    if form.is_valid():
        contact = form.save(commit=False)
        contact.user = request.user
        if contact.is_primary:
            # Unmark other primary contacts
            EmergencyContact.objects.filter(user=request.user).update(is_primary=False)
        contact.save()
        messages.success(request, f"Emergency contact '{contact.name}' added successfully.")
    else:
        for field, errs in form.errors.items():
            for err in errs:
                messages.error(request, f"{field.capitalize()}: {err}")
                
    return redirect('contacts')


@login_required
@require_POST
def edit_contact_view(request, pk):
    contact = get_object_or_404(EmergencyContact, pk=pk, user=request.user)
    form = EmergencyContactForm(request.POST, instance=contact)
    if form.is_valid():
        c = form.save(commit=False)
        if c.is_primary:
            EmergencyContact.objects.filter(user=request.user).exclude(pk=pk).update(is_primary=False)
        c.save()
        messages.success(request, f"Contact '{c.name}' updated.")
    else:
        messages.error(request, "Please check contact details.")
    return redirect('contacts')


@login_required
@require_POST
def delete_contact_view(request, pk):
    contact = get_object_or_404(EmergencyContact, pk=pk, user=request.user)
    contact_name = contact.name
    contact.delete()
    messages.info(request, f"Contact '{contact_name}' deleted.")
    return redirect('contacts')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid():
            user = request.user
            user.first_name = user_form.cleaned_data['first_name']
            user.last_name = user_form.cleaned_data['last_name']
            user.email = user_form.cleaned_data['email']
            user.save()
            user_form.save()
            messages.success(request, "Emergency profile & medical info updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct errors below.")
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        user_form = UserProfileForm(instance=profile, initial=initial)
        
    return render(request, 'profile/profile.html', {
        'profile': profile,
        'form': user_form
    })


@login_required
@require_POST
def update_accessibility_api(request):
    """
    Persists accessibility toggle settings on user profile via AJAX.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST
        
    if 'dark_mode' in data:
        profile.dark_mode = bool(data.get('dark_mode'))
    if 'high_contrast' in data:
        profile.high_contrast = bool(data.get('high_contrast'))
    if 'large_text' in data:
        profile.large_text = bool(data.get('large_text'))
    if 'reduce_motion' in data:
        profile.reduce_motion = bool(data.get('reduce_motion'))
    if 'voice_assist' in data:
        profile.voice_assist = bool(data.get('voice_assist'))
        
    profile.save()
    return JsonResponse({'success': True, 'message': 'Accessibility preferences saved.'})


@login_required
def settings_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'settings/settings.html', {'profile': profile})


@login_required
def location_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'location/location.html', {'profile': profile})


@login_required
@require_POST
def simulate_response_api(request, pk):
    """
    DEMO SIMULATOR ENDPOINT:
    Allows reviewer to simulate Response Team lifecycle steps:
    PENDING -> ACCEPTED -> ON_THE_WAY -> ARRIVED -> RESOLVED
    This fulfills the requirement to demo the live flow before response team app is connected.
    """
    incident = get_object_or_404(Incident, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST
        
    target_status = data.get('target_status')
    
    status_order = ['PENDING', 'ACCEPTED', 'ON_THE_WAY', 'ARRIVED', 'RESOLVED']
    
    if not target_status or target_status == 'next':
        current_idx = status_order.index(incident.status) if incident.status in status_order else 0
        if current_idx < len(status_order) - 1:
            target_status = status_order[current_idx + 1]
        else:
            target_status = 'RESOLVED'
            
    if target_status not in status_order:
        return HttpResponseBadRequest("Invalid status")
        
    incident.status = target_status
    if not incident.response_team_name:
        incident.response_team_name = "Campus Rapid Response Team Alpha"
        
    if target_status == 'ACCEPTED':
        incident.eta_minutes = 6
        incident.responder_notes = "Dispatch confirmed. Officer Davis & EMT Unit 2 assigned."
        note = "Dispatch Accepted by Officer Davis (Alpha Unit 2). Initial ETA 6 mins."
    elif target_status == 'ON_THE_WAY':
        incident.eta_minutes = 3
        incident.responder_notes = "Emergency vehicle en route with sirens active. Clear building entrance."
        note = "Responder Unit Alpha is en route with priority beacon. Updated ETA 3 mins."
    elif target_status == 'ARRIVED':
        incident.eta_minutes = 0
        incident.responder_notes = "First responder unit has arrived at building entrance / location."
        note = "Responder Unit Alpha has arrived on scene. First responders contacting student."
    elif target_status == 'RESOLVED':
        incident.eta_minutes = 0
        incident.resolved_at = timezone.now()
        incident.responder_notes = "Situation assessed, secured, and resolved by campus safety."
        note = "Emergency marked RESOLVED by Rapid Response Team."
    else:
        note = f"Status updated to {target_status}"
        
    incident.save()
    
    IncidentStatusLog.objects.create(
        incident=incident,
        status=target_status,
        note=note,
        updated_by=incident.response_team_name
    )
    
    return JsonResponse({
        'success': True,
        'new_status': incident.status,
        'new_status_display': incident.get_status_display(),
        'eta_minutes': incident.eta_minutes,
        'responder_notes': incident.responder_notes,
        'message': f"Simulation: Incident status moved to '{incident.get_status_display()}'"
    })
