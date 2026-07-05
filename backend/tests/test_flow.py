import time

TERMINAL_STATUSES = {"completed", "failed"}


def _wait_for_terminal_status(client, question_id: str, timeout: float = 15.0) -> dict:
    deadline = time.monotonic() + timeout
    body = {}
    while time.monotonic() < deadline:
        response = client.get(f"/api/progress/{question_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in TERMINAL_STATUSES:
            return body
        time.sleep(0.2)
    raise AssertionError(f"question {question_id} did not reach a terminal status in time: {body}")


def test_full_mock_analysis_flow(client):
    analyze_response = client.post(
        "/api/analyze",
        json={
            "question": "25 × 4는 얼마야?",
            "original_question": "25 곱하기 4는 얼마야?",
            "refined_question": "25 × 4는 얼마야?",
            "answer_purpose": "fact_check",
        },
    )
    assert analyze_response.status_code == 202
    created = analyze_response.json()
    assert created["status"] == "queued"
    question_id = created["question_id"]

    progress = _wait_for_terminal_status(client, question_id)
    assert progress["status"] == "completed"
    assert progress["progress_percent"] == 100

    summary_response = client.get(f"/api/result/{question_id}")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["status"] == "completed"
    assert 0 <= summary["trust_score"] <= 100
    assert summary["claim_summary"]["total"] > 0

    detail_response = client.get(f"/api/result/{question_id}/detail")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert len(detail["claims"]) == summary["claim_summary"]["total"]
    assert len(detail["deterministic_checks"]) > 0
    assert all(c["check_passed"] for c in detail["deterministic_checks"])

    history_response = client.get("/api/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert any(item["question_id"] == question_id for item in history["items"])

    reanalyze_response = client.post(
        f"/api/reanalyze/{question_id}", json={"answer_purpose": "risk_analysis"}
    )
    assert reanalyze_response.status_code == 202
    reanalyzed = reanalyze_response.json()
    assert reanalyzed["original_question_id"] == question_id
    new_question_id = reanalyzed["question_id"]
    assert new_question_id != question_id

    _wait_for_terminal_status(client, new_question_id)
    new_summary = client.get(f"/api/result/{new_question_id}").json()
    assert new_summary["answer_purpose"] == "risk_analysis"

    original_summary_again = client.get(f"/api/result/{question_id}").json()
    assert original_summary_again["answer_purpose"] == "fact_check"
    assert original_summary_again["trust_score"] == summary["trust_score"]


def test_result_not_found(client):
    response = client.get("/api/result/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "QUESTION_NOT_FOUND"


def test_result_not_ready(client):
    analyze_response = client.post(
        "/api/analyze",
        json={
            "question": "테스트용 질문입니다",
            "original_question": "테스트용 질문입니다",
            "answer_purpose": "fact_check",
        },
    )
    question_id = analyze_response.json()["question_id"]
    response = client.get(f"/api/result/{question_id}")
    if response.status_code == 200:
        return
    assert response.status_code == 409
