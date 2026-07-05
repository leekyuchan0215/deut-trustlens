// Types mirror docs/API_SPEC.md exactly. Field names stay snake_case to match the API contract.

export type AnswerPurpose =
  | "fact_check"
  | "concept_understanding"
  | "decision_support"
  | "evidence_focused"
  | "risk_analysis";

export type QuestionType =
  | "calculation"
  | "simple_fact"
  | "comparison"
  | "current_information"
  | "medical"
  | "legal"
  | "recommendation"
  | "opinion"
  | "general";

export type VerificationBasis =
  | "deterministic"
  | "authoritative_fact"
  | "web_evidence"
  | "mixed"
  | "subjective";

export type AnalysisStatus = "queued" | "processing" | "completed" | "failed";

export type PipelineStage =
  | "question_analysis"
  | "prompt_refinement"
  | "ai_generation"
  | "claim_extraction"
  | "claim_consolidation"
  | "verification_strategy"
  | "deterministic_verification"
  | "search_query_generation"
  | "evidence_search"
  | "document_storage"
  | "chunking"
  | "embedding"
  | "hybrid_search"
  | "evidence_selection"
  | "claim_verification"
  | "cross_review"
  | "risk_analysis"
  | "trust_score"
  | "final_answer"
  | "reflection"
  | "result_storage"
  | "completed"
  | "failed";

export type DisplayStage =
  | "question_analysis"
  | "ai_generation"
  | "claim_extraction"
  | "evidence_search"
  | "hybrid_search"
  | "claim_verification"
  | "final_answer";

export type Provider = "gpt" | "claude" | "gemini";

export type VerificationStatus =
  | "pending"
  | "verified"
  | "weak_evidence"
  | "unsupported"
  | "contradicted";

export type SourceType =
  | "deterministic_verifier"
  | "official"
  | "government"
  | "academic"
  | "paper"
  | "documentation"
  | "news"
  | "blog"
  | "community"
  | "unknown";

export type DisplayStepStatus = "pending" | "processing" | "completed" | "failed";

export type ResultTab =
  | "summary"
  | "ai-responses"
  | "claims"
  | "evidence"
  | "risks"
  | "graph";

export type HistorySort = "newest" | "oldest" | "score_high" | "score_low";

export type CheckType =
  | "calculator"
  | "unit_conversion"
  | "base_conversion"
  | "logic_evaluation"
  | "formula"
  | "safe_code_execution"
  | "rule_based";

export type RiskType =
  | "hallucination"
  | "source_credibility"
  | "outdated_information"
  | "contradiction";

export type RiskLevel = "low" | "medium" | "high";

export type ConsensusLevel = "high" | "medium" | "low";

export type ClaimImportance = "core" | "supporting";

export type ClaimType = "fact" | "opinion" | "recommendation" | string;

export type VerificationMode = "llm_judge" | "deterministic" | string;

// ---------- API error ----------

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}

export class ApiError extends Error {
  code: string;
  details: unknown;
  status?: number;

  constructor(body: ApiErrorBody["error"], status?: number) {
    super(body.message);
    this.code = body.code;
    this.details = body.details;
    this.status = status;
  }
}

// ---------- Health ----------

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  use_mock: boolean;
  database_connected: boolean;
  pgvector_enabled: boolean;
}

// ---------- Refine prompt ----------

export interface RefinePromptRequest {
  question: string;
  answer_purpose: AnswerPurpose;
}

export interface RefinePromptResponse {
  original_question: string;
  refined_question: string;
  answer_purpose: AnswerPurpose;
  question_type: QuestionType;
  verification_basis: VerificationBasis;
  suggested_keywords: string[];
}

// ---------- Analyze ----------

export interface AnalyzeRequest {
  question: string;
  original_question: string;
  refined_question: string;
  answer_purpose: AnswerPurpose;
}

export interface AnalyzeResponse {
  question_id: string;
  status: AnalysisStatus;
  current_stage: PipelineStage;
  display_stage: DisplayStage;
  progress_percent: number;
  message: string;
  created_at: string;
}

// ---------- Progress ----------

export interface DisplayStep {
  stage: DisplayStage;
  label: string;
  status: DisplayStepStatus;
  duration_ms: number | null;
}

export interface ModelStatus {
  provider: Provider;
  model_name: string;
  status: "pending" | "processing" | "success" | "failed";
  latency_ms: number | null;
}

