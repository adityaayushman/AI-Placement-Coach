/**
 * Preview mode: lets visitors explore the UI without a backend. Every response here is SAMPLE
 * data generated in the browser; nothing is sent anywhere or saved. The shell shows a banner
 * whenever preview mode is on.
 */
import type { Role } from "./client";

const KEY = "pc.preview";

export function previewRole(): Role | null {
  try {
    return (sessionStorage.getItem(KEY) as Role | null) ?? null;
  } catch {
    return null;
  }
}

export function setPreview(role: Role | null): void {
  try {
    if (role) sessionStorage.setItem(KEY, role);
    else sessionStorage.removeItem(KEY);
  } catch {
    /* storage unavailable */
  }
}

const now = Date.now();
const day = 86_400_000;
const iso = (d: number) => new Date(now - d * day).toISOString();

const state = {
  consents: {
    resume: true,
    interview_recording: false,
    analytics: true,
    coordinator_visibility: false,
  } as Record<string, boolean>,
  recs: [
    { id: 1, skill: "system design", reason: "Estimated mastery 20%; weighted highly by product-based companies; prerequisites are in place; missing from your resume for your target role.", priority: 0.55, status: "open", resource: { id: 7, title: "The System Design Primer", url: "https://github.com/donnemartin/system-design-primer", kind: "guide", minutes: 120 } },
    { id: 2, skill: "dynamic programming", reason: "Estimated mastery 31%; weighted highly by product-based companies; prerequisites are in place.", priority: 0.48, status: "open", resource: { id: 3, title: "CP-Algorithms: introduction to DP", url: "https://cp-algorithms.com/dynamic_programming/intro-to-dp.html", kind: "article", minutes: 45 } },
    { id: 3, skill: "dbms", reason: "Estimated mastery 42%.", priority: 0.33, status: "open", resource: { id: 10, title: "PostgreSQL tutorial", url: "https://www.postgresql.org/docs/current/tutorial.html", kind: "tutorial", minutes: 60 } },
    { id: 4, skill: "testing", reason: "Estimated mastery 20%; missing from your resume for your target role.", priority: 0.3, status: "open", resource: null },
  ],
};

const SAMPLE_USERS: Record<Role, { id: number; email: string; full_name: string; role: Role }> = {
  student: { id: 1, email: "preview.student@example.com", full_name: "Preview Student", role: "student" },
  coordinator: { id: 2, email: "preview.coordinator@example.com", full_name: "Preview Coordinator", role: "coordinator" },
  admin: { id: 3, email: "preview.admin@example.com", full_name: "Preview Admin", role: "admin" },
};

const history = [48.2, 51.0, 52.4, 55.1, 58.9, 61.3, 63.7].map((score, i) => ({ at: iso(30 - i * 5), score }));

const readiness = {
  latest: {
    id: 7, score: 63.7, probability: 0.66,
    model_version: "readiness-logistic_regression-preview",
    components: {
      values: { predictor: 66, resume: 71.4, mastery: 52.3, interview: 61, consistency: 58.3 },
      missing: [], company_type: "product", data_source: "synthetic-v1",
    },
    weights: { predictor: 0.3, resume: 0.15, mastery: 0.25, interview: 0.15, consistency: 0.15 },
    attributions: [
      { feature: "problems_solved", label: "Coding problems solved", value: 240, baseline: 110, effect: 0.081 },
      { feature: "project_count", label: "Projects", value: 3, baseline: 2, effect: 0.042 },
      { feature: "interview_avg", label: "Mock interview average", value: 61, baseline: 55, effect: 0.018 },
      { feature: "backlogs", label: "Backlogs", value: 1, baseline: 0, effect: -0.035 },
      { feature: "cgpa", label: "CGPA", value: 7.4, baseline: 7.2, effect: 0.009 },
    ],
    created_at: iso(0),
  },
  history,
  change: { score: 2.4, components: { mastery: 4.1, interview: 3.0 } },
};

const jobs = [
  { id: 1, company: "Sample Product Co. (illustrative)", role: "Software Engineer I", type: "product", text: "", required_skills: [{ skill: "data structures", weight: 1 }, { skill: "system design", weight: 0.8 }, { skill: "testing", weight: 0.4 }] },
  { id: 2, company: "Sample Services Ltd. (illustrative)", role: "Graduate Engineer Trainee", type: "service", text: "", required_skills: [{ skill: "aptitude", weight: 1 }, { skill: "communication", weight: 1 }] },
];

