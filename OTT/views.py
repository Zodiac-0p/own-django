from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.admin.views.decorators import staff_member_required
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Movie
from .serializers import UserSerializer, MovieSerializer


User = get_user_model()


# =============================
# ✅ CACHE HELPERS (Back button fix)
# =============================
def no_cache(view_func):
    """
    Prevent browser caching so back-button won't show protected pages after logout.
    """
    return cache_control(no_cache=True, no_store=True, must_revalidate=True, max_age=0)(view_func)


# =============================
# 🌍 LANDING
# =============================
def landing_page(request):
    if request.user.is_authenticated:
        # If admin/staff -> dashboard, else -> user browse (you can change)
        return redirect("home")
    return render(request, "landing_page.html")


# =============================
# ✅ AUTH (Template Views)
# =============================
def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        try:
            User.objects.create_user(email=email, username=username, password=password)
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect("register")

    return render(request, "register.html")


@login_required(login_url="login")
@no_cache
def home(request):
    return render(request, "home.html")

@login_required(login_url="login")
@staff_member_required(login_url="login")
@never_cache
def user_details(request):
    users = User.objects.select_related("activity").all()
    return render(request, "UserDetails.html", {"users": users})


def login_view(request):
    # If already logged in, go home (prevents going back to login)
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect("home")

        messages.error(request, "Invalid credentials")
        return redirect("login")

    return render(request, "OTT/login.html")


@require_POST
@login_required(login_url="login")
@no_cache
def logout_view(request):
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect("login")


@no_cache
def change_password(request):
    """
    Works as:
    - Logged in user: change using old password
    - Logged out user: "forgot password" by email (basic)
    """
    if request.method == "POST":

        # Logged in user change
        if request.user.is_authenticated:
            old_password = request.POST.get("old_password", "")
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            user = request.user

            if not user.check_password(old_password):
                messages.error(request, "Old password is incorrect!")
                return redirect("change_password")

        # Forgot password by email
        else:
            email = request.POST.get("email", "").strip()
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            if not email:
                messages.error(request, "Email is required!")
                return redirect("change_password")

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Email not found!")
                return redirect("change_password")

        # Common validation
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match!")
            return redirect("change_password")

        user.set_password(new_password)
        user.save()

        # ✅ Important: clear session and force login again
        logout(request)
        messages.success(request, "Password changed successfully. Please login again.")
        return redirect("login")

    return render(request, "Changepassword.html")



# =============================
# ✅ ADMIN MOVIE MANAGEMENT (Django templates)
# =============================
@login_required(login_url="login")
@staff_member_required(login_url="login")
@no_cache
def dashboard(request):
    user_count = User.objects.count()
    movie_count = Movie.objects.count()
    return render(request, "count.html", {"user_count": user_count, "movie_count": movie_count})


@login_required(login_url="login")
@staff_member_required(login_url="login")
@no_cache
def movie_list(request):
    movies = Movie.objects.all()
    return render(request, "MovieList.html", {"movies": movies})


@login_required(login_url="login")
@staff_member_required(login_url="login")
@no_cache
def create_movie(request):
    if request.method == "POST":
        title = request.POST.get("movie_name")
        description = request.POST.get("movie_description")
        thumbnail = request.FILES.get("movie_image")
        video = request.FILES.get("movie_video")

        Movie.objects.create(
            title=title,
            description=description,
            thumbnail_url=thumbnail,
            video_url=video
        )
        return redirect("movie_list")

    return render(request, "createMovies.html")


@login_required(login_url="login")
@staff_member_required(login_url="login")
@no_cache
def edit_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":
        movie.title = request.POST.get("title", movie.title)
        movie.description = request.POST.get("description", movie.description)

        if "thumbnail_url" in request.FILES:
            movie.thumbnail_url = request.FILES["thumbnail_url"]

        if "video_url" in request.FILES:
            movie.video_url = request.FILES["video_url"]

        movie.save()
        return redirect("movie_list")

    return render(request, "edit.html", {"movie": movie})