export interface ProgressMetrics {
  total_claims: number;
  verified_claims: number;
  deterministic_checks: number;
  search_documents: number;
  selected_evidences: number;
}

export interface ProgressResponse {
  question_id: string;
  status: AnalysisStatus;
  current_stage: PipelineStage;
  display_stage: DisplayStage;
  progress_percent: number;
  message: string;
  estimated_remaining_seconds: number | null;
  display_steps: DisplayStep[];
  model_statuses: ModelStatus[];
  metrics: ProgressMetrics;
  error_message: string | null;
  updated_at: string;
}

// ---------- Score reason ----------

export interface ScoreReason {
  score: number;
  reason: string;
  verification_basis: VerificationBasis;
  positive_factors: string[];
  negative_factors: string[];
}

export interface CalculationDetail {
  formula: string;
  weighted_scores: Record<string, number>;
  verification_basis: VerificationBasis;
  core_claim_count: number;
  verified_core_claim_count: number;
  weak_core_claim_count: number;
  unsupported_core_claim_count: number;
  contradicted_core_claim_count: number;
  supporting_claim_count: number;
  used_evidence_count: number;
  official_source_count: number;
  deterministic_check_count: number;
}

export interface TrustScoreBreakdown {
  evidence_support_score: number;
  source_quality_score: number;
  consensus_score: number;
  logic_score: number;
  freshness_score: number;
  base_score: number;
  contradiction_penalty: number;
  risk_penalty: number;
  total_score: number;
  grade: string;
  score_reasons: Partial<
    Record<
      "evidence_support" | "source_quality" | "consensus" | "logic" | "freshness",
      ScoreReason
    >
  >;
  strengths: string[];
  deductions: string[];
  calculation_detail: CalculationDetail;
  formula_version: string;
}

// ---------- Model score ----------

export interface ModelScore {
  provider: Provider;
  model_name: string;
  score: number;
  grade: string;
  reason: string;
}

// ---------- Claim summary / source summary ----------

export interface ClaimSummary {
  total: number;
  core: number;
  supporting: number;
  verified: number;
  weak_evidence: number;
  unsupported: number;
  contradicted: number;
}

export interface SourceSummary {
  total_documents: number;
  used_evidences: number;
  web_documents: number;
  academic_papers: number;
  technical_blogs: number;
  official_documents: number;
  government_sources: number;
  deterministic_checks: number;
}

// ---------- Result summary ----------

export interface ResultSummaryResponse {
  question_id: string;
  status: AnalysisStatus;
  original_question: string;
  refined_question: string;
  selected_question: string;
  answer_purpose: AnswerPurpose;
  question_type: QuestionType;
  verification_basis: VerificationBasis;
  trust_score: number;
  grade: string;
  summary: string;
  final_answer: string;
  cautions: string[];
  trust_score_breakdown: TrustScoreBreakdown;
  model_scores: ModelScore[];
  claim_summary: ClaimSummary;
  source_summary: SourceSummary;
  key_issues: string[];
  created_at: string;
  completed_at: string | null;
}

// ---------- AI response ----------

export interface AiResponse {
  id: string;
  provider: Provider;
  model_name: string;
  status: "success" | "failed";
  response_text: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  error_message: string | null;
}

// ---------- Claim ----------

export interface Claim {
  id: string;
  display_id: string;
  claim_text: string;
  normalized_claim: string;
  claim_type: ClaimType;
  importance: ClaimImportance;
  verification_basis: VerificationBasis;
  source_models: Provider[];
  consensus_score: number;
  consensus_level: ConsensusLevel;
  verification_status: VerificationStatus;
  verification_confidence: number;
  verification_reason: string;
  verification_mode: VerificationMode;
  direct_evidence_strength: number;
  cross_source_agreement: number;
  risk_level: RiskLevel;
  evidence_count: number;
  evidence_ids: string[];
  positive_factors: string[];
  deductions: string[];
  limitations: string[];
}

// ---------- Deterministic check ----------

export interface DeterministicCheck {
  id: string;
  claim_id: string;
  check_type: CheckType;
  input_expression: string;
  expected_result: string;
  ai_claimed_result: string;
  check_passed: boolean;
  verification_status: VerificationStatus;
  verification_confidence: number;
  verification_reason: string;
  limitations: string[];
}

