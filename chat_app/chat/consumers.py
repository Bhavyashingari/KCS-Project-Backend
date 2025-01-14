import json
from channels.generic.websocket import AsyncWebsocketConsumer
from chat_app.chat.serializers import AddMessageSerializer
from .models import Room, Message
from channels.auth import login, logout

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Fetch the latest messages for this room in descending order of timestamp
        messages = Message.objects.filter(room__name=self.room_name).order_by('-timestamp')[:10]  # Fetch the latest 10 messages
        message_data = [
            {
                'message_id': message.message_id,
                'content': message.content,
                'timestamp': message.timestamp
            }
            for message in messages
        ]

        # Send the previous 10 messages to the WebSocket client
        await self.send(text_data=json.dumps({
            'messages': message_data
        }))

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        room = Room.objects.get(name=self.room_name)

        # Save the message using the AddMessageSerializer logic
        serializer = AddMessageSerializer(data={
            'room_id': room.room_id,
            'user_id': str(self.scope.get("user", None).id) if self.scope.get("user") else None,  # Optionally, handle missing user
            'content': message_content
        })

        if serializer.is_valid():
            message = serializer.save()

            # Send the message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'message_id': message.message_id,
                        'content': message.content,
                        'timestamp': message.timestamp
                    }
                }
            )
        else:
            # Handle validation errors (optional)
            await self.send(text_data=json.dumps({
                'error': 'Message could not be saved'
            }))

    async def chat_message(self, event):
        message = event['message']

        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

class VideoChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'video_{self.room_name}'

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Broadcast data to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_signal',
                'data': data
            }
        )

    async def video_signal(self, event):
        # Send signaling data to WebSocket clients
        await self.send(text_data=json.dumps(event['data']))
