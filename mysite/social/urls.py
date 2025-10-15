from django.urls import path
from . import views


app_name = 'social'


urlpatterns = [
path('', views.feed, name='feed'),
path('signup/', views.signup_view, name='signup'),
path('login/', views.login_view, name='login'),
path('accounts/login/', views.login_view, name='accounts_login'),
path('logout/', views.logout_view, name='logout'),


path('profile/<str:username>/', views.profile_view, name='profile'),
path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),


path('post/create/', views.create_post, name='create_post'),
path('post/<int:post_id>/', views.post_detail, name='post_detail'),


# path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
# path('user/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
]