from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ContentSerializer
from .services.data_get import ContentsService


# Create your views here.


class ContentView(APIView):
    serializer_class = ContentSerializer

    def get(self, request):
        contents = ContentsService.get_non_favorite_content(request.user)
        serializer = self.serializer_class(contents, many=True)
        return Response(serializer.data)