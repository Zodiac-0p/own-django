from rest_framework import serializers
from .models import Movie, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class MovieSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ["id", "title", "description", "view_count", "thumbnail", "video"]

    def get_thumbnail(self, obj):
        try:
            return obj.thumbnail_url.url if obj.thumbnail_url else ""
        except Exception:
            return ""

    def get_video(self, obj):
        try:
            return obj.video_url.url if obj.video_url else ""
        except Exception:
            return ""
