# ContentApp/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth.models import User
from ContentApp.models import Favorite, Rating, CategoryContent


@receiver([post_save, post_delete], sender=Favorite)
def clear_recommendation_cache_on_favorite_change(sender, instance, **kwargs):
    """Очищает кэш рекомендаций при изменении избранного"""
    if hasattr(instance, 'user'):
        # Очищаем кэш рекомендаций для конкретного пользователя
        user_id = instance.user.id

        # Ищем все ключи кэша для этого пользователя
        cache_keys_to_delete = []
        for key in cache._cache.keys():  # Адаптируй под твой бэкенд кэша
            if isinstance(key, str) and f"user_recommendations_{user_id}_" in key:
                cache_keys_to_delete.append(key)

        # Удаляем найденные ключи
        for key in cache_keys_to_delete:
            cache.delete(key)

        print(f"🧹 Очищен кэш рекомендаций для пользователя {user_id}")


@receiver([post_save, post_delete], sender=Rating)
def clear_recommendation_cache_on_rating_change(sender, instance, **kwargs):
    """Очищает кэш рекомендаций при изменении рейтингов"""
    if hasattr(instance, 'author'):
        user_id = instance.author.id
        cache.delete_pattern(f"user_recommendations_{user_id}_*")


@receiver([post_save, post_delete], sender=CategoryContent)
def clear_recommendation_cache_on_vote_change(sender, instance, **kwargs):
    """Очищает кэш рекомендаций при изменении голосов"""
    if hasattr(instance, 'user'):
        user_id = instance.user.id
        cache.delete_pattern(f"user_recommendations_{user_id}_*")


# Для Redis или других бэкендов с поддержкой delete_pattern
def clear_all_user_recommendations(user_id):
    """Утилита для полной очистки кэша рекомендаций пользователя"""
    # Если используешь Redis
    try:
        from django_redis import get_redis_connection
        redis = get_redis_connection("default")
        pattern = f"*user_recommendations_{user_id}_*"
        keys = redis.keys(pattern)
        if keys:
            redis.delete(*keys)
            print(f"🧹 Очищено {len(keys)} ключей рекомендаций для пользователя {user_id}")
    except:
        # Fallback для локального кэша
        for key in list(cache._cache.keys()):
            if isinstance(key, str) and f"user_recommendations_{user_id}_" in key:
                cache.delete(key)