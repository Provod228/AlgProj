from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # API Endpoints
    path('api/contents/', views.ContentView.as_view(), name='api_contents'),
    path('api/favorites/', views.FavoriteContentView.as_view(), name='api_favorites'),
    path('api/rate/', views.RatingView.as_view(), name='api_rate'),
    path('api/popular/', views.PopularContentView.as_view(), name='api_popular'),
    path('api/recommendations/', views.RecommendationsView.as_view(), name='api_recommendations'),
    path('api/category-vote/', views.CategoryVoteView.as_view(), name='api_category_vote'),

    # Auth API
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    path('api/login/', views.LoginView.as_view(), name='api_login'),
    path('api/logout/', views.LogoutView.as_view(), name='api_logout'),
    path('api/profile/', views.UserProfileView.as_view(), name='api_profile'),

    # HTML Pages - Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # HTML Pages - Content
    path('', views.content_list_view, name='content_list'),
    path('favorites/', views.favorite_content_view, name='favorites'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('popular/', views.popular_content_view, name='popular'),
    path('content/<int:content_id>/', views.content_detail_view, name='content_detail'),

    # Static pages
    path('about/', TemplateView.as_view(template_name='ContentApp/about.html'), name='about'),
    path('help/', TemplateView.as_view(template_name='ContentApp/help.html'), name='help'),
    path('api/refresh-recommendations/', views.RefreshRecommendationsView.as_view(),
         name='api_refresh_recommendations'),
]