# TrustLens Development Progress

## 1. 문서 목적

이 문서는 실제로 구현·실행·테스트가 확인된 작업만 기록한다.

완료 기준:

```text
코드 작성
+ 직접 실행
+ 오류 처리 확인
+ 관련 테스트 통과
```

Mock과 Real 구현을 구분한다.

---

## 2. 현재 상태

기준일:

```text
2026-07-05
```

현재 단계:

```text
개발 시작 전 문서 및 UI 설계 완료 단계
```

---

## 3. 준비 완료

```text
[x] 프로젝트 아이디어 정의
[x] PRD 작성
[x] 기능 명세 작성
[x] UI Flow 작성
[x] API 계약 작성
[x] DB Schema 작성
[x] Prompt 명세 작성
[x] Trust Score 기준 작성
[x] 개발 환경 문서 작성
[x] 팀 역할 문서 작성
[x] UI 이미지 10개 설계
[x] UI 이미지 파일명과 화면 연결 정의
[x] Answer Purpose Enum 통일
[x] Verification Basis 추가
[x] Deterministic Check 설계
[x] 추가 설명과 모순 구분 기준 정의
[x] 근거 지지도 산정 이유 구조 정의
```

UI 이미지:

```text
assets/UI/01-home.png
assets/UI/02-prompt_refinement.png
assets/UI/03-loading.png
assets/UI/04-result_summary.png
assets/UI/05-1-detail_analysis.png
assets/UI/05-2-detail_analysis.png
assets/UI/05-3-detail_analysis.png
assets/UI/05-4-detail_analysis.png
assets/UI/05-5-detail_analysis.png
assets/UI/06-history.png
```

---

## 4. 아직 완료되지 않음

### 프로젝트 Skeleton

```text
[ ] Next.js 프로젝트 생성
[ ] FastAPI 프로젝트 생성
[ ] PostgreSQL Docker 실행
[ ] pgvector Extension 활성화
[ ] Alembic 초기화
```

### Frontend

```text
[ ] Sidebar와 Top Header
[ ] Home
[ ] Prompt Refinement Modal
[ ] Loading
[ ] Result Summary
[ ] AI 답변 비교
[ ] Claim 검증
[ ] Evidence
[ ] Risk
[ ] 신뢰성 그래프
[ ] History
[ ] API Client
[ ] Mock Data
[ ] Responsive
[ ] Build
```

### Backend 기본

```text
[ ] FastAPI App
[ ] CORS
[ ] 환경 변수
[ ] DB Session
[ ] 11개 Model
[ ] Pydantic Schema
[ ] Migration
[ ] Mock API
```

### 실제 파이프라인

```text
[ ] GPT
[ ] Claude
[ ] Gemini
[ ] Claim Extraction
[ ] Claim Consolidation
[ ] Verification Strategy
[ ] Deterministic Check
[ ] Tavily
[ ] Chunking
[ ] Embedding
[ ] PostgreSQL FTS
[ ] pgvector Search
[ ] Hybrid Ranking
[ ] Evidence Pack
[ ] Claim Verification
[ ] Cross Review
[ ] Risk Analysis
[ ] 모델별 점수
[ ] Trust Score
[ ] Final Answer
[ ] Reflection
[ ] 결과 저장
```

### 통합과 배포

```text
[ ] Frontend 단독 Mock
[ ] Backend Mock E2E
[ ] Real E2E
[ ] Frontend Build
[ ] Backend Test
[ ] 배포
[ ] 발표 질문 테스트
```

---

## 5. 다음 작업 순서

```text
1. UI 이미지와 문서를 프로젝트에 배치
2. Next.js·FastAPI Skeleton 생성
3. PostgreSQL·pgvector 연결
4. Backend Mock API
5. Frontend Mock·Backend Mock 연결
6. Provider를 하나씩 실제 연결
7. Claim과 검증 파이프라인 구현
8. Trust Score 테스트
9. 전체 E2E
10. 배포와 발표 테스트
```

---

## 6. 점수 관련 필수 테스트

```text
[ ] 추가 설명 차이 → Consensus·Logic 고득점
[ ] 미언급 → 모순 처리 안 함
[ ] 25 × 4 → Deterministic Check 성공
[ ] 원소기호 → 공식 출처 직접 검증
[ ] 최신 날짜 충돌 → Evidence·Freshness 하락
[ ] Supporting Claim 미검증 → 전체 과도한 감점 없음
[ ] 동일 Risk 중복 감점 없음
[ ] 점수 이유 UI 표시 가능
```

---

## 7. 업데이트 규칙

이 문서는 통합 담당자가 실제 실행 결과를 확인한 뒤 수정한다.

잘못된 기록:

```text
코드가 생성됐으므로 완료
Mock 화면이 보이므로 실제 API 완료
문서에 적혀 있으므로 구현 완료
```

올바른 기록:

```text
실행 명령
테스트 결과
성공한 Mode
확인한 화면 또는 API
남은 문제
```
