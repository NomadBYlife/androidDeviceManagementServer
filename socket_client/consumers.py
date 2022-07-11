import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from devices.model_dir.Devices import Device


class MainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'client_room'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        IP = text_data_json['IP']
        PORT = text_data_json['PORT']
        desc = text_data_json['desc']
        status = text_data_json['status']
        priority = text_data_json['priority']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'message_from_client',
                'IP': IP,
                'PORT': PORT,
                'desc': desc,
                'status': status,
                'priority': priority,
            }
        )

    # Receive message from room group
    async def message_from_client(self, event):
        # IP = event['IP']
        await database_sync_to_async(self.test_fn)(event)
        # Send message to WebSocket
        # await self.send(text_data=json.dumps({
        #     'message': IP
        # }))

    def test_fn(self, event):
        print(event, 'event')
        Device.objects.create(
            ip=event['IP'],
            port=event['PORT'],
            description=event['desc'],
            enabled=1,
            allocated=0,
            status='ON',
            priority=event['priority'],

        )
