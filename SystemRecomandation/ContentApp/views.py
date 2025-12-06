from django.shortcuts import render, get_object_or_404, redirect
from django.core.cache import cache
import time
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.utils.decorators import method_decorator

from .serializers import ContentSerializer, RatingSerializer, FavoriteSerializer, UserSerializer
from .services.data_get import ContentsService, ContentService
from ContentApp.models import Content, Rating, Favorite, CategoryContent
from ContentApp.services.recomendation import RecommendationEngine
from .forms import UserRegistrationForm
from .utils.recommendation_updater import RecommendationUpdater


class RefreshRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Принудительно обновляет рекомендации для текущего пользователя"""
        user = request.user

        # Очищаем весь кэш для пользователя
        from django.core.cache import cache
        keys_to_delete = []
        for key in cache._cache.keys():
            if isinstance(key, str) and f"user_recommendations_{user.id}_" in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            cache.delete(key)

        # Генерируем новые рекомендации
        recommendations = RecommendationUpdater.update_recommendations_for_user(user)

        # Сериализуем и возвращаем
        serializer = ContentSerializer(recommendations, many=True)

        return Response({
            'message': 'Рекомендации успешно обновлены',
            'recommendations': serializer.data,
            'count': len(recommendations)
        })



# API Views
class ContentView(APIView):
    serializer_class = ContentSerializer

    def get(self, request):
        contents = ContentsService.get_non_favorite_content(request.user)
        serializer = self.serializer_class(contents, many=True)
        return Response(serializer.data)


class FavoriteContentView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContentSerializer

    def get(self, request):
        contents = ContentsService.get_favorite_content(request.user)
        serializer = self.serializer_class(contents, many=True)
        return Response(serializer.data)

    def post(self, request):
        content_id = request.data.get('content_id')
        if not content_id:
            return Response({'error': 'content_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        content = get_object_or_404(Content, id=content_id, is_published=True)

        # Проверяем, не добавлен ли уже в избранное
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            content=content
        )

        if created:
            return Response({'message': 'Content added to favorites'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Content already in favorites'}, status=status.HTTP_200_OK)

    def delete(self, request):
        content_id = request.data.get('content_id')
        if not content_id:
            return Response({'error': 'content_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.filter(
            user=request.user,
            content_id=content_id
        ).first()

        if favorite:
            favorite.delete()
            return Response({'message': 'Content removed from favorites'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Content not found in favorites'}, status=status.HTTP_404_NOT_FOUND)


class RatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        content_id = request.data.get('content_id')
        rating_value = request.data.get('rating')
        text = request.data.get('text', '')

        if not content_id or not rating_value:
            return Response(
                {'error': 'content_id and rating are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        content = get_object_or_404(Content, id=content_id, is_published=True)

        # Обновляем или создаем рейтинг
        rating, created = Rating.objects.update_or_create(
            content=content,
            author=request.user,
            defaults={
                'rating': rating_value,
                'text': text
            }
        )

        serializer = RatingSerializer(rating)

        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)


class PopularContentView(APIView):
    serializer_class = ContentSerializer

    def get(self, request):
        top_n = int(request.GET.get('top', 10))
        contents = ContentsService.popular_content(top_n)
        serializer = self.serializer_class(contents, many=True)
        return Response(serializer.data)


class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContentSerializer

    def get_recommendations_with_retraining(self, user):
        """Получает рекомендации с переобучением модели с нуля"""
        cache_key = f"user_recommendations_{user.id}_{int(time.time() // 3600)}"  # Кэш на час

        # Проверяем кэш
        cached = cache.get(cache_key)
        if cached:
            return cached

        engine = RecommendationEngine()

        try:
            # Шаг 1: Подготавливаем данные с нуля
            print(f"🔄 Переобучение модели для пользователя {user.id}...")
            engine.get_default_recommendations()
            engine.prepare_user_item_matrix()

            # Шаг 2: Строим и обучаем модель с нуля
            try:
                if (engine.user_item_matrix is not None and
                        len(engine.user_item_matrix.index) > 0 and
                        len(engine.user_item_matrix.columns) > 0):

                    engine.train_deep_model(epochs=5, batch_size=32)
                    print(f"✅ Модель переобучена для пользователя {user.id}")

                    # Шаг 3: Получаем рекомендации
                    recommendations = engine.recommend_for_user(user.id, top_n=10)
                else:
                    # Если недостаточно данных
                    recommendations = ContentsService.popular_content(10)

            except Exception as train_error:
                print(f"⚠️ Ошибка обучения: {train_error}")
                recommendations = ContentsService.popular_content(10)

            # Кэшируем результат
            cache.set(cache_key, recommendations, timeout=3600)  # 1 час

            return recommendations

        except Exception as e:
            print(f"❌ Ошибка рекомендательной системы: {e}")
            recommendations = ContentsService.popular_content(10)
            cache.set(cache_key, recommendations, timeout=300)  # 5 минут при ошибке
            return recommendations

    def get(self, request):
        recommendations = self.get_recommendations_with_retraining(request.user)
        serializer = self.serializer_class(recommendations, many=True)
        return Response(serializer.data)


class CategoryVoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        content_id = request.data.get('content_id')
        category_id = request.data.get('category_id')
        vote = request.data.get('vote', 0)  # 1, -1, или 0

        if not content_id or not category_id:
            return Response(
                {'error': 'content_id and category_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        content = get_object_or_404(Content, id=content_id)

        # Проверяем, принадлежит ли категория к контенту
        if not content.category.filter(id=category_id).exists():
            return Response(
                {'error': 'Category does not belong to this content'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем или обновляем голос
        vote_obj, created = CategoryContent.objects.update_or_create(
            content=content,
            category_id=category_id,
            user=request.user,
            defaults={'vote': vote}
        )

        return Response({
            'message': 'Vote recorded successfully',
            'vote': vote,
            'created': created
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Автоматически входим после регистрации
            login(request, user)

            return Response({
                'message': 'Registration successful',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# HTML Views
def register_view(request):
    """HTML страница регистрации"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Автоматически входим после регистрации
            login(request, user)

            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('content_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'ContentApp/register.html', {'form': form})


def login_view(request):
    """HTML страница входа"""
    if request.user.is_authenticated:
        return redirect('content_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('content_list')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()

    return render(request, 'ContentApp/login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('login')


def profile_view(request):
    """Страница профиля пользователя"""
    if not request.user.is_authenticated:
        return redirect('login')

    # Статистика пользователя
    favorites_count = Favorite.objects.filter(user=request.user).count()
    ratings_count = Rating.objects.filter(author=request.user).count()
    votes_count = CategoryContent.objects.filter(user=request.user).count()

    # Последние активности
    recent_favorites = Favorite.objects.filter(user=request.user).select_related('content')[:5]
    recent_ratings = Rating.objects.filter(author=request.user).select_related('content')[:5]

    return render(request, 'ContentApp/profile.html', {
        'favorites_count': favorites_count,
        'ratings_count': ratings_count,
        'votes_count': votes_count,
        'recent_favorites': recent_favorites,
        'recent_ratings': recent_ratings,
    })


@login_required
def content_list_view(request):
    """Список всего контента"""
    contents = ContentsService.get_all_content()
    favorite_contents = ContentsService.get_favorite_content(request.user)
    favorite_ids = [c.id for c in favorite_contents]

    return render(request, 'ContentApp/content_list.html', {
        'contents': contents,
        'favorite_ids': favorite_ids
    })


@login_required
def favorite_content_view(request):
    """Список избранного контента"""
    contents = ContentsService.get_favorite_content(request.user)

    return render(request, 'ContentApp/favorites.html', {
        'contents': contents
    })


@login_required
def content_detail_view(request, content_id):
    """Детальная страница контента"""
    content = get_object_or_404(Content, id=content_id, is_published=True)

    # Получаем рейтинг пользователя
    user_rating = ContentService.get_rating(request.user, content)

    # Получаем средний рейтинг
    avg_rating = ContentService.get_content_rating(content)

    # Получаем категории с голосами
    categories_vote = ContentService.get_real_content_category(content)

    # Проверяем, в избранном ли
    is_favorite = Favorite.objects.filter(
        user=request.user,
        content=content
    ).exists()

    # Получаем рекомендации
    engine = RecommendationEngine()
    engine.get_default_recommendations()
    similar_content = engine.get_simular_content(content_id, 5)

    return render(request, 'ContentApp/content_detail.html', {
        'content': content,
        'user_rating': user_rating,
        'avg_rating': avg_rating or 0,
        'categories_vote': categories_vote,
        'is_favorite': is_favorite,
        'similar_content': similar_content
    })


@login_required
def recommendations_view(request):
    """Страница с персональными рекомендациями"""
    engine = RecommendationEngine()

    try:
        engine.get_default_recommendations()
        engine.prepare_user_item_matrix()

        recommendations = engine.recommend_for_user(request.user.id, top_n=12)

        if not recommendations:
            recommendations = ContentsService.popular_content(12)

    except Exception as e:
        recommendations = ContentsService.popular_content(12)

    return render(request, 'ContentApp/recommendations.html', {
        'recommendations': recommendations
    })


@login_required
def popular_content_view(request):
    """Страница с популярным контентом"""
    contents = ContentsService.popular_content(20)

    return render(request, 'ContentApp/popular.html', {
        'contents': contents
    })