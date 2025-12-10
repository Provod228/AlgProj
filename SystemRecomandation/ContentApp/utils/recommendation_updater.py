from ContentApp.services.recomendation import RecommendationEngine
from ContentApp.services.data_get import ContentsService
from django.core.cache import cache
import time


class RecommendationUpdater:
    """Утилита для обновления рекомендаций"""

    @staticmethod
    def update_recommendations_for_user(user):
        """Принудительно обновляет рекомендации для пользователя"""
        cache_key = f"user_recommendations_{user.id}_{int(time.time())}"

        engine = RecommendationEngine()

        try:
            # Полная пересборка с нуля
            engine.get_default_recommendations()
            engine.prepare_user_item_matrix()

            if (engine.user_item_matrix is not None and
                    len(engine.user_item_matrix.index) > 0):
                # Обучаем с нуля
                engine.train_deep_model(epochs=5, batch_size=32)

                # Получаем рекомендации
                recommendations = engine.recommend_for_user(user.id, top_n=15)

                # Сохраняем в кэш
                cache.set(cache_key, recommendations, timeout=7200)  # 2 часа

                return recommendations

        except Exception as e:
            print(f"Ошибка при обновлении рекомендаций: {e}")

        return ContentsService.popular_content(10)

    @staticmethod
    def update_all_users_recommendations():
        """Обновляет рекомендации для всех пользователей (для cron задачи)"""
        from django.contrib.auth.models import User

        users = User.objects.all()
        for user in users:
            print(f"Обновление рекомендаций для пользователя {user.id}...")
            RecommendationUpdater.update_recommendations_for_user(user)