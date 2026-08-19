from django.db import migrations, models


def apply_offer_prices(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code="pro").update(
        amount_minor=100,
        compare_at_amount_minor=99900,
        description="Limited-time Pro access for serious learners.",
    )
    Plan.objects.filter(code="enterprise").update(
        amount_minor=200,
        compare_at_amount_minor=499000,
        description="Limited-time Enterprise access for teams.",
    )


def remove_offer_prices(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code="pro").update(
        amount_minor=99900,
        compare_at_amount_minor=None,
        description="Advanced learning, coding, and AI support.",
    )
    Plan.objects.filter(code="enterprise").update(
        amount_minor=499900,
        compare_at_amount_minor=None,
        description="Governed learning for teams and organizations.",
    )


class Migration(migrations.Migration):
    dependencies = [("billing", "0002_seed_plans")]
    operations = [
        migrations.AddField(
            model_name="plan",
            name="compare_at_amount_minor",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(apply_offer_prices, remove_offer_prices),
    ]
