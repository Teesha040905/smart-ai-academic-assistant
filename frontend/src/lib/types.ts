export type Priority = "low" | "medium" | "high";
export type Difficulty = "easy" | "medium" | "hard";
export type TopicStatus = "not_started" | "in_progress" | "completed" | "needs_revision";
export type SessionStatus = "scheduled" | "completed" | "missed" | "skipped";
export type DocumentStatus = "pending" | "processing" | "ready" | "failed";
export type AssignmentStatus = "pending" | "in_progress" | "completed" | "overdue";
export type UserRole = "student" | "admin";

export interface StudentProfile {
  id: string;
  user_id: string;
  photo_url?: string | null;
  course?: string | null;
  branch?: string | null;
  semester?: number | null;
  academic_year?: string | null;
  preferred_study_time?: string | null;
  daily_study_hours: number;
  learning_preferences?: string | null;
  academic_goals?: string | null;
  notification_prefs?: string | null;
  ai_prefs?: string | null;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  theme: string;
  is_active: boolean;
  profile?: StudentProfile | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Topic {
  id: string;
  subject_id: string;
  unit_id?: string | null;
  name: string;
  description?: string | null;
  difficulty: Difficulty;
  status: TopicStatus;
  knowledge_level: number;
  last_studied_at?: string | null;
  revision_count: number;
  quiz_average?: number | null;
  importance: number;
}

export interface Unit {
  id: string;
  subject_id: string;
  name: string;
  order_index: number;
  progress_override?: number | null;
  progress: number;
  topics: Topic[];
}

export interface Subject {
  id: string;
  name: string;
  code?: string | null;
  description?: string | null;
  color: string;
  priority: Priority;
  exam_date?: string | null;
  progress: number;
  units: Unit[];
  topics: Topic[];
}

export interface Document {
  id: string;
  title: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  status: DocumentStatus;
  progress: number;
  error_message?: string | null;
  subject_id?: string | null;
  unit_id?: string | null;
  topic_id?: string | null;
  page_count?: number | null;
  created_at: string;
}

export interface Message {
  id: string;
  role: string;
  content: string;
  sources_json?: string | null;
  used_rag: boolean;
  from_general_knowledge: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  subject_id?: string | null;
  created_at: string;
  messages: Message[];
}

export interface StudySession {
  id: string;
  plan_id?: string | null;
  subject_id?: string | null;
  topic_id?: string | null;
  title: string;
  scheduled_date: string;
  start_time?: string | null;
  end_time?: string | null;
  duration_minutes: number;
  status: SessionStatus;
  activity_type: string;
  notes?: string | null;
}

export interface StudyPlan {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  notes?: string | null;
  is_active: boolean;
  sessions: StudySession[];
}

export interface QuizQuestion {
  id: string;
  question_type: string;
  prompt: string;
  options_json?: string | null;
  topic_tag?: string | null;
  order_index: number;
}

export interface Quiz {
  id: string;
  title: string;
  subject_id?: string | null;
  topic_id?: string | null;
  difficulty: Difficulty;
  question_count: number;
  questions: QuizQuestion[];
}

export interface QuizAnswerReview {
  question_id: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation?: string | null;
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  score: number;
  max_score: number;
  percentage: number;
  strong_topics_json?: string | null;
  weak_topics_json?: string | null;
  completed_at?: string | null;
  review: QuizAnswerReview[];
}

export interface Flashcard {
  id: string;
  subject_id?: string | null;
  topic_id?: string | null;
  question: string;
  answer: string;
  difficulty: Difficulty;
  review_status: string;
  next_review_at?: string | null;
}

export interface Exam {
  id: string;
  subject_id: string;
  name: string;
  exam_date: string;
  exam_time?: string | null;
  syllabus?: string | null;
  priority: Priority;
  days_remaining?: number | null;
  readiness?: Record<string, unknown> | null;
}

export interface Assignment {
  id: string;
  title: string;
  subject_id?: string | null;
  description?: string | null;
  deadline: string;
  priority: Priority;
  status: AssignmentStatus;
}

export interface Recommendation {
  id: string;
  topic_id?: string | null;
  subject_id?: string | null;
  priority: Priority;
  title: string;
  reason: string;
  suggested_actions: Record<string, unknown>[];
  score: number;
}

export interface WeakTopic {
  id: string;
  name: string;
  subject_id: string;
  knowledge_level: number;
  status: "critical" | "warning" | "good";
  quiz_average?: number | null;
}

export interface Dashboard {
  greeting: string;
  student_name: string;
  stats: Record<string, unknown>;
  today_plan: StudySession[];
  weak_topics: WeakTopic[];
  recommendation?: Recommendation | null;
  upcoming_exams: Exam[];
  upcoming_assignments: Assignment[];
  streak: Record<string, unknown>;
}

export interface Analytics {
  overall_progress: number;
  subject_performance: Record<string, unknown>[];
  topic_performance: Record<string, unknown>[];
  study_hours: number;
  quiz_average: number;
  assignments_completed: number;
  topics_completed: number;
  topics_remaining: number;
  weekly_progress: Record<string, unknown>[];
  monthly_progress: Record<string, unknown>[];
  revision_frequency: number;
  study_consistency: number;
}

export interface KnowledgeMap {
  subjects: Record<string, unknown>[];
}

export interface SearchResult {
  type: string;
  id: string;
  title: string;
  subtitle?: string | null;
}

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}
