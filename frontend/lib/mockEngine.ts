// Client-side simulation engine backing lib/api.ts when NEXT_PUBLIC_USE_MOCK=true.
// Sessions persist in localStorage so refreshing /analyze or /result keeps working.

import {
  MOCK_TEMPLATES,
  SEED_HISTORY,
  findTemplate,
  type MockTemplate,
} from "@/data/mockData";
import { DISPLAY_STAGE_LABEL, DISPLAY_STAGE_ORDER } from "@/lib/constants";
import {
  AnswerPurpose,
  ApiError,
  DisplayStage,
  DisplayStep,
  HistoryItem,
  HistoryQuery,
  ModelStatus,
  ProgressResponse,
  QuestionType,
  ResultDetailResponse,
  ResultSummaryResponse,
  VerificationBasis,
} from "@/lib/types";

const STORAGE_KEY = "trustlens_mock_sessions";

interface MockSession {
  question_id: string;
  original_question: string;
  refined_question: string;
  selected_question: string;
  answer_purpose: AnswerPurpose;
  template_id: string;
  created_at: string;
  duration_ms: number;
  source: "session";
}

const STAGE_WEIGHTS: Record<DisplayStage, number> = {
  question_analysis: 0.05,
  ai_generation: 0.3,
  claim_extraction: 0.1,
  evidence_search: 0.2,
  hybrid_search: 0.15,
  claim_verification: 0.15,
  final_answer: 0.05,
};

function readSessions(): MockSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as MockSession[];
  } catch {
    return [];
  }
}

function writeSessions(sessions: MockSession[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(-50)));
}

