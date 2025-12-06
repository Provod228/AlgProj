from django.db.models import Sum, Avg, Count

from ContentApp.services.django_setap import configure_django

configure_django()
from django.contrib.auth.models import User
from ContentApp.models import Content, Rating, CategoryContent, Favorite


class ContentsService:
    @staticmethod
    def get_all_content():
        return Content.objects.all()

    @staticmethod
    def get_non_favorite_content(user: User):
        if not user.is_authenticated:
            return ContentsService.get_all_content()
        return Content.objects.filter(is_published=True).exclude(favorited_by__user=user).order_by('-created_at')

    @staticmethod
    def get_favorite_content(user: User):
        if not user.is_authenticated:
            return ContentsService.get_all_content()
        return Content.objects.filter(is_published=True, favorited_by__user=user).order_by('-created_at')

    @staticmethod
    def get_content_per_user():
        return Favorite.objects.select_related('user', 'content')

    @staticmethod
    def rec_content(per):
        return Content.objects.filter(id__in=per)

    @staticmethod
    def popular_content(top_n):
        try:
            return Content.objects.annotate(
                num_likes=Count('contentlike'),  # Исправлено: правильное имя связи
                avg_rating=Avg('ratings__rating')  # Исправлено: правильное имя связи для рейтингов
            ).order_by('-num_likes', '-avg_rating')[:top_n]
        except Exception:
            return Content.objects.annotate(
                avg_rating=Avg('ratings__rating')
            ).order_by('-avg_rating')[:top_n]


class ContentService:
    @staticmethod
    def get_content_rating(content: Content):
        return Rating.objects.filter(
        content=content
    ).aggregate(avg_rating=Avg('rating'))['avg_rating']

    @staticmethod
    def get_rating(user: User, content: Content):
        rating_obj = Rating.objects.filter(author=user, content=content).first()
        return rating_obj.rating if rating_obj else None

    @staticmethod
    def get_real_content_category(content: Content):
        categories_data = CategoryContent.objects.filter(
            content=content
        ).values(
            'category__name', 'category__id'
        ).annotate(
            category_vote_sum=Sum('vote')
        )

        if not categories_data:
            return {}

        total_vote_sum = sum(
            item['category_vote_sum'] or 0 for item in categories_data if item['category_vote_sum'] > 0)

        categories_vote = {}
        for category in categories_data:
            category_vote_value = category['category_vote_sum'] or 0
            precent_category = round(category_vote_value / total_vote_sum, 4) if total_vote_sum > 0 else 0
            if precent_category > 0:
                categories_vote[category['category__name']] = precent_category

        return categories_vote

