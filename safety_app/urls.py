from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Emergency SOS & Actions
    path('api/sos/trigger/', views.sos_trigger_view, name='sos_trigger'),
    path('api/incidents/sos/', views.sos_trigger_view, name='api_sos_trigger'),
    
    # Incidents
    path('report/', views.incident_report_view, name='incident_report'),
    path('my-reports/', views.my_reports_view, name='my_reports'),
    path('incidents/<int:pk>/', views.incident_detail_view, name='incident_detail'),
    path('incidents/<int:pk>/status/', views.incident_status_api, name='incident_status_api'),
    path('api/incidents/<int:pk>/status/', views.incident_status_api, name='api_incident_status'),
    path('incidents/<int:pk>/safe/', views.resolve_safe_view, name='resolve_safe'),
    path('api/incidents/<int:pk>/safe/', views.resolve_safe_view, name='api_resolve_safe'),
    path('incidents/<int:pk>/cancel/', views.cancel_incident_view, name='cancel_incident'),
    path('incidents/<int:pk>/simulate/', views.simulate_response_api, name='simulate_response'),
    
    # Emergency Contacts
    path('contacts/', views.contacts_view, name='contacts'),
    path('contacts/add/', views.add_contact_view, name='add_contact'),
    path('contacts/<int:pk>/edit/', views.edit_contact_view, name='edit_contact'),
    path('contacts/<int:pk>/delete/', views.delete_contact_view, name='delete_contact'),
    
    # Profile & Preferences
    path('profile/', views.profile_view, name='profile'),
    path('location/', views.location_view, name='location'),
    path('settings/', views.settings_view, name='settings'),
    path('api/accessibility/update/', views.update_accessibility_api, name='update_accessibility'),
]


