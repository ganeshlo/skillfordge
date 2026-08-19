from rest_framework import serializers


class DashboardOverviewSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    full_name = serializers.CharField()
    professional_role = serializers.CharField(allow_blank=True)
    experience_level = serializers.CharField(allow_blank=True)
    career_goal = serializers.CharField(allow_blank=True)
    profile_completion = serializers.IntegerField(min_value=0, max_value=100)
    onboarding_complete = serializers.BooleanField()
    email_verified = serializers.BooleanField()


class DashboardTargetsSerializer(serializers.Serializer):
    daily_minutes = serializers.IntegerField()
    weekly_target_minutes = serializers.IntegerField()
    target_skills = serializers.ListField(child=serializers.CharField())
    current_skills = serializers.ListField(child=serializers.CharField())
    preferred_languages = serializers.ListField(child=serializers.CharField())


class DashboardOrganizationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    role = serializers.CharField()


class DashboardActivitySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    action = serializers.CharField()
    label = serializers.CharField()
    created_at = serializers.DateTimeField()


class DashboardActionSerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    label = serializers.CharField()
    href = serializers.CharField()
    available = serializers.BooleanField()


class DashboardModuleSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    status = serializers.ChoiceField(choices=["ready", "next", "planned"])
    href = serializers.CharField(allow_null=True)


class DashboardActivityDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    minutes = serializers.IntegerField()
    sessions = serializers.IntegerField()


class DashboardLearningActivitySerializer(serializers.Serializer):
    weekly_minutes = serializers.IntegerField()
    weekly_target_minutes = serializers.IntegerField()
    days = DashboardActivityDaySerializer(many=True)


class DashboardSerializer(serializers.Serializer):
    overview = DashboardOverviewSerializer()
    targets = DashboardTargetsSerializer()
    organizations = DashboardOrganizationSerializer(many=True)
    organization_count = serializers.IntegerField()
    recent_activity = DashboardActivitySerializer(many=True)
    next_action = DashboardActionSerializer()
    learning_activity = DashboardLearningActivitySerializer()
    modules = DashboardModuleSerializer(many=True)
