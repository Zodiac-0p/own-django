from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Movie

User = get_user_model()


# ============================
# ✅ USER SERIALIZER
# ============================
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        email = validated_data.get("email")
        username = validated_data.get("username")
        password = validated_data.get("password")

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password
        )
        return user


# ============================
# 🎬 MOVIE SERIALIZER (FULL URL)
# ============================
class MovieSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "description",
            "view_count",
            "thumbnail_url",
            "video_url",
        ]
        read_only_fields = ["id"]

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        if obj.thumbnail_url and hasattr(obj.thumbnail_url, "url"):
            url = obj.thumbnail_url.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_video_url(self, obj):
        request = self.context.get("request")
        if obj.video_url and hasattr(obj.video_url, "url"):
            url = obj.video_url.url
            return request.build_absolute_uri(url) if request else url
        return None
