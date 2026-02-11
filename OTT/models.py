from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver


# -------------------------
# Custom user manager
# -------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, username=None):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, username=None):
        user = self.create_user(email=email, password=password, username=username)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


# -------------------------
# Custom User model
# -------------------------
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    profile_pic = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    hobbies = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)   # your custom flag
    is_staff = models.BooleanField(default=False)   # required for admin access
    is_blocked = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    # Optional permission helpers
    def has_perm(self, perm, obj=None):
        return self.is_admin or self.is_superuser

    def has_module_perms(self, app_label):
        return True


# -------------------------
# Movie related models
# -------------------------
class Movie(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    view_count = models.IntegerField(default=0)
    thumbnail_url = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    video_url = models.FileField(upload_to="videos/", blank=True, null=True)

    def __str__(self):
        return self.title


class ViewHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="view_histories")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="view_histories")
    date = models.DateTimeField(auto_now_add=True)


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist_items")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="watchlisted_by")

    class Meta:
        unique_together = ("user", "movie")


# -------------------------
# Online / activity tracking
# -------------------------
class UserActivity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="activity")
    last_seen = models.DateTimeField(default=timezone.now)

    @property
    def is_online(self):
        return timezone.now() - self.last_seen < timedelta(seconds=5)

    def __str__(self):
        return f"{self.user.email} - {'Online' if self.is_online() else 'Offline'}"


# -------------------------
# Signal: create activity automatically
# -------------------------
@receiver(post_save, sender=User)
def create_user_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(user=instance)
