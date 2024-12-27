import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Group

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.group_group_name = f"chat_{self.group_name}"

        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.group_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Отключаемся от группы
        await self.channel_layer.group_discard(
            self.group_group_name,
            self.channel_name
        )

    # Получаем сообщение от WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', None)
        action = text_data_json.get('action', None)

        # Если сообщение это обычное сообщение чата
        if message:
            # Отправляем сообщение в группу
            await self.channel_layer.group_send(
                self.group_group_name,
                {
                    'type': 'chat_message',
                    'message': message
                }
            )

        # Если действие это "user_added", отправляем уведомление группе
        if action == "user_added":
            new_user = text_data_json.get('new_user', 'unknown')
            notification_message = f"{new_user} был добавлен в группу."

            # Отправляем уведомление всем участникам группы
            await self.channel_layer.group_send(
                self.group_group_name,
                {
                    'type': 'group_notification',
                    'message': notification_message
                }
            )

    # Получаем сообщение от группы (обычное сообщение чата)
    async def chat_message(self, event):
        message = event['message']

        # Отправляем сообщение WebSocket клиенту
        await self.send(text_data=json.dumps({
            'message': message
        }))

    # Получаем уведомление от группы (для действия user_added)
    async def group_notification(self, event):
        message = event['message']

        # Отправляем уведомление WebSocket клиенту
        await self.send(text_data=json.dumps({
            'notification': message
        }))
