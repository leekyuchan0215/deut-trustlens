# TrustLens Trust Score Specification

## 1. 목적

Trust Score는 AI 답변의 사실일 확률이 아니라, TrustLens의 검증 기준에 따라 근거·출처·AI 합의·논리·최신성·위험을 종합한 설명 가능한 점수다.

```text
Trust Score 90점 ≠ 사실일 확률 90%
```

최종 점수는 Backend가 계산하며 LLM이나 Frontend가 직접 결정하지 않는다.

---

## 2. 공식

```text
Base Score =
0.40 × Evidence Support
+ 0.20 × Source Quality
+ 0.15 × Consensus
+ 0.15 × Logic
+ 0.10 × Freshness
```

```text
Final Score =
Base Score
- Contradiction Penalty
- Risk Penalty
```

범위:

```text
구성 점수: 0~100
Final Score: 0~100
```

```text
Final Score = min(100, max(0, 계산 결과))
```

---

## 3. 핵심 수정 원칙

### 추가 설명은 불일치가 아니다

```text
GPT: RAG는 외부 정보를 검색한다.
Claude: RAG는 외부 정보를 검색하며 유지보수도 쉽다.
Gemini: RAG는 검색된 외부 지식을 활용한다.
```

핵심 의미가 같다면:

```text
Consensus 높음
Logic 높음
```

감점하지 않는 차이:

- 답변 길이
- 한 모델의 추가 설명
- 한 모델의 설명 생략
- 예시 차이
- 문장 표현 차이
- 설명 순서 차이
- Supporting Claim 수 차이

### 미언급은 반대가 아니다

```text
미언급 ≠ 반대
생략 ≠ 모순
```

중요한 보완 정보는 `missing_points`에 기록하되 자동 Logic 감점하지 않는다.

### 문서 개수보다 검증 품질

```text
공식 문서 1개 > 관련성이 낮은 블로그 30개
```

Evidence Support는 다음을 본다.

- 핵심 Claim을 직접 검증하는가
- 공식·권위 있는 출처인가
- 계산이나 공식으로 확정 가능한가
- 출처 간 결과가 일치하는가
- 반박 근거가 존재하는가
- 최신 정보인지 여부

---

## 4. Verification Basis

```text
deterministic
authoritative_fact
web_evidence
mixed
subjective
```

### deterministic

계산, 진법, 단위 변환, 논리식, 공식, 안전한 코드 실행처럼 독립 검증 가능한 Claim이다.

검증 성공 시:

```text
Evidence Support = 100
Source Quality = 100
Freshness = 100
```

### authoritative_fact

공식 표준이나 권위 있는 출처로 확정 가능한 안정적인 사실이다.

예시:

```text
산소의 원소기호는 O이다.
물의 화학식은 H₂O이다.
```

공식 출처가 직접 지지하면 95~100점이 가능하다.

### web_evidence

현재 상태나 최신 자료가 필요한 정보다.

평가:

- 공식 출처
- 갱신 날짜
- 복수 출처 일치
- AI 핵심 수치 일치

### mixed

확정 사실과 조건부 판단이 섞인 질문이다.

### subjective

하나의 정답보다 목적·조건·관점이 중요한 질문이다.

---

## 5. Claim 중요도

```text
Core Claim Weight = 1.0
Supporting Claim Weight = 0.25
```

Core Claim은 사용자 질문에 직접 답하는 주장이다.

Supporting Claim은 배경, 예시, 어원, 부가 설명이다.

Supporting Claim 하나가 검증되지 않았다고 정확한 핵심 답변 전체가 크게 낮아지지 않아야 한다.

Consensus 계산에서는 Supporting Claim 영향도를 더 낮게 둘 수 있다.

```text
Core Consensus Weight = 1.0
Supporting Consensus Weight = 0.15
```

---

## 6. Evidence Support — 40%

### 일반 Verification Status 점수

