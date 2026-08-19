from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [("study_workspace", "0002_remove_studyresource_unique_topic_youtube_video_and_more"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name="studynote", name="range_end_seconds", field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="studynote", name="source", field=models.CharField(choices=[("manual", "Manual"), ("ai", "AI generated")], default="manual", max_length=20)),
        migrations.CreateModel(
            name="VideoTranscript",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("language", models.CharField(default="en", max_length=16)),
                ("source", models.CharField(choices=[("manual", "Manual import"), ("youtube_authorized", "Authorized YouTube captions"), ("provider", "Transcript provider")], default="manual", max_length=30)),
                ("full_text", models.TextField()), ("segments", models.JSONField(blank=True, default=list)), ("checksum", models.CharField(max_length=64)),
                ("imported_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="imported_video_transcripts", to=settings.AUTH_USER_MODEL)),
                ("resource", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="transcript", to="study_workspace.studyresource")),
            ],
        ),
        migrations.CreateModel(
            name="AINoteGeneration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("mode", models.CharField(choices=[("full", "Full video"), ("range", "Timestamp range")], max_length=20)),
                ("start_seconds", models.PositiveIntegerField(default=0)), ("end_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("provider", models.CharField(default="openai", max_length=30)), ("model", models.CharField(max_length=120)),
                ("status", models.CharField(choices=[("processing", "Processing"), ("succeeded", "Succeeded"), ("failed", "Failed")], default="processing", max_length=20)),
                ("input_tokens", models.PositiveIntegerField(default=0)), ("output_tokens", models.PositiveIntegerField(default=0)), ("error_code", models.CharField(blank=True, max_length=80)),
                ("note", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ai_generation", to="study_workspace.studynote")),
                ("resource", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_note_generations", to="study_workspace.studyresource")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_note_generations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "indexes": [models.Index(fields=["user", "resource", "-created_at"], name="study_ai_user_resource_idx")]},
        ),
    ]
