from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# Профиль пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# Сигнал для автоматического создания профиля
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:  # Проверяем, что пользователь только что создан
        UserProfile.objects.get_or_create(user=instance)


# Посты пользователей
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return f"Post: {self.title} by {self.author.username}"


# Группы для общения
class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Название группы уникальное
    members = models.ManyToManyField(User, related_name='user_groups', blank=True)

    def __str__(self):
        return self.name


# Сообщения в группе
class Message(models.Model):
    group = models.ForeignKey(Group, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.user.username} in {self.group.name} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
