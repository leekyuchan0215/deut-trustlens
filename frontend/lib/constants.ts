import type {
  AnswerPurpose,
  DisplayStage,
  HistorySort,
  Provider,
  ResultTab,
  RiskType,
  SourceType,
  VerificationBasis,
  VerificationStatus,
} from "./types";

export const MAX_QUESTION_LENGTH = 2000;

export const ANSWER_PURPOSE_OPTIONS: { value: AnswerPurpose; label: string }[] = [
  { value: "fact_check", label: "사실 확인" },
  { value: "concept_understanding", label: "개념 이해" },
  { value: "decision_support", label: "의사 결정" },
  { value: "evidence_focused", label: "근거 중심" },
  { value: "risk_analysis", label: "위험 요소 분석" },
];

export const DEFAULT_ANSWER_PURPOSE: AnswerPurpose = "fact_check";

export const ANSWER_PURPOSE_LABEL: Record<AnswerPurpose, string> = {
  fact_check: "사실 확인",
  concept_understanding: "개념 이해",
  decision_support: "의사 결정",
  evidence_focused: "근거 중심",
  risk_analysis: "위험 요소 분석",
};

export const EXAMPLE_QUESTIONS: string[] = [
  "RAG와 Fine-tuning 중 무엇이 더 좋은 방법인가요?",
  "2024년 하이트 신제품 출시일은?",
  "전기차 배터리는 얼마나 오래 사용할 수 있나요?",
];

export const VERIFICATION_BASIS_LABEL: Record<VerificationBasis, string> = {
  deterministic: "결정적 계산",
  authoritative_fact: "공인된 사실",
  web_evidence: "웹 근거",
  mixed: "혼합",
  subjective: "주관적",
};

export const VERIFICATION_STATUS_LABEL: Record<VerificationStatus, string> = {
  pending: "대기",
  verified: "Verified",
  weak_evidence: "Weak Evidence",
  unsupported: "Unsupported",
  contradicted: "Contradicted",
};

export const SOURCE_TYPE_LABEL: Record<SourceType, string> = {
  deterministic_verifier: "결정적 검증기",
  official: "공식 문서",
  government: "정부 자료",
  academic: "학술 자료",
  paper: "논문",
  documentation: "기술 문서",
  news: "뉴스",
  blog: "블로그",
  community: "커뮤니티",
  unknown: "출처 미상",
};

export const RISK_TYPE_LABEL: Record<RiskType, string> = {
  hallucination: "환각 (Hallucination)",
  source_credibility: "출처 신뢰도",
  outdated_information: "오래된 정보",
  contradiction: "모순 (Contradiction)",
};

export const PROVIDER_LABEL: Record<Provider, string> = {
  gpt: "GPT",
  claude: "Claude",
  gemini: "Gemini",
};

export const DISPLAY_STAGE_LABEL: Record<DisplayStage, string> = {
  question_analysis: "질문 분석",
  ai_generation: "AI 답변 생성",
  claim_extraction: "Claim 추출",
  evidence_search: "외부 근거 검색",
  hybrid_search: "Hybrid Search",
  claim_verification: "Claim 검증",
  final_answer: "최종 답변 생성",
};

export const DISPLAY_STAGE_ORDER: DisplayStage[] = [
  "question_analysis",
  "ai_generation",
  "claim_extraction",
  "evidence_search",
  "hybrid_search",
  "claim_verification",
  "final_answer",
];

export const RESULT_TAB_OPTIONS: { value: ResultTab; label: string }[] = [
  { value: "summary", label: "종합 요약" },
  { value: "ai-responses", label: "AI 답변 비교" },
  { value: "claims", label: "주장 검증" },
  { value: "evidence", label: "근거" },
  { value: "risks", label: "위험 분석" },
  { value: "graph", label: "신뢰성 그래프" },
];

export const DEFAULT_RESULT_TAB: ResultTab = "summary";

export const HISTORY_SORT_OPTIONS: { value: HistorySort; label: string }[] = [
  { value: "newest", label: "최신순" },
  { value: "oldest", label: "오래된순" },
  { value: "score_high", label: "점수 높은순" },
  { value: "score_low", label: "점수 낮은순" },
];

export const HISTORY_SCORE_FILTER_OPTIONS: { value: string; label: string; min?: number; max?: number }[] = [
  { value: "all", label: "전체 점수" },
  { value: "90", label: "90점 이상", min: 90 },
  { value: "75", label: "75점 이상", min: 75 },
  { value: "60", label: "60점 이상", min: 60 },
  { value: "under60", label: "60점 미만", max: 60 },
];

export const HISTORY_PROVIDER_FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "전체 모델" },
  { value: "gpt", label: "GPT" },
  { value: "claude", label: "Claude" },
  { value: "gemini", label: "Gemini" },
];

export const SIDEBAR_ITEMS = [
  { label: "새 질문하기", href: "/", key: "home", implemented: true },
  { label: "대시보드", href: "/analyze", key: "dashboard", implemented: true },
  { label: "검증 기록", href: "/history", key: "history", implemented: true },
  { label: "즐겨찾기", href: "#", key: "favorites", implemented: false },
  { label: "리포트", href: "#", key: "reports", implemented: false },
  { label: "설정", href: "#", key: "settings", implemented: false },
] as const;

export const NOT_READY_MESSAGE = "준비 중인 기능입니다.";

export const MOCK_BANNER_MESSAGE = "UI Mock 데이터 · 실제 AI 검증 결과가 아닙니다.";

export const POLLING_INTERVAL_MS = 2000;
