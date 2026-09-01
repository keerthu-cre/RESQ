from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResponseTeamViewSet

router = DefaultRouter()
router.register(r'', ResponseTeamViewSet, basename='teams')

urlpatterns = [
    path('', include(router.urls)),
]
