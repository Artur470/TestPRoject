from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import UserProfile, Post, Group, Message
from .serializers import UserSerializer, UserProfileSerializer, PostSerializer, GroupSerializer, MessageSerializer
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from rest_framework import status
from asgiref.sync import async_to_sync
from django.core.mail import send_mail, BadHeaderError
import logging
# Страница с лобби, где отображаются все группы
def lobby_view(request):
    groups = Group.objects.all()
    return render(request, 'lobby.html', {'groups': groups})

# Страница чата для конкретной группы
def chat_view(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    return render(request, 'chat.html', {'group': group})

# API для отправки сообщений в группу
@api_view(['POST'])
def send_message(request):
    group_name = request.data.get('group_name')
    username = request.data.get('username')
    message_content = request.data.get('message')

    if not group_name or not username or not message_content:
        return Response({"error": "Missing required fields: group_name, username, message"}, status=400)

    group = get_object_or_404(Group, name=group_name)
    user = get_object_or_404(User, username=username)

    message = Message.objects.create(
        group=group,
        user=user,
        content=message_content
    )
    message.save()

    return Response({"status": "Message sent to group"}, status=200)

# Вьюсет для пользователей


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        # Создание пользователя
        response = super().create(request, *args, **kwargs)

        # После успешного создания пользователя создаем профиль
        if response.status_code == status.HTTP_201_CREATED:
            user = response.data  # Получаем данные созданного пользователя

            # Проверяем, что в ответе есть username
            if 'username' in user:
                try:
                    # Ищем пользователя по username, который только что был создан
                    user_instance = User.objects.get(username=user['username'])
                    # Создаем профиль для пользователя
                    user_profile, created = UserProfile.objects.get_or_create(user=user_instance)

                    # Вы можете отправить уведомление, если профиль был создан, если нужно
                    if created:
                        # Тут можно добавить логику уведомлений через WebSocket или другие методы
                        pass

                except User.DoesNotExist:
                    return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        return response


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def perform_create(self, serializer):
        # Просто сохраняем группу
        serializer.save()

    @action(detail=False, methods=['get'])
    def clean_empty_groups(self, request):
        empty_groups = Group.objects.filter(members__isnull=True)
        empty_groups.delete()
        return Response({"message": "Empty groups have been deleted."})

    @api_view(['POST'])
    def create_group(request):
        # Проверяем наличие имени группы
        group_name = request.data.get('name')
        if not group_name:
            return Response({"error": "Group name is required"}, status=400)

        # Проверка, существует ли уже группа с таким именем
        if Group.objects.filter(name=group_name).exists():
            return Response({"error": "Group with this name already exists"}, status=400)

        # Создаем группу
        group = Group.objects.create(name=group_name)
        return Response({"message": f"Group '{group_name}' created successfully!"}, status=status.HTTP_201_CREATED)


# Логирование ошибок
logger = logging.getLogger(__name__)

@api_view(['POST'])
def add_user_to_group(request, group_id):
    # Получаем имя пользователя из данных запроса
    username = request.data.get('username')
    if not username:
        return Response({"error": "Username is required"}, status=400)

    # Получаем группу по ID
    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, username=username)

    # Сначала обновляем объект группы из базы данных
    group.refresh_from_db()

    # Проверяем, не является ли пользователь уже членом группы
    if user in group.members.all():
        return Response({"error": f"User {username} is already a member of the group {group.name}."}, status=400)

    # Добавляем пользователя в группу
    group.members.add(user)
    group.save()

    # Отправляем уведомление
    send_group_notification(group, user)

    return Response({"message": f"User {username} added to group {group.name} successfully!"}, status=status.HTTP_200_OK)


# Функция для отправки уведомления участникам группы
def send_group_notification(group, new_user):
    # Отправка уведомления через WebSocket
    channel_layer = get_channel_layer()
    group_name = f"group_{group.id}"

    try:
        # Отправляем уведомление всем членам группы через WebSocket
        channel_layer.group_send(
            group_name,
            {
                "type": "user_added",  # Тип события
                "message": f"User {new_user.username} was added to group {group.name}."
            }
        )

        # Дополнительно можно отправить email-уведомление
        members = group.members.all()
        emails = [member.email for member in members if member.email]

        if emails:
            send_mail(
                f'Новый пользователь в группе {group.name}',
                f'Пользователь {new_user.username} был добавлен в группу {group.name}.',
                'from@example.com',
                emails
            )

    except BadHeaderError:
        logger.error("Invalid header while sending email notification.")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")