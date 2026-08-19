from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, UserPreference, UserProfile
from coding.models import CodingProject
from coding.services import create_file
from goals.models import LearningGoal
from organizations.models import Organization, OrganizationMembership
from roadmaps.models import (
    Milestone,
    Resource,
    Roadmap,
    RoadmapModule,
    RoadmapPhase,
    Topic,
    TopicProgress,
)
from study_workspace.models import StudySession


class Command(BaseCommand):
    help = "Create deterministic local-development data. Never run in production."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email="learner@learnos.local",
            defaults={"full_name": "LearnOS Learner"},
        )
        if created:
            user.set_password("LearnOS-local-482!")
            user.save(update_fields=["password"])
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not profile.onboarding_completed_at:
            profile.professional_role = "Developer"
            profile.experience_level = UserProfile.Experience.INTERMEDIATE
            profile.career_goal = "Full-stack engineer"
            profile.learning_goals = ["Build production-ready full-stack applications"]
            profile.current_skills = ["HTML", "CSS", "JavaScript", "Python"]
            profile.target_skills = ["React", "Django", "PostgreSQL", "Docker"]
            profile.preferred_languages = ["Python", "TypeScript"]
            profile.daily_minutes = 60
            profile.weekly_target_minutes = 420
            profile.onboarding_completed_at = timezone.now()
            profile.save()
        UserPreference.objects.get_or_create(user=user)
        organization, _ = Organization.objects.get_or_create(
            slug="learnos-lab",
            defaults={"name": "LearnOS Lab", "created_by": user},
        )
        OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=user,
            defaults={"role": OrganizationMembership.Role.ORG_ADMIN},
        )
        roadmap, _ = Roadmap.objects.get_or_create(
            owner=user,
            title="Full-Stack Engineer Roadmap",
            defaults={
                "description": "A practical path from web foundations to a deployed full-stack project.",
                "career_goal": "Full-stack engineer",
                "visibility": Roadmap.Visibility.PRIVATE,
                "estimated_minutes": 7200,
            },
        )
        phase, _ = RoadmapPhase.objects.get_or_create(roadmap=roadmap, position=0, defaults={"title": "Web foundations"})
        module, _ = RoadmapModule.objects.get_or_create(phase=phase, position=0, defaults={"title": "Modern web essentials", "estimated_minutes": 900})
        topics = [
            ("Semantic HTML", "Build accessible page structure", 0),
            ("Responsive CSS", "Create layouts that adapt across devices", 1),
            ("JavaScript fundamentals", "Use the language confidently in browser applications", 2),
        ]
        for title, objective, position in topics:
            Topic.objects.get_or_create(module=module, position=position, defaults={"title": title, "objective": objective, "estimated_minutes": 180})
        html_topic = Topic.objects.get(module=module, position=0)
        Resource.objects.get_or_create(
            topic=html_topic,
            url="https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content",
            defaults={"title": "MDN: Structuring content with HTML", "resource_type": Resource.Type.ARTICLE},
        )
        roadmap_sections = [
            (1, "Application engineering", [
                ("Frontend architecture", [("React component design", "Build composable, accessible interfaces", 0), ("State and server data", "Manage local and remote state deliberately", 1)]),
                ("Backend APIs", [("Django REST APIs", "Design secure, versioned HTTP APIs", 0), ("PostgreSQL data modeling", "Create reliable relational schemas and queries", 1)]),
            ]),
            (2, "Production delivery", [
                ("Quality and operations", [("Automated testing", "Protect critical behavior with a balanced test suite", 0), ("Docker and deployment", "Package and operate services consistently", 1), ("Observability", "Use logs and metrics to diagnose production behavior", 2)]),
            ]),
        ]
        for phase_position, phase_title, modules in roadmap_sections:
            extra_phase, _ = RoadmapPhase.objects.get_or_create(roadmap=roadmap, position=phase_position, defaults={"title": phase_title})
            for module_position, (module_title, module_topics) in enumerate(modules):
                extra_module, _ = RoadmapModule.objects.get_or_create(phase=extra_phase, position=module_position, defaults={"title": module_title, "estimated_minutes": 720})
                for topic_title, objective, topic_position in module_topics:
                    Topic.objects.get_or_create(module=extra_module, position=topic_position, defaults={"title": topic_title, "objective": objective, "difficulty": Topic.Difficulty.INTERMEDIATE, "estimated_minutes": 180})
        Milestone.objects.get_or_create(roadmap=roadmap, position=0, defaults={"title": "Ship an accessible frontend", "due_date": timezone.localdate() + timedelta(days=14)})
        Milestone.objects.get_or_create(roadmap=roadmap, position=1, defaults={"title": "Deploy the production API", "due_date": timezone.localdate() + timedelta(days=35)})

        all_topics = list(Topic.objects.filter(module__phase__roadmap=roadmap).order_by("module__phase__position", "module__position", "position"))
        for completed_topic in all_topics[:3]:
            TopicProgress.objects.update_or_create(user=user, topic=completed_topic, defaults={"status": TopicProgress.Status.COMPLETED, "confidence": 4, "completed_at": timezone.now() - timedelta(days=2), "last_studied_at": timezone.now() - timedelta(days=2)})
        if len(all_topics) > 3:
            TopicProgress.objects.update_or_create(user=user, topic=all_topics[3], defaults={"status": TopicProgress.Status.IN_PROGRESS, "confidence": 3, "last_studied_at": timezone.now() - timedelta(hours=6)})
        coding_project, _ = CodingProject.objects.get_or_create(
            owner=user,
            name="Python Learning Lab",
            defaults={
                "description": "A private workspace for Python exercises and experiments.",
                "primary_language": "python",
            },
        )
        if not coding_project.files.exists():
            create_file(
                user=user,
                project=coding_project,
                path="main.py",
                language="python",
                content=(
                    '"""LearnOS Python learning lab."""\n\n'
                    "def greet(name: str) -> str:\n"
                    '    return f"Welcome to LearnOS, {name}!"\n\n\n'
                    'print(greet("Learner"))\n'
                ),
            )
        web_project, _ = CodingProject.objects.get_or_create(
            owner=user,
            name="Portfolio Analytics Dashboard",
            defaults={"description": "A production-style TypeScript dashboard for measurable learning outcomes.", "primary_language": "typescript"},
        )
        if not web_project.files.exists():
            create_file(user=user, project=web_project, path="src/index.ts", language="typescript", content="type Metric = { label: string; value: number };\n\nconst metrics: Metric[] = [{ label: 'Completed topics', value: 3 }];\nconsole.log(metrics);\n")

        LearningGoal.objects.get_or_create(
            owner=user, title="Complete the full-stack roadmap",
            defaults={"description": "Finish every topic and ship the capstone application.", "category": LearningGoal.Category.CAREER, "status": LearningGoal.Status.IN_PROGRESS, "priority": LearningGoal.Priority.HIGH, "target_value": len(all_topics), "current_value": 3, "unit": "topics", "target_date": timezone.localdate() + timedelta(days=60), "roadmap": roadmap},
        )
        LearningGoal.objects.get_or_create(
            owner=user, title="Build three portfolio projects",
            defaults={"description": "Create polished projects with documentation and tests.", "category": LearningGoal.Category.PROJECT, "status": LearningGoal.Status.IN_PROGRESS, "priority": LearningGoal.Priority.HIGH, "target_value": 3, "current_value": 2, "unit": "projects", "target_date": timezone.localdate() + timedelta(days=45), "project": web_project},
        )
        LearningGoal.objects.get_or_create(
            owner=user, title="Study consistently each week",
            defaults={"description": "Complete five focused learning sessions every week.", "category": LearningGoal.Category.HABIT, "status": LearningGoal.Status.IN_PROGRESS, "priority": LearningGoal.Priority.MEDIUM, "target_value": 5, "current_value": 3, "unit": "sessions", "target_date": timezone.localdate() + timedelta(days=7)},
        )
        session_data = [(0, 52, "Review API architecture"), (1, 44, "Practice React state patterns"), (3, 61, "Model roadmap data in PostgreSQL"), (5, 35, "Write deployment checks")]
        for days_ago, minutes, session_goal in session_data:
            started_at = timezone.now() - timedelta(days=days_ago, minutes=minutes)
            if not StudySession.objects.filter(user=user, session_goal=session_goal).exists():
                StudySession.objects.create(user=user, topic=all_topics[min(days_ago, len(all_topics) - 1)] if all_topics else None, started_at=started_at, ended_at=started_at + timedelta(minutes=minutes), last_transition_at=started_at + timedelta(minutes=minutes), active_seconds=minutes * 60, session_goal=session_goal, session_summary="Completed the planned focus block.", status=StudySession.Status.ENDED)
        self.stdout.write(self.style.SUCCESS("Development user: learner@learnos.local / LearnOS-local-482!"))
