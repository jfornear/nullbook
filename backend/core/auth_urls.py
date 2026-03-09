from django.urls import path

from .views import csrf_view, login_view, logout_view, session_view

urlpatterns = [
    path("csrf/", csrf_view, name="auth-csrf"),
    path("login/", login_view, name="auth-login"),
    path("logout/", logout_view, name="auth-logout"),
    path("session/", session_view, name="auth-session"),
]
