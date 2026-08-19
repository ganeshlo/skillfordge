from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView

from audit.services import record_audit_event
from core.responses import api_response

from .models import Milestone, Roadmap, RoadmapModule, RoadmapPhase, Topic
from .selectors import roadmap_detail, visible_roadmaps
from .serializers import (
    MilestoneSerializer,
    ResourceSerializer,
    RoadmapCreateSerializer,
    RoadmapDetailSerializer,
    RoadmapListSerializer,
    RoadmapModuleSerializer,
    RoadmapPhaseSerializer,
    TopicProgressSerializer,
    TopicProgressUpdateSerializer,
    TopicSerializer,
)
from .services import (
    add_module,
    add_phase,
    add_resource,
    add_topic,
    create_roadmap,
    update_topic_progress,
)


class RoadmapListCreateView(GenericAPIView):
    queryset = Roadmap.objects.none()
    serializer_class = RoadmapListSerializer

    @extend_schema(operation_id="roadmap_list", responses=RoadmapListSerializer(many=True))
    def get(self, request):
        queryset = visible_roadmaps(user=request.user)
        requested_status = request.query_params.get("status")
        if requested_status in Roadmap.Status.values:
            queryset = queryset.filter(status=requested_status)
        return api_response(self.get_serializer(queryset, many=True).data, request=request)

    @extend_schema(operation_id="roadmap_create", request=RoadmapCreateSerializer, responses=RoadmapListSerializer)
    def post(self, request):
        serializer = RoadmapCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap = create_roadmap(user=request.user, request=request, **serializer.validated_data)
        roadmap = visible_roadmaps(user=request.user).get(id=roadmap.id)
        return api_response(RoadmapListSerializer(roadmap, context={"request": request}).data, request=request, status=status.HTTP_201_CREATED)


class RoadmapDetailView(GenericAPIView):
    serializer_class = RoadmapDetailSerializer

    def get_object(self):
        roadmap = roadmap_detail(user=self.request.user, roadmap_id=self.kwargs["roadmap_id"])
        if not roadmap:
            raise NotFound("Roadmap not found.")
        return roadmap

    @extend_schema(operation_id="roadmap_detail")
    def get(self, request, roadmap_id):
        return api_response(self.get_serializer(self.get_object()).data, request=request)

    def patch(self, request, roadmap_id):
        roadmap = self.get_object()
        if roadmap.owner_id != request.user.id:
            raise PermissionDenied("Only the owner can edit this roadmap.")
        serializer = RoadmapCreateSerializer(roadmap, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.pop("organization_id", None)
        serializer.save()
        roadmap = roadmap_detail(user=request.user, roadmap_id=roadmap.id)
        return api_response(self.get_serializer(roadmap).data, request=request)

    def delete(self, request, roadmap_id):
        roadmap = self.get_object()
        if roadmap.owner_id != request.user.id:
            raise PermissionDenied("Only the owner can delete this roadmap.")
        roadmap.deleted_at = timezone.now()
        roadmap.save(update_fields=["deleted_at", "updated_at"])
        record_audit_event(action="roadmap.deleted", actor=request.user, organization=roadmap.organization, target=roadmap, request=request)
        return api_response({"deleted": True}, request=request)


class PhaseCreateView(GenericAPIView):
    serializer_class = RoadmapPhaseSerializer

    def post(self, request, roadmap_id):
        roadmap = roadmap_detail(user=request.user, roadmap_id=roadmap_id)
        if not roadmap:
            raise NotFound("Roadmap not found.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phase = add_phase(user=request.user, roadmap=roadmap, request=request, **serializer.validated_data)
        return api_response(self.get_serializer(phase).data, request=request, status=status.HTTP_201_CREATED)


class ModuleCreateView(GenericAPIView):
    serializer_class = RoadmapModuleSerializer

    def post(self, request, phase_id):
        phase = RoadmapPhase.objects.select_related("roadmap").filter(id=phase_id, roadmap__in=visible_roadmaps(user=request.user)).first()
        if not phase:
            raise NotFound("Roadmap phase not found.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = add_module(user=request.user, phase=phase, **serializer.validated_data)
        return api_response(self.get_serializer(module).data, request=request, status=status.HTTP_201_CREATED)


class TopicCreateView(GenericAPIView):
    serializer_class = TopicSerializer

    def post(self, request, module_id):
        module = RoadmapModule.objects.select_related("phase__roadmap").filter(id=module_id, phase__roadmap__in=visible_roadmaps(user=request.user)).first()
        if not module:
            raise NotFound("Roadmap module not found.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = add_topic(user=request.user, module=module, **serializer.validated_data)
        return api_response(self.get_serializer(topic).data, request=request, status=status.HTTP_201_CREATED)


class ResourceCreateView(GenericAPIView):
    serializer_class = ResourceSerializer

    def post(self, request, topic_id):
        topic = Topic.objects.select_related("module__phase__roadmap").filter(id=topic_id, module__phase__roadmap__in=visible_roadmaps(user=request.user)).first()
        if not topic:
            raise NotFound("Roadmap topic not found.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resource = add_resource(user=request.user, topic=topic, **serializer.validated_data)
        return api_response(self.get_serializer(resource).data, request=request, status=status.HTTP_201_CREATED)


class MilestoneCreateView(GenericAPIView):
    serializer_class = MilestoneSerializer

    def post(self, request, roadmap_id):
        roadmap = roadmap_detail(user=request.user, roadmap_id=roadmap_id)
        if not roadmap:
            raise NotFound("Roadmap not found.")
        if roadmap.owner_id != request.user.id:
            raise PermissionDenied("Only the owner can add milestones.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        position = serializer.validated_data.pop("position", roadmap.milestones.count())
        milestone = Milestone.objects.create(roadmap=roadmap, position=position, **serializer.validated_data)
        return api_response(self.get_serializer(milestone).data, request=request, status=status.HTTP_201_CREATED)


class MilestoneDetailView(GenericAPIView):
    serializer_class = MilestoneSerializer

    def get_object(self, request, milestone_id):
        milestone = Milestone.objects.select_related("roadmap").filter(id=milestone_id, roadmap__owner=request.user, roadmap__deleted_at__isnull=True).first()
        if not milestone:
            raise NotFound("Milestone not found.")
        return milestone

    def patch(self, request, milestone_id):
        milestone = self.get_object(request, milestone_id)
        completed = request.data.get("completed")
        if completed is not None and not isinstance(completed, bool):
            raise ValidationError({"completed": "Must be true or false."})
        editable = {key: value for key, value in request.data.items() if key in {"title", "due_date", "position"}}
        serializer = self.get_serializer(milestone, data=editable, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(completed_at=timezone.now() if completed else None if completed is not None else milestone.completed_at)
        return api_response(serializer.data, request=request)

    def delete(self, request, milestone_id):
        self.get_object(request, milestone_id).delete()
        return api_response({"deleted": True}, request=request)


class TopicProgressView(GenericAPIView):
    serializer_class = TopicProgressUpdateSerializer

    def post(self, request, topic_id):
        topic = Topic.objects.select_related("module__phase__roadmap").filter(id=topic_id, module__phase__roadmap__in=visible_roadmaps(user=request.user)).first()
        if not topic:
            raise NotFound("Roadmap topic not found.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        progress = update_topic_progress(user=request.user, topic=topic, request=request, **serializer.validated_data)
        return api_response(TopicProgressSerializer(progress).data, request=request)