@login_required(login_url="login")
@staff_member_required(login_url="login")
@no_cache
def delete_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    movie.delete()
    return redirect("movie_list")


# =============================
# ✅ API (React uses these) — Session Auth + CSRF
# =============================

class CSRFTokenAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # This sets the csrftoken cookie in browser + returns token
        return Response({"csrfToken": get_token(request)})


class RegisterUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🚫 If staff, do NOT log them in via API
        if user.is_staff:
            return Response(
                {
                    "error": "admin_redirect",
                    "message": "Admins must login from Django panel."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        login(request, user)

        return Response(
            {
                "message": "Login successful",
                "email": user.email,
            },
            status=status.HTTP_200_OK
        )



class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "email": request.user.email,
            "username": request.user.username,
            "is_staff": request.user.is_staff,
        }, status=status.HTTP_200_OK)


class MovieListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        movies = Movie.objects.all()
        serializer = MovieSerializer(movies, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)



class MovieDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        serializer = MovieSerializer(movie, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "Old and new password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ check old password
        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ set new password
        user.set_password(new_password)
        user.save()

        # Optional: keep user logged in
        update_session_auth_hash(request, user)

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )
        

def home_movies_api(request):
    qs = Movie.objects.order_by("-id")[:3]

    movies = []
    for m in qs:
        thumb_val = getattr(m, "thumbnail_url", None)

        # ✅ Convert ImageFieldFile to URL string
        thumb = ""
        if thumb_val:
            try:
                # If it's ImageFieldFile/FileField -> has .url
                thumb = request.build_absolute_uri(thumb_val.url)
            except Exception:
                # If it is already a string path or full url
                thumb = str(thumb_val)
                if thumb and not thumb.startswith("http"):
                    if not thumb.startswith("/"):
                        thumb = "/" + thumb
                    thumb = request.build_absolute_uri(thumb)

        movies.append({
            "id": m.id,
            "title": getattr(m, "title", ""),
            "description": (getattr(m, "description", "") or "")[:120],
            "thumbnail": thumb,
        })

    return JsonResponse({"movies": movies})

@login_required
def users_status_api(request):
    users = User.objects.select_related("activity").all()

    data = []
    for u in users:
        # activity always exists because of signal, but safe anyway
        online = u.activity.is_online() if hasattr(u, "activity") else False

        data.append({
            "id": u.id,
            "username": u.username or "",
            "email": u.email,
            "is_online": online
        })

    return JsonResponse({"users": data})

@login_required
@login_required
@never_cache
def profile_me(request):
    u = request.user
    return JsonResponse({
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "is_staff": u.is_staff,
        "phone": getattr(u, "phone", "") or "",
        "hobbies": getattr(u, "hobbies", "") or "",
        "bio": getattr(u, "bio", "") or "",
        "profile_pic": u.profile_pic.url if getattr(u, "profile_pic", None) else "",
    })
    
@require_POST
@login_required
@never_cache
def profile_update(request):
    u = request.user

    if "phone" in request.POST: u.phone = request.POST.get("phone", "")
    if "hobbies" in request.POST: u.hobbies = request.POST.get("hobbies", "")
    if "bio" in request.POST: u.bio = request.POST.get("bio", "")

    if "profile_pic" in request.FILES:
        u.profile_pic = request.FILES["profile_pic"]

    u.save()
    u.refresh_from_db()

    return JsonResponse({
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "is_staff": u.is_staff,
        "phone": u.phone or "",
        "hobbies": u.hobbies or "",
        "bio": u.bio or "",
        "profile_pic": u.profile_pic.url if u.profile_pic else "",
    })
    
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"ok": True})

@require_POST
@login_required
def profile_delete_pic(request):
    u = request.user
    if u.profile_pic:
        u.profile_pic.delete(save=False)
        u.profile_pic = None
        u.save()

    return JsonResponse({
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "is_staff": u.is_staff,
        "phone": u.phone or "",
        "hobbies": u.hobbies or "",
        "bio": u.bio or "",
        "profile_pic": "",
    })