const analysis = {
  id: 1, resume_id: 1, jd_id: 1, ats_score: 74.5,
  ats_report: {
    ats_checks: [
      { id: "sections", label: "Standard section headings", points: 20, max_points: 20, passed: true, detail: "Found: education, experience, projects, skills.", fix: "" },
      { id: "parseable", label: "Text is machine-readable", points: 15, max_points: 15, passed: true, detail: "412 words extracted.", fix: "" },
      { id: "contact", label: "Contact details", points: 5, max_points: 10, passed: false, detail: "Email found, phone missing.", fix: "Put email and phone in the header as plain text." },
      { id: "length", label: "Length (about one page)", points: 10, max_points: 10, passed: true, detail: "412 words.", fix: "" },
      { id: "bullets", label: "Bullet points", points: 7.5, max_points: 10, passed: false, detail: "6 bullet lines.", fix: "" },
      { id: "impact", label: "Quantified impact and action verbs", points: 8.8, max_points: 15, passed: false, detail: "1 measurable result, 5 action verbs.", fix: "Start bullets with verbs (built, reduced…) and add numbers (latency −40%, 2k users)." },
      { id: "keywords", label: "Job-description keyword coverage", points: 13.3, max_points: 20, passed: true, detail: "67% of required skills mentioned.", fix: "" },
    ],
    fixes: [], sections: ["education", "experience", "projects", "skills"], embedder: "tfidf-word+char", keyword_coverage: 0.67,
  },
  match_scores: { overall: 0.31, sections: {} },
  skill_gaps: [
    { skill: "system design", category: "design", importance: 0.72, reason: "Required by Sample Product Co. (illustrative) but not found in your resume." },
    { skill: "testing", category: "tools", importance: 0.16, reason: "Required by Sample Product Co. (illustrative) but not found in your resume (only weakly related text)." },
  ],
  skills_found: ["python", "data structures", "algorithms", "sql", "git", "react"],
};

const quiz = {
  id: 1, title: "Data Structures check", skill: "data structures",
  questions: [
    { id: 1, skill: "data structures", difficulty: 1, prompt: "Average time to look up a key in a hash table?", options: ["O(1)", "O(log n)", "O(n)", "O(n log n)"] },
    { id: 2, skill: "data structures", difficulty: 1, prompt: "Which structure gives LIFO order?", options: ["Queue", "Stack", "Heap", "Deque only"] },
    { id: 3, skill: "data structures", difficulty: 1, prompt: "A min-heap's root holds…", options: ["the largest key", "the median", "the smallest key", "a random key"] },
    { id: 4, skill: "data structures", difficulty: 1, prompt: "Inserting at the head of a singly linked list costs…", options: ["O(n)", "O(log n)", "O(1)", "O(n²)"] },
  ],
};
const QUIZ_ANSWERS: Record<number, number> = { 1: 0, 2: 1, 3: 2, 4: 2 };

const cohort = {
  students: 214, scored: 187, mean_score: 58.4, at_risk_count: 41,
  distribution: [0, 2, 6, 14, 19, 33, 45, 38, 21, 9].map((count, i) => ({ range: `${i * 10}-${i * 10 + 9}`, count })),
  departments: [
    { department: "CSE", n: 96, suppressed: false, score: 63.1, predictor: 66.2, resume: 70.4, mastery: 55.0, interview: 60.3, consistency: 52.8 },
    { department: "ECE", n: 64, suppressed: false, score: 55.7, predictor: 57.9, resume: 64.1, mastery: 47.2, interview: 56.4, consistency: 49.9 },
    { department: "MECH", n: 27, suppressed: false, score: 49.8, predictor: 50.3, resume: 58.8, mastery: 41.5, interview: 52.0, consistency: 44.1 },
    { department: "Unspecified", n: 2, suppressed: true },
  ],
  top_skill_gaps: [
    { skill: "system design", students: 88 }, { skill: "aptitude", students: 61 }, { skill: "testing", students: 57 },
    { skill: "communication", students: 44 }, { skill: "dbms", students: 39 },
  ],
  min_group_size: 3,
};

const students = [
  { user_id: 11, name: "Sample Student A", email: "a@example.com", department: "ECE", target: "service", score: 38.5, missing: ["interview"] },
  { user_id: 12, name: "Sample Student B", email: "b@example.com", department: "MECH", target: "product", score: 44.0, missing: [] },
  { user_id: 13, name: "Sample Student C", email: "c@example.com", department: "CSE", target: "product", score: 71.2, missing: [] },
];

const SCOPE_TEXT: Record<string, string> = {
  resume: "Store and analyse my resume.",
  interview_recording: "Record and analyse my mock-interview audio.",
  analytics: "Log my in-app activity to personalise recommendations.",
  coordinator_visibility: "Let placement coordinators see my individual results.",
};

interface Opts {
  method?: string;
  json?: unknown;
  form?: FormData;
}

