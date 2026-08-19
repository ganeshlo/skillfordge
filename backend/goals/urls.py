from django.urls import path

from .views import AnalyticsView, GoalDetailView, GoalListCreateView

urlpatterns = [
    path("goals/", GoalListCreateView.as_view(), name="goal-list"),
    path("goals/<uuid:goal_id>/", GoalDetailView.as_view(), name="goal-detail"),
    path("analytics/", AnalyticsView.as_view(), name="learning-analytics"),
]

