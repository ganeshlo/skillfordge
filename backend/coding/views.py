from django.utils import timezone
from django.conf import settings
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView

from audit.services import record_audit_event
from core.responses import api_response
from .models import CodingProject, ExecutionJob, ProjectFile
from .serializers import (
    CodingCapabilitiesSerializer,
    CodingProjectCreateSerializer,
    CodingProjectDetailSerializer,
    CodingProjectListSerializer,
    ExecutionJobCreateSerializer,
    ExecutionJobSerializer,
    ProjectFileRevisionSerializer,
    ProjectFileSerializer,
)
from .services import cancel_execution_job, create_execution_job, create_file, create_project, owned_projects, soft_delete_project, update_file
from .tasks import cancel_controller_job, dispatch_execution_job
from .validation import ALLOWED_LANGUAGES

STARTERS = {
    "python": ("main.py", "print(\"Hello from LearnOS!\")\n"),
    "javascript": ("index.js", "console.log(\"Hello from LearnOS!\");\n"),
    "typescript": ("index.ts", "const message: string = \"Hello from LearnOS!\";\nconsole.log(message);\n"),
    "java": ("Main.java", "public class Main {\n  public static void main(String[] args) {\n    System.out.println(\"Hello from LearnOS!\");\n  }\n}\n"),
    "c": ("main.c", "#include <stdio.h>\n\nint main(void) {\n  puts(\"Hello from LearnOS!\");\n  return 0;\n}\n"),
    "cpp": ("main.cpp", "#include <iostream>\n\nint main() {\n  std::cout << \"Hello from LearnOS!\\n\";\n  return 0;\n}\n"),
    "go": ("main.go", "package main\n\nimport \"fmt\"\n\nfunc main() { fmt.Println(\"Hello from LearnOS!\") }\n"),
    "rust": ("main.rs", "fn main() {\n    println!(\"Hello from LearnOS!\");\n}\n"),
    "php": ("main.php", "<?php\necho \"Hello from LearnOS!\\n\";\n"),
    "ruby": ("main.rb", "puts \"Hello from LearnOS!\"\n"),
    "kotlin": ("Main.kt", "fun main() {\n  println(\"Hello from LearnOS!\")\n}\n"),
    "sql": ("main.sql", "CREATE TABLE learners (name TEXT, progress INTEGER);\nINSERT INTO learners VALUES ('LearnOS', 100);\nSELECT * FROM learners;\n"),
    "html": ("index.html", "<!doctype html>\n<html lang=\"en\">\n  <head><meta charset=\"utf-8\"><title>LearnOS Project</title></head>\n  <body><h1>Hello from LearnOS!</h1></body>\n</html>\n"),
    "react": ("src/App.tsx", "export default function App() {\n  return <h1>Hello from LearnOS!</h1>;\n}\n"),
}


class CodingProjectListCreateView(GenericAPIView):
    queryset = CodingProject.objects.none()
    serializer_class = CodingProjectListSerializer

    @extend_schema(operation_id="coding_project_list", responses=CodingProjectListSerializer(many=True))
    def get(self, request):
        return api_response(self.get_serializer(owned_projects(user=request.user), many=True).data, request=request)

    @extend_schema(operation_id="coding_project_create", request=CodingProjectCreateSerializer, responses=CodingProjectDetailSerializer)
    def post(self, request):
        serializer = CodingProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        include_starter = serializer.validated_data.pop("include_starter")
        project = create_project(user=request.user, request=request, **serializer.validated_data)
        if include_starter:
            path, content = STARTERS.get(project.primary_language, ("README.md", f"# {project.name}\n"))
            language = project.primary_language if project.primary_language in STARTERS else "markdown"
            create_file(user=request.user, project=project, path=path, content=content, language=language, request=request)
        project = owned_projects(user=request.user).get(id=project.id)
        return api_response(CodingProjectDetailSerializer(project).data, request=request, status=status.HTTP_201_CREATED)


class CodingProjectDetailView(GenericAPIView):
    queryset = CodingProject.objects.none()
    serializer_class = CodingProjectDetailSerializer

    def get_object(self):
        project = owned_projects(user=self.request.user).filter(id=self.kwargs["project_id"]).first()
        if not project:
            raise NotFound("Coding project not found.")
        return project

    def get(self, request, project_id):
        return api_response(self.get_serializer(self.get_object()).data, request=request)

    def patch(self, request, project_id):
        project = self.get_object()
        serializer = CodingProjectListSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response(CodingProjectDetailSerializer(project).data, request=request)

    def delete(self, request, project_id):
        soft_delete_project(user=request.user, project=self.get_object(), request=request)
        return api_response({"deleted": True}, request=request)


