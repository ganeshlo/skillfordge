from django.db import migrations


PLANS = [
    {
        "code": "free",
        "name": "Free",
        "description": "Start learning with essential tools.",
        "amount_minor": 0,
        "duration_days": 32700,
        "display_order": 0,
        "features": ["Learning roadmaps", "Study workspace", "Basic notes", "3 code projects"],
    },
    {
        "code": "pro",
        "name": "Pro",
        "description": "Advanced learning, coding, and AI support.",
        "amount_minor": 1000,
        "duration_days": 30,
        "display_order": 1,
        "is_featured": True,
        "features": ["Everything in Free", "Unlimited projects", "AI tutor and quizzes", "Advanced analytics", "Priority execution"],
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "description": "Governed learning for teams and organizations.",
        "amount_minor": 499900,
        "duration_days": 30,
        "display_order": 2,
        "features": ["Everything in Pro", "Organization management", "Team analytics", "Audit logs", "Priority support"],
    },
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    for values in PLANS:
        code = values["code"]
        Plan.objects.update_or_create(code=code, defaults=values)


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]
    operations = [migrations.RunPython(seed_plans, migrations.RunPython.noop)]
