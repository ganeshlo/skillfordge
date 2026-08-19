from django.urls import path
from . import views

urlpatterns = [
    path("health/live/", views.LivenessView.as_view(), name="health-live"),
    path("health/ready/", views.ReadinessView.as_view(), name="health-ready"),
]
