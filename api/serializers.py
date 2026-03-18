from rest_framework import serializers
from posts.models import Hello

class Hello_serializer(serializers.ModelSerializer):
    class Meta:
        model = Hello
        fields = ['hello_world']
