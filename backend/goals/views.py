from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView

from coding.models import CodingProject
from core.responses import api_response
from roadmaps.models import Roadmap, TopicProgress
from study_workspace.models import StudySession

from .models import LearningGoal
from .serializers import LearningGoalSerializer


class GoalListCreateView(GenericAPIView):
    serializer_class = LearningGoalSerializer

    def get(self, request):
        goals = LearningGoal.objects.filter(owner=request.user, deleted_at__isnull=True).select_related("roadmap", "project")
        requested_status = request.query_params.get("status")
        if requested_status in LearningGoal.Status.values:
            goals = goals.filter(status=requested_status)
        return api_response(self.get_serializer(goals, many=True).data, request=request)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        goal = serializer.save(owner=request.user)
        return api_response(self.get_serializer(goal).data, request=request, status=status.HTTP_201_CREATED)


class GoalDetailView(GenericAPIView):
    serializer_class = LearningGoalSerializer

    def get_object(self):
        return get_object_or_404(LearningGoal.objects.filter(owner=self.request.user, deleted_at__isnull=True).select_related("roadmap", "project"), id=self.kwargs["goal_id"])

    def patch(self, request, goal_id):
        goal = self.get_object()
        serializer = self.get_serializer(goal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        next_status = serializer.validated_data.get("status", goal.status)
        serializer.save(completed_at=timezone.now() if next_status == LearningGoal.Status.COMPLETED else None)
        return api_response(serializer.data, request=request)

    def delete(self, request, goal_id):
        goal = self.get_object()
        goal.deleted_at = timezone.now()
        goal.save(update_fields=["deleted_at", "updated_at"])
        return api_response({"deleted": True}, request=request)


class AnalyticsView(GenericAPIView):
    def get(self, request):
        today = timezone.localdate()
        start = today - timedelta(days=6)
        sessions = StudySession.objects.filter(user=request.user, started_at__date__gte=start)
        activity_rows = sessions.annotate(day=TruncDate("started_at")).values("day").annotate(minutes=Sum("active_seconds"), sessions=Count("id")).order_by("day")
        by_day = {row["day"]: row for row in activity_rows}
        weekly = [{"date": start + timedelta(days=index), "minutes": round((by_day.get(start + timedelta(days=index), {}).get("minutes") or 0) / 60), "sessions": by_day.get(start + timedelta(days=index), {}).get("sessions", 0)} for index in range(7)]

        roadmaps = Roadmap.objects.filter(owner=request.user, deleted_at__isnull=True).annotate(
            topic_count=Count("phases__modules__topics", distinct=True),
            completed_topic_count=Count("phases__modules__topics__progress_records", filter=Q(phases__modules__topics__progress_records__user=request.user, phases__modules__topics__progress_records__status=TopicProgress.Status.COMPLETED), distinct=True),
        )
        roadmap_rows = [{"id": item.id, "title": item.title, "status": item.status, "topic_count": item.topic_count, "completed_topic_count": item.completed_topic_count, "progress_percentage": round(item.completed_topic_count / item.topic_count * 100) if item.topic_count else 0} for item in roadmaps]
        goals = LearningGoal.objects.filter(owner=request.user, deleted_at__isnull=True)
        total_topics = sum(item["topic_count"] for item in roadmap_rows)
        completed_topics = sum(item["completed_topic_count"] for item in roadmap_rows)
        total_minutes = StudySession.objects.filter(user=request.user).aggregate(total=Sum("active_seconds"))["total"] or 0
        return api_response({
            "overview": {
                "total_study_minutes": round(total_minutes / 60), "weekly_study_minutes": sum(item["minutes"] for item in weekly),
                "completed_topics": completed_topics, "total_topics": total_topics,
                "active_roadmaps": roadmaps.filter(status=Roadmap.Status.ACTIVE).count(),
                "projects": CodingProject.objects.filter(owner=request.user, deleted_at__isnull=True).count(),
                "completed_goals": goals.filter(status=LearningGoal.Status.COMPLETED).count(), "total_goals": goals.count(),
            },
            "weekly_activity": weekly,
            "roadmaps": roadmap_rows,
            "goal_breakdown": [{"status": value["status"], "count": value["count"]} for value in goals.values("status").annotate(count=Count("id")).order_by("status")],
        }, request=request)
