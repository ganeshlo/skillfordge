from django.urls import path
from .views import MeView, OnboardingView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/onboarding/", OnboardingView.as_view(), name="onboarding"),
]

