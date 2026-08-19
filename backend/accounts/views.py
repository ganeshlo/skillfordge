from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.responses import api_response
from .models import User
from .passwords import request_password_reset, reset_password
from .serializers import EmptySerializer, EmailTokenObtainPairSerializer, ForgotPasswordSerializer, MeUpdateSerializer, OnboardingSerializer, RegisterSerializer, ResetPasswordSerializer, UserSerializer


def set_refresh_cookie(response, token):
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE,
        str(token),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite="Lax",
        path="/api/v1/auth/",
    )


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return api_response(UserSerializer(user).data, request=request, status=status.HTTP_201_CREATED)


class LoginView(GenericAPIView):
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = EmailTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = api_response({"access": serializer.validated_data["access"]}, request=request)
        set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class RefreshView(GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_refresh"

    def post(self, request):
        token_value = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        if not token_value:
            raise AuthenticationFailed("A refresh session is required.")
        try:
            old = RefreshToken(token_value)
            user_id = old[settings.SIMPLE_JWT.get("USER_ID_CLAIM", "user_id")]
            old.blacklist()
            new = RefreshToken.for_user(User.objects.get(id=user_id, is_active=True))
        except (TokenError, KeyError, User.DoesNotExist):
            raise AuthenticationFailed("The refresh session is invalid or expired.")
        response = api_response({"access": str(new.access_token)}, request=request)
        set_refresh_cookie(response, new)
        return response


class LogoutView(GenericAPIView):
    serializer_class = EmptySerializer
    def post(self, request):
        token_value = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        if token_value:
            try:
                RefreshToken(token_value).blacklist()
            except TokenError:
                pass
        response = api_response({"logged_out": True}, request=request)
        response.delete_cookie(settings.JWT_REFRESH_COOKIE, path="/api/v1/auth/")
        return response


class ForgotPasswordView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_request"
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_url = request_password_reset(email=serializer.validated_data["email"], request=request)
        data = {"message": "If an account exists for that email, a reset link has been sent."}
        if settings.DEBUG and reset_url:
            data["debug_reset_url"] = reset_url
        return api_response(data, request=request)


class ResetPasswordView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_reset"
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_password(request=request, **serializer.validated_data)
        return api_response({"message": "Your password has been reset. You can now sign in."}, request=request)


class MeView(GenericAPIView):
    serializer_class = UserSerializer
    def get(self, request):
        return api_response(UserSerializer(request.user).data, request=request)

    def patch(self, request):
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return api_response(UserSerializer(user).data, request=request)


class OnboardingView(GenericAPIView):
    serializer_class = OnboardingSerializer
    def post(self, request):
        serializer = OnboardingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response(UserSerializer(request.user).data, request=request)
