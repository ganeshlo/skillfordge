export type ApiEnvelope<T> = { data: T; request_id: string | null };

export type User = {
  id: string;
  email: string;
  full_name: string;
  email_verified_at: string | null;
  profile: {
    professional_role: string;
    experience_level: string;
    career_goal: string;
    learning_goals: string[];
    target_skills: string[];
    daily_minutes: number;
    weekly_target_minutes: number;
    onboarding_completed_at: string | null;
  };
  preferences: { theme: string; timezone: string; learning_style: string; email_notifications: boolean };
};

export type Organization = { id: string; name: string; slug: string; current_role: string; created_at: string };

export type DashboardData = {
  overview: {
    first_name: string; full_name: string; professional_role: string; experience_level: string;
    career_goal: string; profile_completion: number; onboarding_complete: boolean; email_verified: boolean;
  };
  targets: {
    daily_minutes: number; weekly_target_minutes: number; target_skills: string[];
    current_skills: string[]; preferred_languages: string[];
  };
  organizations: { id: string; name: string; slug: string; role: string }[];
  organization_count: number;
  recent_activity: { id: string; action: string; label: string; created_at: string }[];
  next_action: { type: string; title: string; description: string; label: string; href: string; available: boolean };
  learning_activity: { weekly_minutes: number; weekly_target_minutes: number; days: { date: string; minutes: number; sessions: number }[] };
  modules: { key: string; label: string; description: string; status: "ready" | "next" | "planned"; href: string | null }[];
};

export type RoadmapSummary = {
  id: string; title: string; description: string; career_goal: string; visibility: "private" | "organization" | "public";
  status: "draft" | "active" | "completed" | "archived"; target_deadline: string | null; estimated_minutes: number;
  owner_name: string; organization_name: string | null; topic_count: number; completed_topic_count: number;
  progress_percentage: number; is_owner: boolean; created_at: string; updated_at: string;
};

export type RoadmapTopic = {
  id: string; title: string; objective: string; difficulty: string; position: number; estimated_minutes: number;
  progress: { status: string; confidence: number | null; completed_at: string | null; last_studied_at: string | null } | null;
  resources: { id: string; title: string; url: string; resource_type: string; position: number }[];
};

export type RoadmapDetail = RoadmapSummary & {
  phases: { id: string; title: string; description: string; position: number; modules: { id: string; title: string; description: string; position: number; estimated_minutes: number; topics: RoadmapTopic[] }[] }[];
  milestones: { id: string; title: string; due_date: string | null; completed_at: string | null; position: number }[];
};

export type LearningGoal = {
  id: string; title: string; description: string; category: "career" | "skill" | "project" | "certification" | "habit";
  status: "not_started" | "in_progress" | "completed" | "paused"; priority: "low" | "medium" | "high";
  target_value: number; current_value: number; unit: string; target_date: string | null; completed_at: string | null;
  roadmap: string | null; roadmap_title: string | null; project: string | null; project_name: string | null;
  progress_percentage: number; is_overdue: boolean; created_at: string; updated_at: string;
};

export type LearningAnalytics = {
  overview: { total_study_minutes: number; weekly_study_minutes: number; completed_topics: number; total_topics: number; active_roadmaps: number; projects: number; completed_goals: number; total_goals: number };
  weekly_activity: { date: string; minutes: number; sessions: number }[];
  roadmaps: { id: string; title: string; status: string; topic_count: number; completed_topic_count: number; progress_percentage: number }[];
  goal_breakdown: { status: string; count: number }[];
};

export type CodingProjectSummary = {
  id: string; name: string; description: string; primary_language: string; status: "active" | "archived";
  file_count: number; created_at: string; updated_at: string;
};

export type CodingFile = {
  id: string; path: string; content: string; language: string; version: number; checksum: string;
  size_bytes: number; created_at: string; updated_at: string;
};

export type CodingProjectDetail = CodingProjectSummary & { files: CodingFile[] };

export type CodingCapabilities = {
  editor: boolean; autosave: boolean; version_history: boolean; project_download: boolean;
  execution: boolean; execution_message: string; languages: string[];
};

export type ExecutionJob = {
  id: string; project_id: string; file_path: string | null; language: string;
  status: "queued" | "dispatching" | "running" | "succeeded" | "failed" | "cancelled" | "timed_out";
  limits: { timeout_seconds: number; memory_mb: number; cpu_millis: number; output_bytes: number; network: false };
  stdout: string; stderr: string; exit_code: number | null; error_code: string;
  started_at: string | null; finished_at: string | null; cancelled_at: string | null;
  runtime_ms: number | null; memory_bytes: number | null; created_at: string; updated_at: string;
};

