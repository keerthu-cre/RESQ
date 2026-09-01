from django.urls import re_path
from .consumers import AdminIncidentConsumer

websocket_urlpatterns = [
    re_path(r'^ws/admin/incidents/$', AdminIncidentConsumer.as_asgi()),
]
