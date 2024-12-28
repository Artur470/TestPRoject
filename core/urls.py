from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Импортируем views
from .views import UserViewSet, UserProfileViewSet, PostViewSet, GroupViewSet, add_user_to_group

# Создаём объект роутера
router = DefaultRouter()
router.register('users', UserViewSet)
router.register('profiles', UserProfileViewSet)
router.register('posts', PostViewSet)
router.register('groups', GroupViewSet)

urlpatterns = [
    # Новый путь для добавления пользователя в группу
    path('groups/<int:group_id>/add_member/', views.add_user_to_group, name='add_user_to_group'),
] + router.urls  # Добавляем все маршруты из роутера
