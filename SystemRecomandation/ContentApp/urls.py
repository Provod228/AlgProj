from django.urls import path

from ContentApp.views import ContentView

urlpatterns = [
    path('data/', ContentView.as_view(), name='data'),
]