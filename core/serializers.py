from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post, Group, UserProfile, Message


# Сериализатор для профиля пользователя
class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Отображение имени пользователя вместо ID

    class Meta:
        model = UserProfile
        fields = ['id', 'bio', 'birth_date', 'user']


# Сериализатор для постов
class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)  # Автоматическое получение username автора

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author']

    def create(self, validated_data):
        # Извлекаем текущего пользователя из контекста запроса
        request = self.context.get('request')
        author = request.user if request else None
        if not author:
            raise serializers.ValidationError("Author must be authenticated.")

        # Создаем пост
        return Post.objects.create(author=author, **validated_data)


# Сериализатор для групп
class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(), many=True
    )  # Отображение username вместо ID

    class Meta:
        model = Group
        fields = ['id', 'name', 'members']


# Сериализатор для пользователей
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    posts = PostSerializer(many=True, read_only=True)
    user_groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', 'posts', 'user_groups']

    def create(self, validated_data):
        # Извлекаем данные профиля, если они переданы
        profile_data = validated_data.pop('profile', None)

        # Создаем пользователя
        user = User.objects.create_user(**validated_data)

        # Создаем профиль пользователя
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.get_or_create(user=user)

        return user


# Сериализатор для сообщений
class MessageSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    group = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'group', 'user', 'content', 'created_at']


# Сериализатор для добавления пользователя в группу
class AddUserToGroupSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()

    def validate(self, data):
        user = User.objects.filter(id=data['user_id']).first()
        group = Group.objects.filter(id=data['group_id']).first()

        if not user:
            raise serializers.ValidationError("User not found.")
        if not group:
            raise serializers.ValidationError("Group not found.")
        if user in group.members.all():
            raise serializers.ValidationError("User is already a member of this group.")

        return data

    def save(self):
        validated_data = self.validated_data
        user = User.objects.get(id=validated_data['user_id'])
        group = Group.objects.get(id=validated_data['group_id'])
        group.members.add(user)  # Добавляем пользователя в группу
        return group
