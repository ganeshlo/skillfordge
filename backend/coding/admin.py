from django.contrib import admin
from .models import CodingProject, ExecutionJob, ProjectFile, ProjectFileRevision

admin.site.register([CodingProject, ProjectFile, ProjectFileRevision, ExecutionJob])
