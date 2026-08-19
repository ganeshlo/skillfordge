# Study Workspace

The workspace is scoped to existing roadmap topics. A roadmap owner adds an official YouTube URL; authenticated learners with topic access receive private progress, notes, and bookmarks.

```text
/study -> choose topic -> /study/{topicId}
  -> add/select YouTube video
  -> YouTube IFrame API emits playback intervals
  -> PATCH progress with idempotent client event ID
  -> create timestamped notes/bookmarks beside the player
```

`StudyResource` stores the YouTube ID without downloading media. `VideoProgress` is unique per user/resource. `WatchedInterval` records replay-safe client events, while the service merges overlaps to calculate unique watched seconds; completion requires 90% unique coverage. `StudyNote` and `StudyBookmark` are always filtered by the authenticated user. The REST API validates YouTube hosts, timestamps, note size, topic visibility, and content ownership.

Frontend state keeps the current player timestamp and drafts locally. Note drafts are mirrored to `localStorage`; playback intervals save every 12 seconds and on pause/end. The production screen is responsive: video first, with notes and bookmarks beside it on desktop and below it on smaller screens.
