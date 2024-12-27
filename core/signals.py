from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Создаем профиль только при создании нового пользователя
        UserProfile.objects.create(user=instance)

        # Отправляем уведомление через WebSocket
        channel_layer = get_channel_layer()
        message = f"Профиль пользователя {instance.username} был создан."

        # Отправляем сообщение в группу WebSocket
        async_to_sync(channel_layer.group_send)(
            "notifications",  # Название группы, куда будем отправлять уведомления
            {
                "type": "chat.message",  # Тип события
                "message": message,  # Само сообщение
            }
        )
