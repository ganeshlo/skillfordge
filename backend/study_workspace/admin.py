from django.contrib import admin
from .models import (
    StudyBookmark,
    StudyNote,
    StudyResource,
    StudySession,
    TopicStudyProgress,
    VideoProgress,
    WatchedInterval,
)

admin.site.register(
    [
        StudyResource,
        VideoProgress,
        WatchedInterval,
        StudyNote,
        StudyBookmark,
        StudySession,
        TopicStudyProgress,
    ]
)
