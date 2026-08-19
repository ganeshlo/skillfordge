from django.urls import path
from .views import ForgotPasswordView, LoginView, LogoutView, RefreshView, RegisterView, ResetPasswordView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("token/", LoginView.as_view(), name="auth-token"),
    path("token/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("token/revoke/", LogoutView.as_view(), name="auth-logout"),
    path("password/forgot/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("password/reset/", ResetPasswordView.as_view(), name="auth-reset-password"),
]
