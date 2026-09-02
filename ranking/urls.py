from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "ranking"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("post/<int:pk>/", views.ScorePostDetailView.as_view(), name="score_post_detail"),
    path("login/", auth_views.LoginView.as_view(template_name="ranking/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="ranking:home"), name="logout"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("post/new/", views.ScorePostCreateView.as_view(), name="score_post_create"),
    path("mypage/", views.MyPageView.as_view(), name="mypage"),
    path("post/<int:pk>/delete/", views.ScorePostDeleteView.as_view(), name="score_post_delete"),
]