from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserPreference, UserProfile
from .services import complete_onboarding, register_user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ["user"]
        read_only_fields = ["id", "created_at", "updated_at", "onboarding_completed_at"]


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ["theme", "timezone", "learning_style", "email_notifications"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    preferences = PreferenceSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "email_verified_at", "profile", "preferences", "created_at"]
        read_only_fields = ["id", "email", "email_verified_at", "created_at"]


class MeUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=160)
    professional_role = serializers.CharField(max_length=80, required=False, allow_blank=True)
    experience_level = serializers.ChoiceField(
        choices=UserProfile.Experience.choices, required=False, allow_blank=True
    )
    career_goal = serializers.CharField(max_length=120, required=False, allow_blank=True)
    daily_minutes = serializers.IntegerField(min_value=10, max_value=720, required=False)
    weekly_target_minutes = serializers.IntegerField(min_value=30, max_value=5040, required=False)
    theme = serializers.ChoiceField(choices=UserPreference.Theme.choices, required=False)

    def update(self, instance, validated_data):
        theme = validated_data.pop("theme", None)
        if "full_name" in validated_data:
            instance.full_name = validated_data.pop("full_name")
            instance.save(update_fields=["full_name", "updated_at"])
        profile = instance.profile
        for field, value in validated_data.items():
            setattr(profile, field, value)
        profile.save()
        if theme is not None:
            preferences, _ = UserPreference.objects.get_or_create(user=instance)
            preferences.theme = theme
            preferences.save(update_fields=["theme", "updated_at"])
        return instance


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=160)
    password = serializers.CharField(write_only=True, min_length=10, validators=[validate_password])

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        return register_user(**validated_data, request=self.context.get("request"))


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {"no_active_account": "The email or password is incorrect."}


class EmptySerializer(serializers.Serializer):
    pass


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=256)
    new_password = serializers.CharField(write_only=True, min_length=10)


class OnboardingSerializer(serializers.Serializer):
    professional_role = serializers.CharField(max_length=80)
    experience_level = serializers.ChoiceField(choices=UserProfile.Experience.choices)
    career_goal = serializers.CharField(max_length=120)
    learning_goals = serializers.ListField(child=serializers.CharField(max_length=120), min_length=1, max_length=10)
    current_skills = serializers.ListField(child=serializers.CharField(max_length=80), max_length=30, required=False)
    target_skills = serializers.ListField(child=serializers.CharField(max_length=80), min_length=1, max_length=30)
    preferred_languages = serializers.ListField(child=serializers.CharField(max_length=40), max_length=20, required=False)
    daily_minutes = serializers.IntegerField(min_value=10, max_value=720)
    weekly_target_minutes = serializers.IntegerField(min_value=30, max_value=5040)
    target_deadline = serializers.DateField(required=False, allow_null=True)
    learning_style = serializers.CharField(max_length=80, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, default="UTC")

    def validate_target_deadline(self, value):
        if value and value < timezone.localdate():
            raise serializers.ValidationError("The target deadline must be in the future.")
        return value

    def save(self, **kwargs):
        return complete_onboarding(
            user=self.context["request"].user,
            validated_data=self.validated_data,
            request=self.context["request"],
        )
