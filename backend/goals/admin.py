from django.contrib import admin

from .models import LearningGoal


@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "status", "priority", "target_date")
    list_filter = ("category", "status", "priority")
    search_fields = ("title", "owner__email")

