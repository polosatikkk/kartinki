from rest_framework import generics
from posts.models import Hello
from api.serializers import Hello_serializer

# Create your views here.

class hello_view(generics.ListAPIView):
    queryset = Hello.objects.all()
    serializer_class = Hello_serializer
