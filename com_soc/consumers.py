import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta
from .models import ChatMensagem

class ChatConsumer(AsyncWebsocketConsumer):
    online_users = set()

    async def connect(self):
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close()
            return

        is_subscriber = getattr(user, 'role', None) == 'Subscritor'
        is_staff = user.is_staff or user.is_superuser

        if not is_subscriber and not is_staff:
            await self.close()
            return

        self.room_group_name = 'chat_subscribers'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        ChatConsumer.online_users.add(self.channel_name)
        await self.broadcast_online_count()

        mensagens = await self.get_recent_messages()
        for msg in mensagens:
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message': msg['conteudo'],
                'username': msg['utilizador__username'],
                'timestamp': msg['timestamp'].strftime('%H:%M'),
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            ChatConsumer.online_users.discard(self.channel_name)
            await self.broadcast_online_count()
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        user = self.scope['user']
        data = json.loads(text_data)
        message = data.get('message', '').strip()

        if not message:
            return

        await self.save_message(user, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': user.username,
                'timestamp': timezone.now().strftime('%H:%M'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    async def broadcast_online_count(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_count',
                'count': len(ChatConsumer.online_users),
            }
        )

    async def online_count(self, event):
        await self.send(text_data=json.dumps({
            'type': 'online_count',
            'count': event['count'],
        }))

    @database_sync_to_async
    def get_recent_messages(self):
        since = timezone.now() - timedelta(hours=24)
        return list(
            ChatMensagem.objects.filter(
                timestamp__gte=since,
                estado=ChatMensagem.Estado.NORMAL
            )
            .select_related('utilizador')
            .order_by('timestamp')
            .values('conteudo', 'utilizador__username', 'timestamp')
        )

    @database_sync_to_async
    def save_message(self, user, message):
        ChatMensagem.objects.create(
            utilizador=user,
            conteudo=message,
        )