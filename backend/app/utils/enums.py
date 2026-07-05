from enum import Enum


class AnswerPurpose(str, Enum):
    fact_check = "fact_check"
    concept_understanding = "concept_understanding"
    decision_support = "decision_support"
    evidence_focused = "evidence_focused"
    risk_analysis = "risk_analysis"


class QuestionType(str, Enum):
    calculation = "calculation"
    simple_fact = "simple_fact"
    comparison = "comparison"
    current_information = "current_information"
    medical = "medical"
    legal = "legal"
    recommendation = "recommendation"
    opinion = "opinion"
    general = "general"


class VerificationBasis(str, Enum):
    deterministic = "deterministic"
    authoritative_fact = "authoritative_fact"
    web_evidence = "web_evidence"
    mixed = "mixed"
    subjective = "subjective"


class AnalysisStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class PipelineStage(str, Enum):
    question_analysis = "question_analysis"
    prompt_refinement = "prompt_refinement"
    ai_generation = "ai_generation"
    claim_extraction = "claim_extraction"
    claim_consolidation = "claim_consolidation"
    verification_strategy = "verification_strategy"
    deterministic_verification = "deterministic_verification"
    search_query_generation = "search_query_generation"
    evidence_search = "evidence_search"
    document_storage = "document_storage"
    chunking = "chunking"
    embedding = "embedding"
    hybrid_search = "hybrid_search"
    evidence_selection = "evidence_selection"
    claim_verification = "claim_verification"
    cross_review = "cross_review"
    risk_analysis = "risk_analysis"
    trust_score = "trust_score"
    final_answer = "final_answer"
    reflection = "reflection"
    result_storage = "result_storage"
    completed = "completed"
    failed = "failed"


class DisplayStage(str, Enum):
    question_analysis = "question_analysis"
    ai_generation = "ai_generation"
    claim_extraction = "claim_extraction"
    evidence_search = "evidence_search"
    hybrid_search = "hybrid_search"
    claim_verification = "claim_verification"
    final_answer = "final_answer"


class DisplayStepStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AIProvider(str, Enum):
    gpt = "gpt"
    claude = "claude"
    gemini = "gemini"


class AIResponseStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    timeout = "timeout"


class ClaimType(str, Enum):
    fact = "fact"
    numeric = "numeric"
    calculation = "calculation"
    definition = "definition"
    comparison = "comparison"
    cause_effect = "cause_effect"
    latest_info = "latest_info"
    recommendation = "recommendation"
    opinion = "opinion"


class ClaimImportance(str, Enum):
    core = "core"
    supporting = "supporting"


class VerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    weak_evidence = "weak_evidence"
    unsupported = "unsupported"
    contradicted = "contradicted"


class EvidenceRelation(str, Enum):
    support = "support"
    contradict = "contradict"
    neutral = "neutral"


class SourceType(str, Enum):
    deterministic_verifier = "deterministic_verifier"
    official = "official"
    government = "government"
    academic = "academic"
    paper = "paper"
    documentation = "documentation"
    news = "news"
    blog = "blog"
    community = "community"
    unknown = "unknown"


class RiskType(str, Enum):
    hallucination = "hallucination"
    source_credibility = "source_credibility"
    outdated_information = "outdated_information"
    contradiction = "contradiction"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DeterministicCheckType(str, Enum):
    calculator = "calculator"
    unit_conversion = "unit_conversion"
    base_conversion = "base_conversion"
    logic_evaluation = "logic_evaluation"
    formula = "formula"
    safe_code_execution = "safe_code_execution"
    rule_based = "rule_based"


class ExecutionMode(str, Enum):
    mock = "mock"
    real = "real"


ANSWER_PURPOSE_VALUES = [e.value for e in AnswerPurpose]
QUESTION_TYPE_VALUES = [e.value for e in QuestionType]
VERIFICATION_BASIS_VALUES = [e.value for e in VerificationBasis]
ANALYSIS_STATUS_VALUES = [e.value for e in AnalysisStatus]
PIPELINE_STAGE_VALUES = [e.value for e in PipelineStage]
DISPLAY_STAGE_VALUES = [e.value for e in DisplayStage]
DISPLAY_STEP_STATUS_VALUES = [e.value for e in DisplayStepStatus]
AI_PROVIDER_VALUES = [e.value for e in AIProvider]
AI_RESPONSE_STATUS_VALUES = [e.value for e in AIResponseStatus]
CLAIM_TYPE_VALUES = [e.value for e in ClaimType]
CLAIM_IMPORTANCE_VALUES = [e.value for e in ClaimImportance]
VERIFICATION_STATUS_VALUES = [e.value for e in VerificationStatus]
EVIDENCE_RELATION_VALUES = [e.value for e in EvidenceRelation]
SOURCE_TYPE_VALUES = [e.value for e in SourceType]
RISK_TYPE_VALUES = [e.value for e in RiskType]
RISK_LEVEL_VALUES = [e.value for e in RiskLevel]
DETERMINISTIC_CHECK_TYPE_VALUES = [e.value for e in DeterministicCheckType]
EXECUTION_MODE_VALUES = [e.value for e in ExecutionMode]

# 7-step display pipeline shown on the loading screen, in order.
DISPLAY_STEP_ORDER: list[tuple[str, str]] = [
    ("question_analysis", "질문 분석"),
    ("ai_generation", "AI 답변 생성"),
    ("claim_extraction", "Claim 추출"),
    ("evidence_search", "외부 근거 검색"),
    ("hybrid_search", "Hybrid Search"),
    ("claim_verification", "Claim 검증"),
    ("final_answer", "최종 답변 생성"),
]

# Detailed backend pipeline stages, in execution order, mapped to a display
# stage and the progress_percent reached once that stage completes.
PIPELINE_STEPS: list[tuple[str, str, int]] = [
    ("question_analysis", "question_analysis", 5),
    ("ai_generation", "ai_generation", 25),
    ("claim_extraction", "claim_extraction", 32),
    ("claim_consolidation", "claim_extraction", 36),
    ("verification_strategy", "claim_extraction", 40),
    ("deterministic_verification", "evidence_search", 46),
    ("search_query_generation", "evidence_search", 50),
    ("evidence_search", "evidence_search", 58),
    ("document_storage", "evidence_search", 62),
    ("chunking", "hybrid_search", 68),
    ("embedding", "hybrid_search", 74),
    ("hybrid_search", "hybrid_search", 80),
    ("evidence_selection", "hybrid_search", 84),
    ("claim_verification", "claim_verification", 89),
    ("cross_review", "claim_verification", 92),
    ("risk_analysis", "claim_verification", 94),
    ("trust_score", "final_answer", 96),
    ("final_answer", "final_answer", 98),
    ("result_storage", "final_answer", 99),
    ("completed", "final_answer", 100),
]
