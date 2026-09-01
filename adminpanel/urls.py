from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
    path('', views.dashboard_view, name='admin_dashboard'),
    path('incidents/', views.incidents_list_view, name='admin_incidents'),
    path('incidents/<int:pk>/', views.incident_detail_view, name='admin_incident_detail'),
    path('users/', views.users_list_view, name='admin_users'),
    path('users/<int:pk>/', views.user_detail_view, name='admin_user_detail'),
    path('users/<int:pk>/toggle-status/', views.user_toggle_status_view, name='admin_user_toggle_status'),
    path('teams/', views.teams_list_view, name='admin_teams'),
    path('teams/<int:pk>/', views.team_detail_view, name='admin_team_detail'),
    path('analytics/', views.analytics_page_view, name='admin_analytics'),
    path('export-csv/', views.export_incidents_csv, name='admin_export_csv'),
]
