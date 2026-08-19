from django.urls import path
from .views import OrganizationListCreateView, OrganizationMemberListView

urlpatterns = [
    path("organizations/", OrganizationListCreateView.as_view(), name="organization-list"),
    path("organizations/<uuid:organization_id>/members/", OrganizationMemberListView.as_view(), name="organization-members"),
]

