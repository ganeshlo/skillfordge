from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied

from core.responses import api_response
from .models import Organization, OrganizationMembership
from .policies import ADMIN_ROLES, active_membership
from .serializers import MembershipSerializer, OrganizationSerializer


class OrganizationListCreateView(generics.GenericAPIView):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__status=OrganizationMembership.Status.ACTIVE,
            deleted_at__isnull=True,
        ).prefetch_related("memberships")

    def get(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(serializer.data, request=request)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        output = self.get_serializer(organization)
        return api_response(output.data, request=request, status=status.HTTP_201_CREATED)


class OrganizationMemberListView(generics.GenericAPIView):
    serializer_class = MembershipSerializer

    def get(self, request, organization_id):
        organization = Organization.objects.filter(id=organization_id, deleted_at__isnull=True).first()
        if not organization:
            raise NotFound("Organization not found.")
        membership = active_membership(user=request.user, organization=organization)
        if not membership or membership.role not in ADMIN_ROLES:
            raise PermissionDenied("You cannot view this organization's members.")
        members = organization.memberships.select_related("user").order_by("user__full_name")
        return api_response(self.get_serializer(members, many=True).data, request=request)

