import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coding", "0001_initial"),
        ("roadmaps", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="LearningGoal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("career", "Career"), ("skill", "Skill"), ("project", "Project"), ("certification", "Certification"), ("habit", "Habit")], default="skill", max_length=24)),
                ("status", models.CharField(choices=[("not_started", "Not started"), ("in_progress", "In progress"), ("completed", "Completed"), ("paused", "Paused")], default="not_started", max_length=24)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium", max_length=12)),
                ("target_value", models.PositiveIntegerField(default=100, validators=[django.core.validators.MinValueValidator(1)])),
                ("current_value", models.PositiveIntegerField(default=0)),
                ("unit", models.CharField(default="percent", max_length=40)),
                ("target_date", models.DateField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="learning_goals", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="goals", to="coding.codingproject")),
                ("roadmap", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="goals", to="roadmaps.roadmap")),
            ],
            options={"ordering": ["status", "-priority", "target_date", "-updated_at"]},
        ),
        migrations.AddIndex(model_name="learninggoal", index=models.Index(fields=["owner", "status", "target_date"], name="goals_learn_owner_i_6d3b2e_idx")),
    ]
