import json
from channels.generic.websocket import AsyncWebsocketConsumer
import uuid

class VideoCallConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = "video_call_room"
        self.user_id = None
        self.location = None
        self.location_name = None

    async def connect(self):
        self.user_id = str(uuid.uuid4())[:8]
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user_id,
                'location': self.location,
                'location_name': self.location_name,
                'message': f'User {self.user_id} joined'
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user_id,
                'message': f'User {self.user_id} left'
            }
        )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'location_info':
                self.location = data.get('location')
                self.location_name = data.get('location_name')
                print(f"User {self.user_id} 위치 정보 업데이트: {self.location_name}")
                
                # 다른 사용자들에게 위치 정보 알림
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'location_updated',
                        'user_id': self.user_id,
                        'location': self.location,
                        'location_name': self.location_name
                    }
                )
                
            elif message_type == 'offer':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_message',
                        'message_type': 'offer',
                        'offer': data.get('offer'),
                        'from_user': self.user_id,
                        'to_user': data.get('to_user', 'all')
                    }
                )
                
            elif message_type == 'answer':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_message',
                        'message_type': 'answer',
                        'answer': data.get('answer'),
                        'from_user': self.user_id,
                        'to_user': data.get('to_user')
                    }
                )
                
            elif message_type == 'ice_candidate':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_message',
                        'message_type': 'ice_candidate',
                        'candidate': data.get('candidate'),
                        'from_user': self.user_id,
                        'to_user': data.get('to_user')
                    }
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))

    async def user_joined(self, event):
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'location': event.get('location'),
                'location_name': event.get('location_name'),
                'message': event['message']
            }))

    async def user_left(self, event):
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'location': event.get('location'),
                'location_name': event.get('location_name'),
                'message': event['message']
            }))

    async def location_updated(self, event):
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'location_updated',
                'user_id': event['user_id'],
                'location': event['location'],
                'location_name': event['location_name']
            }))

    async def webrtc_message(self, event):
        if event['from_user'] != self.user_id:
            if event['to_user'] == 'all' or event['to_user'] == self.user_id:
                await self.send(text_data=json.dumps({
                    'type': event['message_type'],
                    'from_user': event['from_user'],
                    'offer': event.get('offer'),
                    'answer': event.get('answer'),
                    'candidate': event.get('candidate')
                }))