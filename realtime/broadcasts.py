from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

def broadcast_incident_created(incident_data):
    """
    Broadcasts a newly raised incident to the 'admin_incidents' WebSocket group.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    try:
        async_to_sync(channel_layer.group_send)(
            "admin_incidents",
            {
                "type": "incident_new",
                "data": incident_data,
            }
        )
    except Exception as e:
        logger.error(f"Error broadcasting incident_new: {e}")


def broadcast_incident_status_updated(incident_data):
    """
    Broadcasts an incident status update (accept/progress/resolve/reject)
    to the 'admin_incidents' WebSocket group.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    try:
        async_to_sync(channel_layer.group_send)(
            "admin_incidents",
            {
                "type": "incident_status_changed",
                "data": incident_data,
            }
        )
    except Exception as e:
        logger.error(f"Error broadcasting incident_status_changed: {e}")