// ---------- Evidence ----------

export type EvidenceRelation = "support" | "contradict" | "neutral";

export interface Evidence {
  id: string;
  claim_id: string;
  title: string;
  url: string;
  domain: string;
  snippet: string;
  source_name: string;
  source_type: SourceType;
  published_at: string | null;
  searched_at: string;
  relation: EvidenceRelation;
  keyword_score: number;
  vector_score: number;
  hybrid_score: number;
  source_quality_score: number;
  directness_score: number;
  support_score: number;
  rank: number;
}

// ---------- Cross review ----------

export interface SemanticConsensusItem {
  claim_id: string;
  meaning: string;
  agreeing_models: Provider[];
  consensus_level: ConsensusLevel;
}

export interface MissingPoint {
  description: string;
  affects_core_answer: boolean;
}

export interface CrossReview {
  semantic_consensus: SemanticConsensusItem[];
  consensus: string[];
  contradictions: string[];
  model_additions: Partial<Record<Provider, string[]>>;
  missing_points: MissingPoint[];
  overclaims: string[];
  logic_issues: string[];
  model_strengths: Partial<Record<Provider, string[]>>;
  model_weaknesses: Partial<Record<Provider, string[]>>;
  cross_review_mode: VerificationMode;
}

// ---------- Risk ----------

export interface Risk {
  id: string;
  claim_id: string | null;
  risk_type: RiskType;
  risk_level: RiskLevel;
  description: string;
  affects_core_answer: boolean;
  resolved_by_evidence: boolean;
  penalty: number;
  detected_by: VerificationMode;
}

// ---------- Final result ----------

export interface Citation {
  evidence_id: string;
  title: string;
  url: string;
}

export interface FinalResult {
  summary: string;
  final_answer: string;
  cautions: string[];
  citations: Citation[];
  final_answer_mode: VerificationMode;
  cross_review_mode: VerificationMode;
  judge_provider: string;
  judge_model: string;
  judge_attempts: number;
  fallback_reason: string | null;
}

// ---------- Claim distribution / claim-evidence relations ----------

export interface ClaimDistribution {
  verified: number;
  weak_evidence: number;
  unsupported: number;
  contradicted: number;
}

export interface ClaimEvidenceRelation {
  claim_id: string;
  claim_text: string;
  verification_status: VerificationStatus;
  evidences: {
    evidence_id: string;
    title: string;
    domain: string;
  }[];
}

// ---------- Result detail ----------

export interface ResultDetailResponse {
  question_id: string;
  status: AnalysisStatus;
  original_question: string;
  refined_question: string;
  selected_question: string;
  answer_purpose: AnswerPurpose;
  question_type: QuestionType;
  verification_basis: VerificationBasis;
  ai_responses: AiResponse[];
  model_scores: ModelScore[];
  claims: Claim[];
  deterministic_checks: DeterministicCheck[];
  evidences: Evidence[];
  cross_review: CrossReview;
  risk_analysis: Risk[];
  trust_score_breakdown: TrustScoreBreakdown;
  source_summary: SourceSummary;
  claim_distribution: ClaimDistribution;
  claim_evidence_relations: ClaimEvidenceRelation[];
  final_result: FinalResult;
  created_at: string;
  completed_at: string | null;
}

// ---------- History ----------

export interface HistoryItem {
  question_id: string;
  question: string;
  answer_purpose: AnswerPurpose;
  question_type: QuestionType;
  verification_basis: VerificationBasis;
  status: AnalysisStatus;
  providers: Provider[];
  model_names: string[];
  trust_score: number | null;
  grade: string | null;
  summary: string;
  tags: string[];
  created_at: string;
  completed_at: string | null;
}

export interface HistoryQuery {
  search?: string;
  status?: AnalysisStatus;
  min_score?: number;
  max_score?: number;
  provider?: Provider;
  sort?: HistorySort;
  limit?: number;
  offset?: number;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

// ---------- Reanalyze ----------

export interface ReanalyzeRequest {
  answer_purpose?: AnswerPurpose;
}

export interface ReanalyzeResponse {
  original_question_id: string;
  question_id: string;
  status: AnalysisStatus;
  current_stage: PipelineStage;
  display_stage: DisplayStage;
  progress_percent: number;
  message: string;
  created_at: string;
}
