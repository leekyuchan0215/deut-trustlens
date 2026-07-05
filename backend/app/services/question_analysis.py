"""Deterministic (non-LLM) mock classifier used while USE_MOCK=true.

Real mode will replace this with an actual LLM call, but the output shape
(question_type / verification_basis / suggested_keywords) must stay the same.
"""
import re

_CALCULATION_PATTERN = re.compile(
    r"[\d].*[+\-*/×÷%]|[+\-*/×÷%].*[\d]|진법|이진|십육진"
    r"|\d.*(곱하기|더하기|빼기|나누기|곱셈|덧셈|뺄셈|나눗셈)"
)
_CURRENT_INFO_KEYWORDS = ["오늘", "현재", "최근", "환율", "주가", "실시간", "이번 주", "이번 달", "올해"]
_COMPARISON_KEYWORDS = ["비교", " vs ", "vs.", "차이", "뭐가 좋", "어느 것이", "어떤 게"]
_FACT_KEYWORDS = ["원소기호", "수도는", "정의", "뜻은", "무엇인가", "란 무엇"]
_RECOMMENDATION_KEYWORDS = ["추천", "골라", "선택해", "사야"]
_OPINION_KEYWORDS = ["생각해", "의견", "어떻게 생각"]
_MEDICAL_KEYWORDS = ["증상", "질병", "치료", "복용", "부작용"]
_LEGAL_KEYWORDS = ["법률", "계약", "소송", "판례", "위법"]

_STOPWORDS = {"그리고", "그래서", "하지만", "그런데", "위한", "대한", "에서", "으로", "에게"}


def classify_question(question: str) -> tuple[str, str]:
    """Return (question_type, verification_basis) using simple keyword rules."""
    text = question.strip()

    if _CALCULATION_PATTERN.search(text):
        return "calculation", "deterministic"
    if any(k in text for k in _MEDICAL_KEYWORDS):
        return "medical", "mixed"
    if any(k in text for k in _LEGAL_KEYWORDS):
        return "legal", "mixed"
    if any(k in text for k in _COMPARISON_KEYWORDS):
        return "comparison", "mixed"
    if any(k in text for k in _CURRENT_INFO_KEYWORDS):
        return "current_information", "web_evidence"
    if any(k in text for k in _FACT_KEYWORDS):
        return "simple_fact", "authoritative_fact"
    if any(k in text for k in _RECOMMENDATION_KEYWORDS):
        return "recommendation", "mixed"
    if any(k in text for k in _OPINION_KEYWORDS):
        return "opinion", "subjective"
    return "general", "mixed"


def extract_keywords(question: str, limit: int = 5) -> list[str]:
    tokens = re.split(r"[\s,.?!·\"'()]+", question)
    keywords: list[str] = []
    for token in tokens:
        token = token.strip()
        if len(token) < 2 or token in _STOPWORDS:
            continue
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= limit:
            break
    return keywords


def refine_question(question: str, answer_purpose: str, question_type: str) -> str:
    purpose_hint = {
        "fact_check": "정확한 사실 여부를 확인할 수 있도록",
        "concept_understanding": "핵심 개념을 이해하기 쉽게",
        "decision_support": "의사결정에 필요한 비교 기준을 포함해서",
        "evidence_focused": "근거와 출처를 명확히 확인할 수 있도록",
        "risk_analysis": "위험 요소와 한계를 함께 확인할 수 있도록",
    }.get(answer_purpose, "명확한 답변을 받을 수 있도록")

    type_hint = ""
    if question_type == "comparison":
        type_hint = " 비교 기준과 현재 시점을 함께 명시합니다."
    elif question_type == "current_information":
        type_hint = " 기준 시점을 함께 명시합니다."

    stripped = question.strip().rstrip("?.!")
    return f"[MOCK] {stripped}에 대해 {purpose_hint} 구체화한 질문입니다.{type_hint}"