export async function previewApi(path: string, opts: Opts): Promise<unknown> {
  await new Promise((r) => setTimeout(r, 150));
  const role = previewRole() ?? "student";
  const method = opts.method ?? (opts.json !== undefined || opts.form ? "POST" : "GET");
  const route = path.split("?")[0];

  if (route === "/auth/me") return SAMPLE_USERS[role];
  if (route === "/consents") {
    if (method === "PUT") for (const c of opts.json as { scope: string; granted: boolean }[]) state.consents[c.scope] = c.granted;
    return Object.entries(SCOPE_TEXT).map(([scope, description]) => ({ scope, description, granted: state.consents[scope] }));
  }
  if (route === "/me/readiness" || route === "/me/readiness/refresh") return readiness;
  if (route === "/me/recommendations") return state.recs.filter((r) => r.status === "open" || r.status === "accepted");
  if (route.startsWith("/me/recommendations/")) {
    const id = Number(route.split("/").pop());
    const rec = state.recs.find((r) => r.id === id);
    if (rec) rec.status = (opts.json as { status: string }).status;
    return rec;
  }
  if (route === "/me/mastery") return [
    { skill: "data structures", p_known: 0.78, n_obs: 12 }, { skill: "algorithms", p_known: 0.66, n_obs: 9 },
    { skill: "communication", p_known: 0.58, n_obs: 4 }, { skill: "dbms", p_known: 0.42, n_obs: 4 },
    { skill: "dynamic programming", p_known: 0.31, n_obs: 3 },
  ];
  if (route === "/announcements") return [
    { id: 1, title: "Sample: aptitude mock test on Friday", body: "Room 204, 10 am. Bring your ID card.", created_at: iso(1) },
  ];
  if (route === "/me/profile") return {
    pseudonym_id: "preview", department: "CSE", graduation_year: 2026, gender: null, target_company_type: "product",
    target_role: "Software Engineer", cgpa: 7.4, backlogs: 1, tenth_pct: 88, twelfth_pct: 82, internships: 1,
    ...(method === "PUT" ? (opts.json as object) : {}),
  };
  if (route === "/me/coding") return method === "POST" ? { id: 99, ...(opts.json as object) } : [{ id: 1, platform: "LeetCode", problems_solved: 240, contest_rating: 1610, created_at: iso(3) }];
  if (route === "/me/projects") return method === "POST" ? { id: 99, ...(opts.json as object) } : [{ id: 1, title: "Campus marketplace", complexity: 2 }, { id: 2, title: "Route planner", complexity: 3 }];
  if (route === "/me/certifications") return method === "POST" ? { id: 99, ...(opts.json as object) } : [{ id: 1, name: "AWS Cloud Practitioner", issuer: "AWS" }];
  if (route === "/jobs") return jobs;
  if (route === "/resumes" || route === "/resumes/analyses/latest") return analysis;
  if (route === "/assessments") return [
    { id: 1, title: "Data Structures check", skill: "data structures" }, { id: 2, title: "Dbms check", skill: "dbms" },
    { id: 3, title: "Aptitude check", skill: "aptitude" },
  ];
  if (route.match(/^\/assessments\/\d+$/)) return quiz;
  if (route.match(/^\/assessments\/\d+\/attempts$/)) {
    const answers = (opts.json as { answers: Record<string, number> }).answers;
    const correct = Object.fromEntries(Object.keys(QUIZ_ANSWERS).map((k) => [k, answers[k] === QUIZ_ANSWERS[Number(k)]]));
    const score = (100 * Object.values(correct).filter(Boolean).length) / 4;
    return { id: 1, assessment_id: 1, score, correct };
  }
  if (route === "/interviews/sessions") return {
    id: 1, role: "Software Engineer", company_type: "product", status: "active",
    questions: [
      { id: 1, category: "hr", difficulty: 1, prompt: "Tell me about yourself." },
      { id: 2, category: "behavioral", difficulty: 2, prompt: "Describe a time you handled a conflict in a team project." },
      { id: 3, category: "technical", difficulty: 1, prompt: "What is database normalisation and why does it matter?" },
      { id: 4, category: "dsa", difficulty: 2, prompt: "How would you find whether a linked list has a cycle?" },
    ],
  };
  if (route.match(/^\/interviews\/sessions\/\d+\/answers$/)) {
    const words = String(opts.form?.get("transcript") ?? "").split(/\s+/).filter(Boolean).length;
    const comm = Math.min(95, 40 + words);
    return {
      id: Math.round(Math.random() * 1e6), question_id: Number(opts.form?.get("question_id")), transcript: "",
      scores: { content: 58, communication: comm, delivery: 80, overall: Math.round(0.5 * 58 + 0.3 * comm + 0.2 * 80), details: {} },
      feedback: [
        "Preview feedback: the real API scores your words against the question's key points.",
        words < 40 ? `Your answer was ${words} words; aim for 80-200 with an example.` : "Good length. Add one concrete example with a result.",
      ],
    };
  }
  if (route === "/coordinator/cohort") return cohort;
  if (route === "/coordinator/students") return path.includes("at_risk=true") ? students.filter((s) => s.score < 50) : students;
  if (route === "/admin/models") return [{ version: "readiness-logistic_regression-preview", is_active: true, data_hash: "", metrics: { holdout: { roc_auc: 0.8926, accuracy: 0.7967 }, source: "synthetic-v1" }, created_at: iso(0) }];
  if (route === "/admin/audit") return [
    { id: 2, actor_id: 2, action: "coordinator_viewed_individuals", target: "cohort", created_at: iso(0) },
    { id: 1, actor_id: 3, action: "create_staff", target: "user:2", created_at: iso(1) },
  ];
  if (method !== "GET") return {};
  throw new Error("This part needs the live API. It is not available in preview.");
}
