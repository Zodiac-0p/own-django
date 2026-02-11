from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from OTT.models import UserActivity
class ActiveUserMiddleware:
    """
    Update the user's last_seen every time they make an authenticated request.
    If the user is inactive, log them out and show a message.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ✅ Check if user is authenticated
        if request.user.is_authenticated:
            # Example: log out inactive users and show message
            if not request.user.is_active:
                logout(request)
                messages.success(request, "Logged out successfully.")

            # ✅ Update last_seen for active users
            else:
                try:
                    activity = request.user.activity
                    activity.last_seen = timezone.now()
                    activity.save(update_fields=['last_seen'])
                except UserActivity.DoesNotExist:
                    UserActivity.objects.create(user=request.user, last_seen=timezone.now())

        # ✅ Continue to next middleware / view
        response = self.get_response(request)
        return response

class DisableCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

class DisableClientSideCachingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # apply to authenticated pages
        if request.user.is_authenticated:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response
    

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            try:
                # only if your User model has last_seen
                user.last_seen = timezone.now()
                user.save(update_fields=["last_seen"])
            except Exception:
                # don't kill the whole site if DB/table/field isn't ready
                pass

        return response
