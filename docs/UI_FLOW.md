# TrustLens UI Flow

## 1. 문서 목적

이 문서는 TrustLens Frontend의 화면 구조, 사용자 이동, UI 이미지 참조 기준과 화면별 데이터 요구사항을 정의한다.

Frontend는 `assets/UI` 폴더의 이미지를 실제 시각적 구현 기준으로 사용한다.

```text
assets/UI/
├── 01-home.png
├── 02-prompt_refinement.png
├── 03-loading.png
├── 04-result_summary.png
├── 05-1-detail_analysis.png
├── 05-2-detail_analysis.png
├── 05-3-detail_analysis.png
├── 05-4-detail_analysis.png
├── 05-5-detail_analysis.png
└── 06-history.png
```

우선순위:

```text
시각적 구성 → UI 이미지
API 필드     → docs/API_SPEC.md
점수 계산    → docs/TRUST_SCORE.md
DB 구조      → docs/DB_SCHEMA.md
```

이미지 속 질문, 날짜, 점수, 모델명은 예시 데이터이며 하드코딩하지 않는다.

---

## 2. Route

```text
/                                  질문 입력
/analyze?question_id={uuid}        분석 진행
/result?question_id={uuid}         결과
/history                           검증 기록
```

Result Tab:

```text
/result?question_id={uuid}&tab=summary
/result?question_id={uuid}&tab=ai-responses
/result?question_id={uuid}&tab=claims
/result?question_id={uuid}&tab=evidence
/result?question_id={uuid}&tab=risks
/result?question_id={uuid}&tab=graph
```

기본 Tab:

```text
summary
```

---

## 3. 공통 Layout

Desktop 기준:

```text
┌───────────────┬──────────────────────────────┐
│ Sidebar       │ Top Header                   │
│               ├──────────────────────────────┤
│               │ Main Content                 │
│               │                              │
└───────────────┴──────────────────────────────┘
```

공통 특징:

- 왼쪽 고정 Sidebar
- 상단 Header
- 밝은 Blue·Beige Gradient 배경
- 흰색 또는 반투명 Card
- 넓고 약한 그림자
- 16~24px 수준의 둥근 모서리
- Teal 계열 Primary Action
- Navy 계열 제목

---

## 4. Sidebar

참조:

```text
01-home.png
03-loading.png
04-result_summary.png
06-history.png
```

메뉴:

```text
새 질문하기
대시보드
검증 기록
즐겨찾기
리포트
설정
```

Route와 활성 메뉴:

| Route | 활성 메뉴 |
|---|---|
| `/` | 새 질문하기 |
| `/analyze` | 대시보드 |
| `/result` | 검증 기록 |
| `/history` | 검증 기록 |

MVP에서 미구현 메뉴:

```text
즐겨찾기
리포트
설정
업그레이드
```

동작:

```text
준비 중인 기능입니다.
```

실제 로그인 기능은 없으므로 사용자 이름과 Avatar는 UI용 Placeholder를 사용할 수 있다.

---

## 5. Top Header

왼쪽:

- Breadcrumb
- 페이지 이름

오른쪽:

- 알림 아이콘
- Avatar
- 사용자 또는 Workspace 이름
- Dropdown 아이콘

실제 계정 기능은 MVP에 포함하지 않는다.

---

## 6. Home Page

Route:

```text
/
```

참조:

```text
assets/UI/01-home.png
```

화면 구성:

```text
Hero
질문 입력 Card
답변 목적 선택 Card
검증 시작 Button
최근 질문 Card
```

### Hero

```text
AI 답변을 검증하고 더 신뢰할 수 있는 정보를 얻으세요
궁금한 내용을 질문하면 AI가 답변을 검증해드립니다.
```

### 질문 입력

- 최대 2000자
- 글자 수 표시
- 예시 질문 Chip
- 구체적인 질문 안내 문구

### 답변 목적

| 화면 | API 값 |
|---|---|
| 사실 확인 | `fact_check` |
| 개념 이해 | `concept_understanding` |
| 의사 결정 | `decision_support` |
| 근거 중심 | `evidence_focused` |
| 위험 요소 분석 | `risk_analysis` |

기본값:

```text
fact_check
```

### 검증 시작

```text
질문 Validation
→ POST /api/refine-prompt
→ 질문 개선 Modal
```

### 최근 질문

최대 3개:

- 질문
- Trust Score
- 날짜
- 전체 보기

전체 보기:

```text
/history
```

---

## 7. Prompt Refinement Modal

참조:

```text
assets/UI/02-prompt_refinement.png
```

별도 Route가 아니라 Home 위에 Modal로 표시한다.

구성:

- 어두운 Overlay
- Background Blur
- 원본 질문
- 개선된 질문
- 개선 질문 사용
- 직접 수정
- 원본 질문 사용
- 닫기

동작:

```text
개선 질문 사용
→ POST /api/analyze
→ /analyze?question_id={id}
```

