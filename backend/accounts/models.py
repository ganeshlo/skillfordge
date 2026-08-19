from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.models import TimestampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("A superuser must have staff and superuser privileges")
        return self.create_user(email, password, **extra_fields)


class User(TimestampedModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email


class UserProfile(TimestampedModel):
    class Experience(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    professional_role = models.CharField(max_length=80, blank=True)
    experience_level = models.CharField(max_length=20, choices=Experience.choices, blank=True)
    career_goal = models.CharField(max_length=120, blank=True)
    learning_goals = models.JSONField(default=list, blank=True)
    current_skills = models.JSONField(default=list, blank=True)
    target_skills = models.JSONField(default=list, blank=True)
    preferred_languages = models.JSONField(default=list, blank=True)
    daily_minutes = models.PositiveSmallIntegerField(default=30)
    weekly_target_minutes = models.PositiveIntegerField(default=210)
    target_deadline = models.DateField(null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)


class UserPreference(TimestampedModel):
    class Theme(models.TextChoices):
        SYSTEM = "system", "System"
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"

    user = models.OneToOneField(User, related_name="preferences", on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.SYSTEM)
    timezone = models.CharField(max_length=64, default="UTC")
    learning_style = models.CharField(max_length=80, blank=True)
    email_notifications = models.BooleanField(default=True)

