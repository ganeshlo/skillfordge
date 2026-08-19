from django.urls import path

from .views import (
    MilestoneCreateView,
    MilestoneDetailView,
    ModuleCreateView,
    PhaseCreateView,
    ResourceCreateView,
    RoadmapDetailView,
    RoadmapListCreateView,
    TopicCreateView,
    TopicProgressView,
)

urlpatterns = [
    path("roadmaps/", RoadmapListCreateView.as_view(), name="roadmap-list"),
    path("roadmaps/<uuid:roadmap_id>/", RoadmapDetailView.as_view(), name="roadmap-detail"),
    path("roadmaps/<uuid:roadmap_id>/phases/", PhaseCreateView.as_view(), name="roadmap-phase-create"),
    path("roadmaps/<uuid:roadmap_id>/milestones/", MilestoneCreateView.as_view(), name="roadmap-milestone-create"),
    path("roadmap-milestones/<uuid:milestone_id>/", MilestoneDetailView.as_view(), name="roadmap-milestone-detail"),
    path("roadmap-phases/<uuid:phase_id>/modules/", ModuleCreateView.as_view(), name="roadmap-module-create"),
    path("roadmap-modules/<uuid:module_id>/topics/", TopicCreateView.as_view(), name="roadmap-topic-create"),
    path("roadmap-topics/<uuid:topic_id>/resources/", ResourceCreateView.as_view(), name="roadmap-resource-create"),
    path("roadmap-topics/<uuid:topic_id>/progress/", TopicProgressView.as_view(), name="roadmap-topic-progress"),
]