```text
직접 수정
→ Textarea 활성화
→ 수정 질문으로 POST /api/analyze
```

```text
원본 질문 사용
→ 원본으로 POST /api/analyze
```

분석 요청 실패 시 Modal을 유지하고 오류를 표시한다.

접근성:

- Escape로 닫기
- Focus Trap 권장
- Modal 외부 Scroll 방지

---

## 8. Loading Page

Route:

```text
/analyze?question_id={uuid}
```

참조:

```text
assets/UI/03-loading.png
```

상단:

```text
TrustLens가 답변을 검증하고 있습니다
다중 AI 답변 생성, Claim 검증, 외부 근거 검색을 진행합니다.
```

### 모델 상태 Card

```text
GPT
Claude
Gemini
```

표시:

- Provider 아이콘
- 실제 모델명
- 상태
- 응답 시간

### 사용자용 7단계

```text
1. 질문 분석
2. AI 답변 생성
3. Claim 추출
4. 외부 근거 검색
5. Hybrid Search
6. Claim 검증
7. 최종 답변 생성
```

Backend 상세 단계 매핑:

| 화면 단계 | Backend Stage |
|---|---|
| 질문 분석 | `question_analysis`, `prompt_refinement` |
| AI 답변 생성 | `ai_generation` |
| Claim 추출 | `claim_extraction`, `claim_consolidation`, `verification_strategy` |
| 외부 근거 검색 | `deterministic_verification`, `search_query_generation`, `evidence_search`, `document_storage`, `chunking` |
| Hybrid Search | `embedding`, `hybrid_search`, `evidence_selection` |
| Claim 검증 | `claim_verification`, `cross_review`, `risk_analysis` |
| 최종 답변 생성 | `trust_score`, `final_answer`, `reflection`, `result_storage` |

### Progress

- `progress_percent`
- 현재 단계
- 예상 남은 시간
- 단계별 완료 상태

Polling:

```text
2초 간격
completed / failed / Unmount 시 중단
```

완료:

```text
/result?question_id={id}&tab=summary
```

---

## 9. Result 공통 Header

참조:

```text
04-result_summary.png
05-1-detail_analysis.png
05-2-detail_analysis.png
05-3-detail_analysis.png
05-4-detail_analysis.png
05-5-detail_analysis.png
```

표시:

- AI Judge 검증 완료 Badge
- 실제 분석 질문
- 답변 목적
- Question ID
- 공유 버튼
- 리포트 저장 버튼
- 원본 질문
- 개선된 질문

공유와 리포트가 미구현이면 `준비 중인 기능입니다`로 처리한다.

---

## 10. Result Tab

순서:

```text
종합 요약
AI 답변 비교
주장 검증
근거
위험 분석
신뢰성 그래프
```

| 화면 | Query 값 |
|---|---|
| 종합 요약 | `summary` |
| AI 답변 비교 | `ai-responses` |
| 주장 검증 | `claims` |
| 근거 | `evidence` |
| 위험 분석 | `risks` |
| 신뢰성 그래프 | `graph` |

활성 Tab:

- Teal 글자
- 하단 Teal Border
- 굵은 글자

---

## 11. Result Summary

참조:

```text
assets/UI/04-result_summary.png
```

### 상단 2열

왼쪽:

```text
종합 신뢰도 점수
```

오른쪽:

```text
최종 검증 답변
```

### Trust Score

- 원형 Gauge
- `total_score`
- `grade`
- 완료 시간
- Evidence Support
- Source Quality
- Consensus
- Logic
- Freshness
- Contradiction Penalty
- Risk Penalty

구성 점수를 클릭하거나 펼치면 다음을 표시할 수 있어야 한다.

- 점수 이유
- Positive Factors
- Negative Factors
- Verification Basis

특히 Evidence Support에는:

- Core Claim 수
- 검증된 Core Claim 수
- Weak·Unsupported·Contradicted Core Claim 수
- 공식 출처 수
- Deterministic Check 수

### 최종 답변

- Summary 강조 박스
- Final Answer
- Cautions
- Citation

### 요약 Card 4개

```text
주요 쟁점
검증 결과
주의사항
주요 출처
```

### 모델별 신뢰도

```text
GPT
Claude
Gemini
```

- 모델명
- 점수
- 등급
- 간단한 이유

설명이 짧거나 길다는 이유로 점수를 낮추지 않는다.

---

## 12. AI 답변 비교

참조:

```text
assets/UI/05-1-detail_analysis.png
```

상단:

- GPT 답변
- Claude 답변
- Gemini 답변
- 긴 답변 내부 Scroll

하단 2×2:

```text
일치한 내용
상충한 내용
누락된 내용
과도한 주장
```

추가 설명은 상충이 아니라 모델별 추가 정보로 처리한다.

---

## 13. 주장 검증

참조:

```text
assets/UI/05-2-detail_analysis.png
```

Filter:

