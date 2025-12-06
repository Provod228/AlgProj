from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from ContentApp.models import Content, Rating, Favorite, Category, CategoryContent


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'password', 'password2', 'date_joined']
        read_only_fields = ['id', 'date_joined']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

    def update(self, instance, validated_data):
        # Удаляем password2 из данных
        validated_data.pop('password2', None)

        # Если есть новый пароль, устанавливаем его
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ContentSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(source='category', many=True, read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    avg_rating = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = [
            'id', 'title', 'summary', 'price', 'categories',
            'author_name', 'is_published', 'is_digital',
            'created_at', 'updated_at', 'slug', 'image',
            'avg_rating', 'is_favorite'
        ]

    def get_avg_rating(self, obj):
        from ContentApp.services.data_get import ContentService
        return ContentService.get_content_rating(obj)

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False


class RatingSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'content', 'content_title', 'rating', 'text',
                  'author_name', 'created_at', 'updated_at']
        read_only_fields = ['author_name', 'content_title', 'created_at', 'updated_at']


class FavoriteSerializer(serializers.ModelSerializer):
    content = ContentSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['user', 'created_at']


class CategoryContentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CategoryContent
        fields = ['id', 'content', 'content_title', 'category', 'category_name',
                  'user', 'user_name', 'vote', 'created_at', 'updated_at']
        read_only_fields = ['content_title', 'category_name', 'user_name',
                            'created_at', 'updated_at']