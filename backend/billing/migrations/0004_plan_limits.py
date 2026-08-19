from django.db import migrations, models


def apply_plan_limits(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code="free").update(limits={"coding_projects": 3})
    Plan.objects.filter(code__in=["pro", "enterprise"]).update(limits={"coding_projects": None})


def remove_plan_limits(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.all().update(limits={})


class Migration(migrations.Migration):
    dependencies = [("billing", "0003_offer_prices")]
    operations = [
        migrations.AddField(
            model_name="plan",
            name="limits",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(apply_plan_limits, remove_plan_limits),
    ]
