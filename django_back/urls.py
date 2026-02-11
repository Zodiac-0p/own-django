from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from OTT import views
# from django.views.static import serve
# from django.urls import re_path



urlpatterns = [

    # ======================================
    # 🔐 DJANGO ADMIN
    # ======================================
    path('admin/', admin.site.urls),


    # ======================================
    # 🌍 TEMPLATE ROUTES (Django rendered)
    # ======================================
    path('', views.landing_page, name='landing_page'),
    path('home/', views.home, name='home'),

    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),

    path("user-details/", views.user_details, name="user_details"),

    # Admin management pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/create/', views.create_movie, name='create_movie'),
    path('movies/edit/<int:movie_id>/', views.edit_movie, name='edit_movie'),
    path('movies/delete/<int:movie_id>/', views.delete_movie, name='delete_movie'),
    # path('users/', views.user_list, name='user_list'),


    # ======================================
    # 🚀 API ROUTES (React uses these)
    # ======================================
    path('api/csrf/', views.CSRFTokenAPIView.as_view(), name='api_csrf'),
    path('api/register/', views.RegisterUserAPIView.as_view(), name='api_register'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path("api/change-password/", views.ChangePasswordAPIView.as_view(), name="api_change_password"),
    path('api/movies/', views.MovieListAPIView.as_view(), name='api_movie_list'),
    path('api/movies/<int:movie_id>/', views.MovieDetailAPIView.as_view(), name='api_movie_detail'),
    path("api/home-movies/", views.home_movies_api, name="home_movies_api"),
    path("api/users-status/", views.users_status_api, name="users_status_api"),
    # path('api/me/', views.MeAPIView.as_view(), name='api_me'),
    path("api/me/", views.profile_me, name="profile_me"),
    path("api/profile/update/", views.profile_update),
    path("api/csrf/", views.csrf, name="csrf"),
    path("api/profile/delete-pic/", views.profile_delete_pic),
]



# ======================================
# 📂 MEDIA FILES (Development Only)
# ======================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
#     urlpatterns += [
#     # re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
# ]