| 상태 | 기본 점수 |
|---|---:|
| `verified` | 100 |
| `weak_evidence` | 60 |
| `unsupported` | 20 |
| `contradicted` | 0 |
| `pending` | 0 |

`unsupported`는 근거 부족이고 `contradicted`는 신뢰 가능한 근거가 직접 반박한 경우다.

### Deterministic Claim

```text
check_passed = true → 100
조건·단위 일부 불명확 → 60~85
독립 검증 결과와 다름 → 0
```

### Authoritative Fact

| 상황 | 점수 |
|---|---:|
| 공식 출처가 직접 지지 | 100 |
| 권위 있는 학술·교육 출처가 직접 지지 | 95 |
| 복수의 신뢰 가능한 출처가 일치 | 90~95 |
| 간접 지지 | 70~85 |
| 출처 간 일부 차이 | 50~70 |
| 근거 없음 | 20 |
| 공식 출처가 직접 반박 | 0 |

### Web Evidence Claim

```text
Claim Support Score =
0.60 × Verification Status Score
+ 0.25 × Direct Evidence Strength
+ 0.15 × Cross Source Agreement
```

### 전체 계산

```text
Evidence Support =
Σ(Claim Support Score × Importance Weight)
÷
Σ(Importance Weight)
```

### 낮아지는 경우

- Core Claim 직접 근거 없음
- AI 핵심 수치가 서로 다름
- 공식 출처끼리 충돌
- 최신 정보인데 오래된 자료만 존재
- Evidence보다 강하게 단정
- 조건부 내용을 항상 참으로 표현
- 핵심 Claim 일부만 검증
- 공식 출처가 직접 반박

### 낮아지지 않는 경우

- 검색 문서가 적음
- 공식 출처가 하나뿐임
- 한 모델만 부가 설명
- 다른 모델이 부가 설명 생략
- Supporting Claim 일부 미검증
- 안정적 사실의 게시일 없음
- 계산 문제에 웹 결과 없음

---

## 7. Source Quality — 20%

기본 점수:

| Source Type | 점수 |
|---|---:|
| `deterministic_verifier` | 100 |
| `official` | 100 |
| `government` | 100 |
| `academic` | 95 |
| `paper` | 95 |
| `documentation` | 90 |
| `news` | 80 |
| `blog` | 60 |
| `community` | 40 |
| `unknown` | 20 |

실제로 Claim 검증에 사용한 Evidence만 반영한다.

Claim별 계산:

```text
Claim Source Quality =
0.75 × Best Direct Source
+ 0.25 × Other Reliable Sources Average
```

공식 출처 하나가 직접 검증하면 100점 가능하다.

전체 계산:

```text
Source Quality =
Σ(Claim Source Quality × Importance Weight)
÷
Σ(Importance Weight)
```

---

## 8. Consensus — 15%

Consensus는 문장 유사도가 아니라 핵심 의미의 합의도다.

```text
Claim Consensus =
핵심 의미에 동의한 성공 모델 수
÷
성공 모델 수
× 100
```

예시:

```text
GPT: 동의
Claude: 동의 + 추가 설명
Gemini: 동의
→ Claim Consensus = 100
```

미언급 처리:

- 명시적 반대 → 합의도 하락
- 단순 미언급 → 자동 반대 처리 금지

Provider 참여 보정:

```text
3개 성공 → 최대 100
2개 성공 → 최대 85
1개 성공 → 최대 40
```

예상 범위:

| 상황 | 점수 |
|---|---:|
| 핵심 의미 모두 동일 | 95~100 |
| 핵심 결론 같고 부가 설명만 다름 | 90~100 |
| Core Claim 일부 2:1 | 55~75 |
| 핵심 수치가 다름 | 35~65 |
| 핵심 결론 직접 충돌 | 10~45 |

---

## 9. Logic — 15%

Logic은 100점에서 실제 논리 문제만 차감한다.

```text
Logic Score = 100 - Logic Deductions
```

평가 대상:

- 답변 내부 자기모순
- 최종 답변 자기모순
- 근거 없는 인과관계
- Evidence보다 강한 결론
- Unsupported Core Claim을 사실처럼 사용
- Contradicted Claim 사용
- 조건부 결론을 항상 참으로 일반화
- 사용자 질문에 직접 답하지 못함

평가하지 않음:

- 답변 길이 차이
- 한 모델의 추가 설명
- 한 모델의 설명 생략
- 예시 차이
- 문장 구조 차이
- 일반적인 Missing Point

권장 감점:

| 문제 | 감점 |
|---|---:|
| 핵심 자기모순 | -25 |
| Contradicted Core Claim 사용 | -30 |
| Unsupported Core Claim 확정 사용 | -20 |
| 근거 없는 핵심 인과관계 | -15 |
| 조건부 결론 일반화 | -10 |
| Evidence보다 강한 단정 | -8 |
| 질문에 직접 답하지 못함 | -5~-15 |
| Supporting Claim 과도한 단정 | -2~-4 |
| 단순 생략·추가 설명 차이 | 0 |

핵심 의미가 같고 자기모순이 없다면 일반적으로 95~100점이 가능하다.

---

## 10. Freshness — 10%

### Deterministic

```text
100
```

### 안정적인 공식 사실

```text
95~100
```

게시일이 없다는 이유만으로 감점하지 않는다.

### 최신 정보

| 자료 상태 | 점수 |
|---|---:|
| 현재 공식 데이터 | 100 |
| 30일 이내 | 90~100 |
| 31~90일 | 75~90 |
| 91~365일 | 50~75 |
| 1년 초과 | 20~50 |
| 날짜 불명 | 30~50 |

전체 계산은 Core Claim을 우선한 가중 평균을 사용한다.

---

## 11. Contradiction Penalty

적용 조건:

- Core Claim에 영향
- 두 주장이 동시에 참일 수 없음
- 표현 차이가 아님
- Evidence로 해결되지 않음
- 최종 답변에서 정리되지 않음

적용하지 않음:

- 한 모델의 추가 설명
- 미언급
- 예시 차이
- 길이 차이
- 같은 결론의 다른 표현

| 정도 | Penalty |
|---|---:|
| 없음 | 0 |
| Supporting 경미한 충돌 | 0~3 |
| Core 일부 충돌 | 5~15 |
| 핵심 수치·결론 충돌 | 15~25 |
| 핵심 답변 전체 반대 | 25~30 |

최대 30점이다.

---

## 12. Risk Penalty

Risk Type:

```text
hallucination
source_credibility
outdated_information
contradiction
```

기본:

| Level | Penalty |
|---|---:|
| `low` | 0 |
| `medium` | 5 |
| `high` | 15 |

실제 적용 전 확인:

- Core Claim 영향 여부
- Final Answer 포함 여부
- 공식 Evidence로 해결 여부
- 같은 Risk 중복 여부
- 사용자 오해 가능성

같은 Claim의 같은 Risk는 가장 높은 하나만 반영한다.

같은 모순에 Contradiction Penalty를 적용했다면 Risk Penalty로 다시 차감하지 않는다.

최대 40점이다.

---

## 13. 점수 이유 반환

각 구성 점수는 다음 구조를 반환한다.

```json
{
  "score": 96,
  "reason": "핵심 Claim이 공식 출처에서 검증되었습니다.",
  "verification_basis": "authoritative_fact",
  "positive_factors": [
    "Core Claim 2개 모두 검증됨"
  ],
  "negative_factors": [
    "Supporting Claim 1개의 직접 근거가 제한적임"
  ]
}
```

Evidence Support 추가 정보:

```text
core_claim_count
verified_core_claim_count
weak_core_claim_count
unsupported_core_claim_count
contradicted_core_claim_count
supporting_claim_count
official_source_count
deterministic_check_count
used_evidence_count
```

UI는 낮은 점수의 정확한 이유를 표시할 수 있어야 한다.

---

## 14. 등급