export type StudyProgress = { id: string; last_position_seconds: number; unique_watched_seconds: number; completion_percentage: string; playback_speed: string; completed: boolean; completed_at: string | null; last_watched_at: string | null; watched_intervals: { id: string; start_seconds: number; end_seconds: number }[]; updated_at: string };
export type StudyTranscriptStatus = { available: boolean; has_timestamps: boolean; language: string | null };
export type StudyResource = { id: string; title: string; external_url: string; youtube_video_id: string; channel_name: string; duration_seconds: number; display_order: number; progress: StudyProgress | null; transcript: StudyTranscriptStatus };
export type StudyNote = { id: string; timestamp_seconds: number; range_end_seconds: number | null; content: string; content_format: string; is_pinned: boolean; is_important: boolean; tags: string[]; source: "manual" | "ai"; created_at: string; updated_at: string };
export type StudyBookmark = { id: string; timestamp_seconds: number; label: string; description: string; bookmark_type: string; created_at: string; updated_at: string };
export type StudySession = { id: string; resource: string | null; started_at: string; ended_at: string | null; last_transition_at: string; active_seconds: number; paused_seconds: number; idle_seconds: number; session_goal: string; session_summary: string; status: "active" | "paused" | "ended"; created_at: string; updated_at: string };
export type TodayActivity = { active_study_seconds: number; video_playback_seconds: number; unique_watched_seconds: number; videos_studied: number; videos_completed: number; notes_created: number; bookmarks_created: number };
export type StudyWorkspaceData = { library: { title: string; count: number }; resources: StudyResource[]; current_resource_id: string | null; notes: StudyNote[]; bookmarks: StudyBookmark[]; today_activity: TodayActivity; active_session: StudySession | null; ai_notes_available: boolean };

export type KnowledgeFolder = { id: string; parent_id: string | null; name: string; color: string; is_favorite: boolean; item_count: number; created_at: string; updated_at: string };
export type KnowledgeTag = { id: string; name: string; color: string; created_at: string };
export type KnowledgeNote = { id: string; folder_id: string | null; title: string; content: string; content_format: "markdown"; tags: KnowledgeTag[]; context_type: "general" | "subject" | "topic" | "project"; context_label: string; source_url: string; is_favorite: boolean; is_archived: boolean; current_version: number; created_at: string; updated_at: string };
export type KnowledgeNoteVersion = { id: string; version: number; title: string; content: string; created_at: string };
export type KnowledgeDocument = { id: string; folder_id: string | null; title: string; original_filename: string; mime_type: string; size_bytes: number; status: "processing" | "ready" | "failed"; error_code: string; page_count: number; is_favorite: boolean; tags: KnowledgeTag[]; highlights_count: number; created_at: string; updated_at: string };
export type DocumentHighlight = { id: string; page_number: number; start_offset: number | null; end_offset: number | null; quote: string; annotation: string; color: string; created_at: string; updated_at: string };
export type CodeSnippet = { id: string; folder_id: string | null; title: string; description: string; language: string; code: string; is_favorite: boolean; tags: KnowledgeTag[]; created_at: string; updated_at: string };
export type KnowledgeSearchResult = { id: string; source_type: "note" | "document" | "snippet"; source_id: string; title: string; excerpt: string; score: number; metadata: Record<string, string> };
export type KnowledgeDashboard = { counts: { notes: number; documents: number; snippets: number; favorites: number }; folders: KnowledgeFolder[]; tags: KnowledgeTag[]; recent_notes: KnowledgeNote[]; recent_documents: KnowledgeDocument[]; recent_snippets: CodeSnippet[]; semantic_search_available: boolean };

export type BillingPlan = { id: string; code: "free" | "pro" | "enterprise"; name: string; description: string; amount_minor: number; compare_at_amount_minor: number | null; currency: string; billing_interval: "month" | "year"; duration_days: number; features: string[]; limits: { coding_projects?: number | null }; is_featured: boolean };
export type BillingSubscription = { id: string | null; plan: BillingPlan | null; provider: string | null; status: "pending" | "active" | "past_due" | "cancelled" | "expired"; started_at: string | null; current_period_start: string | null; current_period_end: string | null; cancel_at_period_end: boolean; cancelled_at: string | null; ended_at: string | null };
export type BillingPayment = { id: string; plan: BillingPlan; provider: string; provider_order_id: string | null; provider_payment_id: string; amount_minor: number; currency: string; status: "created" | "authorized" | "captured" | "failed" | "cancelled" | "refund_pending" | "refunded"; signature_verified: boolean; failure_code: string; failure_description: string; paid_at: string | null; refunded_at: string | null; created_at: string; updated_at: string };
export type BillingInvoice = { id: string; invoice_number: string; plan_name: string; amount_minor: number; currency: string; status: "paid" | "refunded" | "void"; issued_at: string; refunded_at: string | null };
export type BillingOrder = { free_activated: boolean; subscription?: BillingSubscription; key_id?: string; payment_id?: string; order_id?: string; amount_minor?: number; currency?: string; plan?: BillingPlan; prefill?: { name: string; email: string } };
