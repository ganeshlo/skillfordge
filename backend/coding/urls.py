from django.urls import path
from .views import (
    CodingCapabilitiesView,
    CodingProjectDetailView,
    CodingProjectListCreateView,
    ExecutionJobCancelView,
    ExecutionJobDetailView,
    ExecutionJobListCreateView,
    ProjectFileCreateView,
    ProjectFileDetailView,
    ProjectFileRevisionListView,
)

urlpatterns = [
    path("coding/capabilities/", CodingCapabilitiesView.as_view(), name="coding-capabilities"),
    path("coding/projects/", CodingProjectListCreateView.as_view(), name="coding-project-list"),
    path("coding/projects/<uuid:project_id>/", CodingProjectDetailView.as_view(), name="coding-project-detail"),
    path("coding/projects/<uuid:project_id>/files/", ProjectFileCreateView.as_view(), name="coding-file-create"),
    path("coding/files/<uuid:file_id>/", ProjectFileDetailView.as_view(), name="coding-file-detail"),
    path("coding/files/<uuid:file_id>/revisions/", ProjectFileRevisionListView.as_view(), name="coding-file-revisions"),
    path("coding/executions/", ExecutionJobListCreateView.as_view(), name="coding-execution-list"),
    path("coding/executions/<uuid:job_id>/", ExecutionJobDetailView.as_view(), name="coding-execution-detail"),
    path("coding/executions/<uuid:job_id>/cancel/", ExecutionJobCancelView.as_view(), name="coding-execution-cancel"),
]
