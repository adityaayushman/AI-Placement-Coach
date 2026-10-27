export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "student" | "coordinator" | "admin";
}

export interface Profile {
  pseudonym_id: string;
  department: string;
  graduation_year: number | null;
  gender: string | null;
  target_company_type: "product" | "service";
  target_role: string;
  cgpa: number | null;
  backlogs: number;
  tenth_pct: number | null;
  twelfth_pct: number | null;
  internships: number;
}

export interface Consent {
  scope: string;
  description: string;
  granted: boolean;
}

export interface Attribution {
  feature: string;
  label: string;
  value: number;
  baseline: number;
  effect: number;
}

export interface Score {
  id: number;
  score: number;
  probability: number | null;
  components: {
    values: Record<string, number | null>;
    missing: string[];
    company_type: string;
    data_source: string;
  };
  weights: Record<string, number>;
  model_version: string;
  attributions: Attribution[];
  created_at: string;
}

export interface Readiness {
  latest: Score | null;
  history: { at: string; score: number }[];
  change: { score: number | null; components: Record<string, number> };
}

export interface Recommendation {
  id: number;
  skill: string;
  reason: string;
  priority: number;
  status: string;
  resource: { id: number; title: string; url: string; kind: string; minutes: number } | null;
}

export interface Mastery {
  skill: string;
  p_known: number;
  n_obs: number;
}

export interface AtsCheck {
  id: string;
  label: string;
  points: number;
  max_points: number;
  passed: boolean;
  detail: string;
  fix: string;
}

export interface Gap {
  skill: string;
  category: string;
  importance: number;
  reason: string;
}

export interface Analysis {
  id: number;
  resume_id: number;
  jd_id: number | null;
  ats_score: number;
  ats_report: {
    ats_checks: AtsCheck[];
    fixes: string[];
    sections: string[];
    embedder: string;
    keyword_coverage: number | null;
  };
  match_scores: { overall?: number; sections?: Record<string, number> };
  skill_gaps: Gap[];
  skills_found: string[];
}

export interface Job {
  id: number;
  company: string;
  role: string;
  type: string;
  text: string;
  required_skills: { skill: string; weight: number }[];
}

export interface AssessmentSummary {
  id: number;
  title: string;
  skill: string;
}

export interface Question {
  id: number;
  skill: string;
  difficulty: number;
  prompt: string;
  options: string[];
}

export interface Attempt {
  id: number;
  assessment_id: number;
  score: number;
  correct: Record<string, boolean>;
}

export interface InterviewSession {
  id: number;
  role: string;
  company_type: string;
  status: string;
  questions: { id: number; category: string; difficulty: number; prompt: string }[];
}

export interface InterviewAnswer {
  id: number;
  question_id: number;
  transcript: string;
  scores: {
    content: number;
    communication: number;
    delivery: number | null;
    confidence: number;
    overall: number;
    details: Record<string, unknown>;
  };
  feedback: string[];
}

export interface Cohort {
  students: number;
  scored: number;
  mean_score: number | null;
  at_risk_count: number;
  distribution: { range: string; count: number }[];
  departments: ({ department: string; n: number; suppressed: boolean } & Record<string, unknown>)[];
  top_skill_gaps: { skill: string; students: number }[];
  min_group_size: number;
}

export interface StudentRow {
  user_id: number;
  name: string;
  email: string;
  department: string;
  target: string;
  score: number | null;
  missing: string[];
}

export interface Announcement {
  id: number;
  title: string;
  body: string;
  created_at: string;
}