| 점수 | 등급 |
|---|---|
| 90~100 | 신뢰도 매우 높음 |
| 75~89.99 | 신뢰도 높음 |
| 60~74.99 | 신뢰도 보통 |
| 40~59.99 | 신뢰도 낮음 |
| 0~39.99 | 신뢰도 매우 낮음 |

Backend가 등급을 반환한다.

---

## 15. 예시

### 계산

```text
질문: 25 × 4는?
독립 계산: 100
AI 3개: 100
```

```text
Evidence Support 100
Source Quality 100
Consensus 100
Logic 100
Freshness 100
Penalty 0
Final Score 100
```

### 안정적인 사실

```text
질문: 산소와 철의 원소기호는?
Core Claim 2개 공식 출처 검증
Supporting 어원 설명 1개 일부 미검증
```

예상:

```text
Evidence Support 95 이상
Source Quality 95 이상
Consensus 95 이상
Logic 95 이상
```

### 조건부 비교

```text
질문: RAG와 Fine-tuning 중 무엇이 더 좋은가?
```

높은 Logic:

```text
최신 정보와 출처 추적은 RAG가 유리하고,
출력 행동 조정은 Fine-tuning이 유리하다.
```

낮아질 수 있는 표현:

```text
RAG가 모든 상황에서 무조건 더 좋다.
```

---

## 16. 모델별 신뢰도

모델별 점수는 해당 모델이 생성한 Claim 기준으로 계산한다.

반영:

- Core Claim 검증 상태
- Contradicted Claim
- Unsupported Core Claim 단정
- Logic Issue
- Overclaim
- Risk

반영하지 않음:

- 답변 길이
- 추가 설명의 양
- 다른 모델보다 설명이 적음

---

## 17. API 결과 예시

```json
{
  "evidence_support_score": 96,
  "source_quality_score": 100,
  "consensus_score": 98,
  "logic_score": 99,
  "freshness_score": 100,
  "base_score": 98.5,
  "contradiction_penalty": 0,
  "risk_penalty": 0,
  "total_score": 98.5,
  "grade": "신뢰도 매우 높음",
  "score_reasons": {},
  "strengths": [],
  "deductions": [],
  "calculation_detail": {},
  "formula_version": "1.1"
}
```

---

## 18. 테스트

```text
[ ] 추가 설명 차이 → Consensus·Logic 95 이상
[ ] Supporting Claim 미언급 → Core Consensus 큰 감점 없음
[ ] 계산 검증 성공 → Evidence Support 100
[ ] 공식 사실 직접 검증 → Evidence Support 95 이상
[ ] 최신 수치 충돌 → Evidence·Consensus·Freshness 하락
[ ] Core 2개 verified + Supporting 1개 unsupported → 과도한 하락 없음
[ ] 실제 자기모순 → Logic 감점
[ ] 동일 Risk 중복 → 한 번만 감점
[ ] 동일 모순 → Penalty 중복 없음
```

---

## 19. 금지 사항

- 답변 길이 차이로 Logic 감점
- 추가 설명 유무로 Consensus 감점
- 미언급을 모순으로 처리
- Missing Point를 자동 Logic Error 처리
- 검색 문서 수만으로 Evidence Support 계산
- 계산 문제에 웹 결과가 없다고 감점
- 공식 출처 하나뿐이라고 감점
- Supporting Claim을 Core와 같은 비중으로 계산
- 같은 Risk 또는 모순 중복 감점
- 최종 점수 하드코딩
- LLM에게 최종 숫자 결정 요청
- Frontend에서 점수 재계산

---

## 20. 완료 기준

```text
[ ] 의미 기반 Consensus
[ ] 실제 Logic Issue만 감점
[ ] Deterministic Check 반영
[ ] 공식 사실 직접 검증 반영
[ ] Core·Supporting 가중치 분리
[ ] 점수 이유 반환
[ ] 중복 Penalty 방지
[ ] Final Score 0~100
[ ] 테스트 통과
```
