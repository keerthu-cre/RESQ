from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from adminpanel.views import AdminUserViewSet, AdminTeamViewSet, AdminAnalyticsAPIView

admin_api_router = DefaultRouter()
admin_api_router.register(r'users', AdminUserViewSet, basename='admin-users')
admin_api_router.register(r'teams', AdminTeamViewSet, basename='admin-teams')

def root_redirect(request):
    return redirect('admin_dashboard')

urlpatterns = [
    # Root redirect to Admin Dashboard
    path('', root_redirect, name='root'),

    # Django built-in admin
    path('django-admin/', admin.site.urls),

    # Server-Rendered Admin Dashboard & Views
    path('admin-dashboard/', include('adminpanel.urls')),

    # REST APIs (For Person 1, Person 2, and Mobile Clients)
    path('api/auth/', include('accounts.urls')),
    path('api/incidents/', include('incidents.urls')),
    path('api/teams/', include('teams.urls')),

    # Admin REST APIs (For Person 3 & Analytics)
    path('api/admin/analytics/', AdminAnalyticsAPIView.as_view(), name='admin_api_analytics'),
    path('api/admin/', include(admin_api_router.urls)),
]