function hashString(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 31 + input.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function exactTemplateMatch(question: string): MockTemplate | undefined {
  const trimmed = question.trim();
  return MOCK_TEMPLATES.find((t) => t.seed_question === trimmed);
}

// Prefer an exact match against a template's own seed question (e.g. the example chips)
// so its curated refined_question/claims stay paired with the question that inspired them.
// Anything else falls back to a stable hash so the same arbitrary question always maps to
// the same mock scoring content across a session.
function templateForQuestion(question: string): MockTemplate {
  const exact = exactTemplateMatch(question);
  if (exact) return exact;
  const idx = hashString(question.trim()) % MOCK_TEMPLATES.length;
  return MOCK_TEMPLATES[idx];
}

const PURPOSE_REFINE_SUFFIX: Record<AnswerPurpose, string> = {
  fact_check: "정확한 사실 관계와 근거를 함께 확인해 주세요.",
  concept_understanding: "핵심 개념과 예시를 포함해 이해하기 쉽게 설명해 주세요.",
  decision_support: "비교 기준과 상황별 장단점을 포함해 설명해 주세요.",
  evidence_focused: "신뢰할 수 있는 출처와 근거를 중심으로 답변해 주세요.",
  risk_analysis: "발생 가능한 위험 요소와 주의사항을 포함해 설명해 주세요.",
};

// Generic refinement used when the question doesn't match a curated template, so the
// suggested question still visibly relates to what the user actually typed.
function genericRefine(question: string, purpose: AnswerPurpose): string {
  const trimmed = question.trim().replace(/[?？.!]+$/, "");
  return `${trimmed}? ${PURPOSE_REFINE_SUFFIX[purpose]}`;
}

export function inferQuestionType(question: string): QuestionType {
  const q = question.toLowerCase();
  if (/[0-9].*[×x*÷/+\-].*[0-9]/.test(q) || /계산|더하기|곱하기|나누기/.test(q)) return "calculation";
  if (/원소기호|원자번호|화학식|수도|정의/.test(q)) return "simple_fact";
  if (/vs|중 무엇|비교|차이점/.test(q)) return "comparison";
  if (/언제|출시일|일정|최신|202\d년/.test(q)) return "current_information";
  if (/추천|어떤.*좋을까|어떤.*나을까/.test(q)) return "recommendation";
  if (/어떻게 생각|의견/.test(q)) return "opinion";
  return "general";
}

export function inferVerificationBasis(questionType: QuestionType): VerificationBasis {
  switch (questionType) {
    case "calculation":
      return "deterministic";
    case "simple_fact":
      return "authoritative_fact";
    case "current_information":
      return "web_evidence";
    case "comparison":
      return "mixed";
    case "recommendation":
    case "opinion":
      return "subjective";
    default:
      return "web_evidence";
  }
}

export function mockRefine(question: string, purpose: AnswerPurpose) {
  const questionType = inferQuestionType(question);
  const verificationBasis = inferVerificationBasis(questionType);
  const exactTemplate = exactTemplateMatch(question);
  const refined = exactTemplate ? exactTemplate.refine(question) : genericRefine(question, purpose);
  const suggestedKeywords = question
    .replace(/[?.!,]/g, "")
    .split(/\s+/)
    .filter((w) => w.length >= 2)
    .slice(0, 5);

  return {
    original_question: question,
    refined_question: refined,
    answer_purpose: purpose,
    question_type: questionType,
    verification_basis: verificationBasis,
    suggested_keywords: suggestedKeywords.length > 0 ? suggestedKeywords : [question],
  };
}

export function mockAnalyze(params: {
  question: string;
  original_question: string;
  refined_question: string;
  answer_purpose: AnswerPurpose;
}) {
  const template = templateForQuestion(params.original_question);
  const question_id = `mock-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const duration_ms = 15000 + Math.round(Math.random() * 4000);

  const session: MockSession = {
    question_id,
    original_question: params.original_question,
    refined_question: params.refined_question,
    selected_question: params.question,
    answer_purpose: params.answer_purpose,
    template_id: template.id,
    created_at: new Date().toISOString(),
    duration_ms,
    source: "session",
  };

  const sessions = readSessions();
  sessions.push(session);
  writeSessions(sessions);

  return {
    question_id,
    status: "queued" as const,
    current_stage: "question_analysis" as const,
    display_stage: "question_analysis" as const,
    progress_percent: 0,
    message: "검증 작업이 생성되었습니다.",
    created_at: session.created_at,
  };
}

// Seed history entries aren't real sessions (no localStorage record), but History links to
// them via the same /result?question_id= route, so resolve them as already-completed sessions.
function seedAsSession(question_id: string): MockSession | undefined {
  const entry = SEED_HISTORY.find((s) => s.question_id === question_id);
  if (!entry) return undefined;
  return {
    question_id: entry.question_id,
    original_question: entry.question,
    refined_question: entry.question,
    selected_question: entry.question,
    answer_purpose: "fact_check",
    template_id: entry.template_id,
    created_at: entry.created_at,
    duration_ms: 0,
    source: "session",
  };
}

function findSession(question_id: string): MockSession | undefined {
  return readSessions().find((s) => s.question_id === question_id) ?? seedAsSession(question_id);
}

function elapsedRatio(session: MockSession): number {
  const elapsed = Date.now() - new Date(session.created_at).getTime();
  return Math.max(0, Math.min(1, elapsed / session.duration_ms));
}

function stageAtRatio(ratio: number): { stage: DisplayStage; stageRatio: number } {
  let acc = 0;
  for (const stage of DISPLAY_STAGE_ORDER) {
    const weight = STAGE_WEIGHTS[stage];
    if (ratio < acc + weight || stage === DISPLAY_STAGE_ORDER[DISPLAY_STAGE_ORDER.length - 1]) {
      const stageRatio = weight === 0 ? 1 : Math.max(0, Math.min(1, (ratio - acc) / weight));
      return { stage, stageRatio };
    }
    acc += weight;
  }
  return { stage: "final_answer", stageRatio: 1 };
}

function buildDisplaySteps(currentStage: DisplayStage, ratio: number): DisplayStep[] {
  const currentIdx = DISPLAY_STAGE_ORDER.indexOf(currentStage);
  return DISPLAY_STAGE_ORDER.map((stage, idx) => {
    const weight = STAGE_WEIGHTS[stage];
    if (idx < currentIdx || ratio >= 1) {
      return {
        stage,
        label: DISPLAY_STAGE_LABEL[stage],
        status: "completed" as const,
        duration_ms: Math.round(weight * 16000),
      };
    }
    if (idx === currentIdx && ratio < 1) {
      return {
        stage,
        label: DISPLAY_STAGE_LABEL[stage],
        status: "processing" as const,
        duration_ms: null,
      };
    }
    return {
      stage,
      label: DISPLAY_STAGE_LABEL[stage],
      status: "pending" as const,
      duration_ms: null,
    };
  });
}

function buildModelStatuses(template: MockTemplate, ratio: number): ModelStatus[] {
  const aiStageStart = STAGE_WEIGHTS.question_analysis;
  return template.ai_responses.map((response, idx) => {
    const share = (idx + 1) / template.ai_responses.length;
    const completionPoint = aiStageStart + STAGE_WEIGHTS.ai_generation * share;
    if (ratio >= completionPoint) {
      return {
        provider: response.provider,
        model_name: response.model_name,
        status: "success" as const,
        latency_ms: response.latency_ms,
      };
    }
    if (ratio >= aiStageStart) {
      return {
        provider: response.provider,
        model_name: response.model_name,
        status: "processing" as const,
        latency_ms: null,
      };
    }
    return {
      provider: response.provider,
      model_name: response.model_name,
      status: "pending" as const,
      latency_ms: null,
    };
  });
}

function interpolate(target: number, ratio: number): number {
  return Math.round(target * Math.min(1, ratio * 1.15));
}

export function mockProgress(question_id: string): ProgressResponse {
  const session = findSession(question_id);
  if (!session) {
    throw new ApiError(
      { code: "QUESTION_NOT_FOUND", message: "요청한 분석 기록을 찾을 수 없습니다.", details: null },
      404,
    );
  }
  const template = findTemplate(session.template_id);
  if (!template) {
    throw new ApiError(
      { code: "QUESTION_NOT_FOUND", message: "요청한 분석 기록을 찾을 수 없습니다.", details: null },
      404,
    );
  }

  const ratio = elapsedRatio(session);
  const completed = ratio >= 1;
  const { stage } = stageAtRatio(ratio);
  const progress_percent = Math.round(ratio * 100);
  const remaining = Math.max(0, Math.round(((1 - ratio) * session.duration_ms) / 1000));

  return {
    question_id,
    status: completed ? "completed" : "processing",
    current_stage: completed ? "completed" : stage,
    display_stage: completed ? "final_answer" : stage,
    progress_percent: completed ? 100 : progress_percent,
    message: completed
      ? "검증이 완료되었습니다."
      : `${DISPLAY_STAGE_LABEL[stage]}을(를) 수행하고 있습니다.`,
    estimated_remaining_seconds: completed ? 0 : remaining,
    display_steps: buildDisplaySteps(stage, ratio),
    model_statuses: buildModelStatuses(template, ratio),
    metrics: {
      total_claims: interpolate(template.claims.length, ratio),
      verified_claims: interpolate(
        template.claims.filter((c) => c.verification_status === "verified").length,
        ratio,
      ),
      deterministic_checks: interpolate(template.deterministic_checks.length, ratio),
      search_documents: interpolate(template.source_summary.total_documents, ratio),
      selected_evidences: interpolate(template.evidences.length, ratio),
    },
    error_message: null,
    updated_at: new Date().toISOString(),
  };
}

function requireCompletedSession(question_id: string): { session: MockSession; template: MockTemplate } {
  const session = findSession(question_id);
  if (!session) {
    throw new ApiError(
      { code: "QUESTION_NOT_FOUND", message: "요청한 분석 기록을 찾을 수 없습니다.", details: null },
      404,
    );
  }
  const template = findTemplate(session.template_id);
  if (!template) {
    throw new ApiError(
      { code: "QUESTION_NOT_FOUND", message: "요청한 분석 기록을 찾을 수 없습니다.", details: null },
      404,
    );
  }
  if (elapsedRatio(session) < 1) {
    throw new ApiError(
      { code: "RESULT_NOT_READY", message: "아직 검증 결과가 준비되지 않았습니다.", details: null },
      409,
    );
  }
  return { session, template };
}

export function mockResultSummary(question_id: string): ResultSummaryResponse {
  const { session, template } = requireCompletedSession(question_id);
  const breakdown = template.trust_score_breakdown;
  const claim_summary = {
    total: template.claims.length,
    core: template.claims.filter((c) => c.importance === "core").length,
    supporting: template.claims.filter((c) => c.importance === "supporting").length,
    verified: template.claims.filter((c) => c.verification_status === "verified").length,
    weak_evidence: template.claims.filter((c) => c.verification_status === "weak_evidence").length,
    unsupported: template.claims.filter((c) => c.verification_status === "unsupported").length,
    contradicted: template.claims.filter((c) => c.verification_status === "contradicted").length,
  };

  return {
    question_id,
    status: "completed",
    original_question: session.original_question,
    refined_question: session.refined_question,
    selected_question: session.selected_question,
    answer_purpose: session.answer_purpose,
    question_type: template.question_type,
    verification_basis: template.verification_basis,
    trust_score: breakdown.total_score,
    grade: breakdown.grade,
    summary: template.summary,
    final_answer: template.final_answer,
    cautions: template.cautions,
    trust_score_breakdown: breakdown,
    model_scores: template.model_scores,
    claim_summary,
    source_summary: template.source_summary,
    key_issues: template.key_issues,
    created_at: session.created_at,
    completed_at: new Date(new Date(session.created_at).getTime() + session.duration_ms).toISOString(),
  };
}

export function mockResultDetail(question_id: string): ResultDetailResponse {
  const { session, template } = requireCompletedSession(question_id);

  const claim_distribution = {
    verified: template.claims.filter((c) => c.verification_status === "verified").length,
    weak_evidence: template.claims.filter((c) => c.verification_status === "weak_evidence").length,
    unsupported: template.claims.filter((c) => c.verification_status === "unsupported").length,
    contradicted: template.claims.filter((c) => c.verification_status === "contradicted").length,
  };

  const claim_evidence_relations = template.claims.map((claim) => ({
    claim_id: claim.id,
    claim_text: claim.claim_text,
    verification_status: claim.verification_status,
    evidences: claim.evidence_ids.map((eid) => {
      const evidence = template.evidences.find((e) => e.id === eid);
      return {
        evidence_id: eid,
        title: evidence?.title ?? "",
        domain: evidence?.domain ?? "",
      };
    }),
  }));

  const final_result = {
    summary: template.summary,
    final_answer: template.final_answer,
    cautions: template.cautions,
    citations: template.evidences.slice(0, 5).map((e) => ({
      evidence_id: e.id,
      title: e.title,
      url: e.url,
    })),
    final_answer_mode: "llm_judge" as const,
    cross_review_mode: template.cross_review.cross_review_mode,
    judge_provider: "claude",
    judge_model: "claude-sonnet-4",
    judge_attempts: 1,
    fallback_reason: null,
  };

  return {
    question_id,
    status: "completed",
    original_question: session.original_question,
    refined_question: session.refined_question,
    selected_question: session.selected_question,
    answer_purpose: session.answer_purpose,
    question_type: template.question_type,
    verification_basis: template.verification_basis,
    ai_responses: template.ai_responses,
    model_scores: template.model_scores,
    claims: template.claims,
    deterministic_checks: template.deterministic_checks,
    evidences: template.evidences,
    cross_review: template.cross_review,
    risk_analysis: template.risk_analysis,
    trust_score_breakdown: template.trust_score_breakdown,
    source_summary: template.source_summary,
    claim_distribution,
    claim_evidence_relations,
    final_result,
    created_at: session.created_at,
    completed_at: new Date(new Date(session.created_at).getTime() + session.duration_ms).toISOString(),
  };
}

function toHistoryItem(
  question_id: string,
  question: string,
  answer_purpose: AnswerPurpose,
  template: MockTemplate,
  status: "processing" | "completed",
  created_at: string,
  completed_at: string | null,
): HistoryItem {
  const breakdown = template.trust_score_breakdown;
  return {
    question_id,
    question,
    answer_purpose,
    question_type: template.question_type,
    verification_basis: template.verification_basis,
    status,
    providers: template.ai_responses.map((r) => r.provider),
    model_names: template.ai_responses.map((r) => r.model_name),
    trust_score: status === "completed" ? breakdown.total_score : null,
    grade: status === "completed" ? breakdown.grade : null,
    summary: template.summary,
    tags: template.tags,
    created_at,
    completed_at,
  };
}

export function mockHistory(query: HistoryQuery): { items: HistoryItem[]; total: number } {
  const seedItems = SEED_HISTORY.map((entry) => {
    const template = findTemplate(entry.template_id);
    if (!template) return null;
    return toHistoryItem(
      entry.question_id,
      entry.question,
      "fact_check",
      template,
      "completed",
      entry.created_at,
      entry.completed_at,
    );
  }).filter((x): x is HistoryItem => x !== null);

  const sessionItems = readSessions().map((session) => {
    const template = findTemplate(session.template_id);
    if (!template) return null;
    const ratio = elapsedRatio(session);
    const completed = ratio >= 1;
    return toHistoryItem(
      session.question_id,
      session.selected_question,
      session.answer_purpose,
      template,
      completed ? "completed" : "processing",
      session.created_at,
      completed
        ? new Date(new Date(session.created_at).getTime() + session.duration_ms).toISOString()
        : null,
    );
  }).filter((x): x is HistoryItem => x !== null);

  let items = [...sessionItems, ...seedItems];

  if (query.search) {
    const term = query.search.toLowerCase();
    items = items.filter(
      (item) =>
        item.question.toLowerCase().includes(term) ||
        item.tags.some((tag) => tag.toLowerCase().includes(term)),
    );
  }
  if (query.provider) {
    items = items.filter((item) => item.providers.includes(query.provider!));
  }
  if (typeof query.min_score === "number") {
    items = items.filter((item) => item.trust_score !== null && item.trust_score >= query.min_score!);
  }
  if (typeof query.max_score === "number") {
    items = items.filter((item) => item.trust_score !== null && item.trust_score < query.max_score!);
  }

  const sort = query.sort ?? "newest";
  items = [...items].sort((a, b) => {
    switch (sort) {
      case "oldest":
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case "score_high":
        return (b.trust_score ?? -1) - (a.trust_score ?? -1);
      case "score_low":
        return (a.trust_score ?? 101) - (b.trust_score ?? 101);
      case "newest":
      default:
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }
  });

  const total = items.length;
  const offset = query.offset ?? 0;
  const limit = query.limit ?? 20;
  return { items: items.slice(offset, offset + limit), total };
}

export function mockReanalyze(question_id: string, answer_purpose?: AnswerPurpose) {
  const session = findSession(question_id);
  if (!session) {
    throw new ApiError(
      { code: "QUESTION_NOT_FOUND", message: "요청한 분석 기록을 찾을 수 없습니다.", details: null },
      404,
    );
  }
  const template = findTemplate(session.template_id);
  const purpose = answer_purpose ?? session.answer_purpose;
  const new_question_id = `mock-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const duration_ms = 15000 + Math.round(Math.random() * 4000);

  const newSession: MockSession = {
    question_id: new_question_id,
    original_question: session.original_question,
    refined_question: session.refined_question,
    selected_question: session.selected_question,
    answer_purpose: purpose,
    template_id: template?.id ?? session.template_id,
    created_at: new Date().toISOString(),
    duration_ms,
    source: "session",
  };
  const sessions = readSessions();
  sessions.push(newSession);
  writeSessions(sessions);

  return {
    original_question_id: question_id,
    question_id: new_question_id,
    status: "queued" as const,
    current_stage: "question_analysis" as const,
    display_stage: "question_analysis" as const,
    progress_percent: 0,
    message: "재검증 작업이 생성되었습니다.",
    created_at: newSession.created_at,
  };
}
