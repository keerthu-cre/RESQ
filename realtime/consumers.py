import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AdminIncidentConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = "admin_incidents"

    async def connect(self):
        # Join admin incidents broadcast room
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name
        )
        await self.accept()
        
        # Send initial connected confirmation ping
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected to RESQ Live Incident Stream."
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        # Allow ping/heartbeat from client
        if text_data:
            try:
                data = json.loads(text_data)
                if data.get("type") == "ping":
                    await self.send(text_data=json.dumps({"type": "pong"}))
            except Exception:
                pass

    # Handler for incident.new events
    async def incident_new(self, event):
        await self.send(text_data=json.dumps({
            "event": "incident.new",
            "data": event["data"]
        }))

    # Handler for incident.status_changed events
    async def incident_status_changed(self, event):
        await self.send(text_data=json.dumps({
            "event": "incident.status_changed",
            "data": event["data"]
        }))
