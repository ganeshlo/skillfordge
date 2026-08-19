from django.contrib import admin
from .models import Milestone, Resource, Roadmap, RoadmapModule, RoadmapPhase, Topic, TopicProgress

admin.site.register([Roadmap, RoadmapPhase, RoadmapModule, Topic, Resource, Milestone, TopicProgress])