```text
전체
검증 완료
부분 증거
반박 증거
지원 안됨
```

Table Column:

```text
Claim ID
주장 내용
AI 합의도
검증 결과
근거 수
위험도
```

화면 ID:

```text
C1
C2
C3
```

상태:

```text
Verified
Weak Evidence
Unsupported
Contradicted
```

합의도는 문장 동일성이 아닌 핵심 의미를 기준으로 표시한다.

---

## 14. 근거

참조:

```text
assets/UI/05-3-detail_analysis.png
```

Evidence Card:

- Domain
- Title
- Snippet
- 검색일
- Source Type
- 관련도
- 출처 보기

관련도:

```text
hybrid_score × 100
```

Frontend가 별도 검색 점수를 계산하지 않는다.

Deterministic Check는 웹 URL 없이 별도 검증 Card로 표시할 수 있다.

---

## 15. 위험 분석

참조:

```text
assets/UI/05-4-detail_analysis.png
```

상단:

- Claim 상태 개수 요약

Accordion:

```text
환각
출처 신뢰도
오래된 정보
모순
```

표시:

- Risk Level
- 설명
- 관련 Claim
- Core 영향 여부
- Evidence로 해결 여부
- 적용 Penalty

해결된 낮은 Risk는 Penalty 0일 수 있다.

---

## 16. 신뢰성 그래프

참조:

```text
assets/UI/05-5-detail_analysis.png
```

구성:

### Trust Score 구성

- Evidence Support
- Source Quality
- Consensus
- Logic
- Freshness
- Penalty

### Claim 검증 분포

```text
Verified
Weak Evidence
Unsupported
Contradicted
```

### Claim ↔ Evidence 관계

- Claim 문장
- 상태
- Evidence 개수
- Evidence 제목과 Domain

### Cross Review 요약

```text
일치
상충
누락
과잉 주장
```

복잡한 Network Graph보다 이미지와 같은 Card·Bar 구조를 우선한다.

---

## 17. History

Route:

```text
/history
```

참조:

```text
assets/UI/06-history.png
```

Filter:

- 질문 또는 키워드
- 점수 범위
- Provider
- 정렬

점수 예시:

```text
전체 점수
90점 이상
75점 이상
60점 이상
60점 미만
```

정렬:

```text
최신순
오래된순
점수 높은순
점수 낮은순
```

History Card:

- 질문
- 성공 Provider
- Summary
- Tags
- Trust Score
- 등급
- 날짜
- 결과 보기

진행 중이면 Loading Page로 이동한다.

---

## 18. Mock 표시

Frontend Mock:

```env
NEXT_PUBLIC_USE_MOCK=true
```

표시:

```text
UI Mock 데이터
실제 AI 검증 결과가 아닙니다.
```

Backend Mock도 응답의 실행 모드를 이용해 표시한다.

---

## 19. Responsive

### Desktop

- Sidebar 고정
- AI 답변 3열
- Summary 2열
- 요약 Card 4열

### Tablet

- Sidebar 축소
- 2열 또는 가로 Scroll

### Mobile

- Sidebar Drawer
- 1열 Card
- Result Tab 가로 Scroll
- Claim Table을 Card로 변환
- Filter 세로 배치

---

## 20. 접근성

- 입력 Label 연결
- 색상 외 텍스트 상태 표시
- Button `aria-label`
- Modal Keyboard 접근
- Progress ARIA 속성
- Focus 표시
- 외부 링크 `noopener noreferrer`

---

## 21. 권장 Frontend 구조

```text
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── analyze/page.tsx
│   ├── result/page.tsx
│   └── history/page.tsx
├── components/
│   ├── layout/
│   ├── common/
│   ├── home/
│   ├── analysis/
│   ├── result/
│   └── history/
├── hooks/
│   └── useAnalysisPolling.ts
├── lib/
│   ├── api.ts
│   ├── types.ts
│   ├── constants.ts
│   └── formatters.ts
└── data/
    └── mockData.ts
```

---

## 22. 금지 사항

- UI 이미지 무시
- Sidebar와 Header 제거
- 질문 개선을 별도 Page로 변경
- Result Tab 삭제
- Trust Score를 Frontend에서 재계산
- 이미지 예시 수치 하드코딩
- Mock 결과를 실제 결과처럼 표시
- 존재하지 않는 Citation 생성
- 미구현 기능을 완료된 기능처럼 처리

---

## 23. UI 완료 기준

```text
[ ] UI 이미지 10장 확인
[ ] 공통 Sidebar·Header
[ ] Home 화면 일치
[ ] Prompt Refinement Modal 일치
[ ] Loading 7단계 일치
[ ] Result Summary 일치
[ ] 상세 Tab 5개 일치
[ ] History 화면 일치
[ ] API Data 렌더링
[ ] Mock Data 렌더링
[ ] Error·Loading·Empty 상태
[ ] Desktop Layout
[ ] Mobile 기본 동작
[ ] npm run build 성공
```
