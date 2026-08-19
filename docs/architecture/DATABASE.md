# Database Entity Relationships

All primary business entities use UUID keys, UTC timestamps, indexed tenant keys where applicable, and soft deletion for user-restorable content. Restricted secrets live in a separate encrypted credential store/table and never in generic JSON fields.

```text
User 1--1 UserProfile
User 1--1 UserPreference
User 1--* DeviceSession
User *--* Organization through OrganizationMembership
Organization 1--* Team
Team *--* User through TeamMembership
Organization 1--* Role --* Permission

User/Organization 1--* Roadmap 1--* RoadmapPhase 1--* LearningModule
LearningModule 1--* Topic 1--* Lesson 1--* Activity
Topic 1--* Resource
Roadmap *--* User through RoadmapAssignment
User *--* Topic through TopicProgress

Resource 1--0..1 LearningVideo
LearningVideo 1--* VideoProgress (per user)
VideoProgress 1--* WatchedInterval
VideoProgress 1--* WatchSession
LearningVideo 1--* VideoNote / VideoBookmark

User 1--* StudySession
User 1--* Note *--* NoteTag
Note *--* Topic / Resource / CodingProject (typed links)
Document 1--* DocumentChunk 1--1 EmbeddingReference

Quiz 1--* Question 1--* AnswerOption
Quiz 1--* QuizAttempt 1--* AttemptAnswer
Flashcard 1--* FlashcardReview

CodingProblem 1--* TestCase
CodingProblem 1--* CodeSubmission 1--0..1 ExecutionJob
CodingProject 1--* ProjectFile / ProjectTask / ProjectVersion

User 1--* Goal 1--* Habit / GoalCheckIn
User *--* Skill through UserSkillEvidence
User 1--* CareerReadinessSnapshot

AIConversation 1--* AIMessage
AIRequest 1--1 AIUsage
AIMessage *--* SourceReference

User 1--* Notification
Organization 1--* AuditLog
Organization/User 1--* Integration 1--0..1 EncryptedCredential
```

## Tenant isolation

Tenant-owned tables carry a non-null `organization_id`; private personal rows carry an `owner_id` and nullable organization association only when deliberately shared. Unique constraints include the tenant key. Query helpers require a tenant/principal argument. PostgreSQL row-level security is a defense-in-depth option after connection-pooling behavior is validated; application policies remain mandatory.

## High-volume tables

`activity_event`, `watched_interval`, `audit_log`, `ai_usage`, and `execution_job` use time-oriented indexes and are candidates for monthly partitioning. Aggregates are materialized asynchronously; product reads do not scan raw event history.

## Video completion invariant

Intervals are normalized, clamped to `[0, duration]`, merged when overlapping/adjacent, and summed once. Completion is `unique_watched_seconds / duration`, never `last_position / duration`.