class ProjectFileCreateView(GenericAPIView):
    queryset = ProjectFile.objects.none()
    serializer_class = ProjectFileSerializer

    def post(self, request, project_id):
        project = owned_projects(user=request.user).filter(id=project_id).first()
        if not project:
            raise NotFound("Coding project not found.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = create_file(user=request.user, project=project, request=request, **serializer.validated_data)
        return api_response(self.get_serializer(file).data, request=request, status=status.HTTP_201_CREATED)


class ProjectFileDetailView(GenericAPIView):
    queryset = ProjectFile.objects.none()
    serializer_class = ProjectFileSerializer

    def get_object(self):
        file = ProjectFile.objects.select_related("project").filter(
            id=self.kwargs["file_id"], project__owner=self.request.user, project__deleted_at__isnull=True,
        ).first()
        if not file:
            raise NotFound("Project file not found.")
        return file

    def patch(self, request, file_id):
        file = self.get_object()
        serializer = self.get_serializer(file, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        file = update_file(user=request.user, file=file, request=request, **serializer.validated_data)
        return api_response(self.get_serializer(file).data, request=request)

    def delete(self, request, file_id):
        file = self.get_object()
        project = file.project
        path = file.path
        file.delete()
        project.updated_at = timezone.now()
        project.save(update_fields=["updated_at"])
        record_audit_event(action="coding.file_deleted", actor=request.user, target=project, request=request, metadata={"path": path})
        return api_response({"deleted": True}, request=request)


class ProjectFileRevisionListView(GenericAPIView):
    queryset = ProjectFile.objects.none()
    serializer_class = ProjectFileRevisionSerializer

    def get(self, request, file_id):
        file = ProjectFile.objects.filter(id=file_id, project__owner=request.user, project__deleted_at__isnull=True).first()
        if not file:
            raise NotFound("Project file not found.")
        return api_response(self.get_serializer(file.revisions.all()[:50], many=True).data, request=request)


class CodingCapabilitiesView(GenericAPIView):
    serializer_class = CodingCapabilitiesSerializer

    def get(self, request):
        data = {
            "editor": True,
            "autosave": True,
            "version_history": True,
            "project_download": True,
            "execution": settings.EXECUTION_ENABLED,
            "execution_message": "Secure execution is ready." if settings.EXECUTION_ENABLED else "Run is disabled because the isolated runner is not configured. Set the execution controller URL and signing secret, then connect a sandbox provider.",
            "languages": sorted(ALLOWED_LANGUAGES),
        }
        return api_response(self.get_serializer(data).data, request=request)


class ExecutionJobListCreateView(GenericAPIView):
    queryset = ExecutionJob.objects.none()
    serializer_class = ExecutionJobSerializer

    @extend_schema(operation_id="coding_execution_list", responses=ExecutionJobSerializer(many=True))
    def get(self, request):
        jobs = ExecutionJob.objects.filter(requested_by=request.user).select_related("source_file")[:50]
        return api_response(self.get_serializer(jobs, many=True).data, request=request)

    @extend_schema(operation_id="coding_execution_create", request=ExecutionJobCreateSerializer, responses=ExecutionJobSerializer)
    def post(self, request):
        serializer = ExecutionJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key", "")
        if len(key) < 8 or len(key) > 128:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"idempotency_key": "Provide an Idempotency-Key between 8 and 128 characters."})
        file = ProjectFile.objects.select_related("project").filter(
            id=serializer.validated_data["file_id"], project__owner=request.user, project__deleted_at__isnull=True,
        ).first()
        if not file:
            raise NotFound("Project file not found.")
        job, created = create_execution_job(
            user=request.user, file=file, stdin=serializer.validated_data["stdin"],
            idempotency_key=key, request=request,
        )
        if created:
            transaction.on_commit(lambda: dispatch_execution_job.delay(str(job.id)))
        output = ExecutionJob.objects.select_related("source_file").get(id=job.id)
        return api_response(self.get_serializer(output).data, request=request, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ExecutionJobDetailView(GenericAPIView):
    queryset = ExecutionJob.objects.none()
    serializer_class = ExecutionJobSerializer

    def get_object(self):
        job = ExecutionJob.objects.select_related("source_file").filter(id=self.kwargs["job_id"], requested_by=self.request.user).first()
        if not job:
            raise NotFound("Execution job not found.")
        return job

    @extend_schema(operation_id="coding_execution_retrieve", responses=ExecutionJobSerializer)
    def get(self, request, job_id):
        return api_response(self.get_serializer(self.get_object()).data, request=request)


class ExecutionJobCancelView(GenericAPIView):
    queryset = ExecutionJob.objects.none()
    serializer_class = ExecutionJobSerializer

    @extend_schema(operation_id="coding_execution_cancel", responses=ExecutionJobSerializer)
    def post(self, request, job_id):
        job = ExecutionJob.objects.select_related("source_file").filter(id=job_id, requested_by=request.user).first()
        if not job:
            raise NotFound("Execution job not found.")
        job, cancelled = cancel_execution_job(user=request.user, job=job, request=request)
        if cancelled:
            transaction.on_commit(lambda: cancel_controller_job.delay(str(job.id)))
        return api_response(self.get_serializer(job).data, request=request)
