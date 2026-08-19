from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Organization, OrganizationMembership
from .services import create_organization


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMembership
        fields = ["id", "user", "role", "status", "joined_at"]

    @extend_schema_field(serializers.DictField())
    def get_user(self, obj):
        return {"id": obj.user_id, "full_name": obj.user.full_name, "email": obj.user.email}


class OrganizationSerializer(serializers.ModelSerializer):
    current_role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "current_role", "created_at"]
        read_only_fields = ["id", "current_role", "created_at"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_current_role(self, obj):
        membership = next((item for item in obj.memberships.all() if item.user_id == self.context["request"].user.id), None)
        return membership.role if membership else None

    def create(self, validated_data):
        return create_organization(user=self.context["request"].user, request=self.context["request"], **validated_data)
