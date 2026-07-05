def test_refine_prompt_success(client):
    response = client.post(
        "/api/refine-prompt",
        json={"question": "RAG랑 Fine-tuning 뭐가 좋아?", "answer_purpose": "decision_support"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["question_type"] == "comparison"
    assert body["verification_basis"] == "mixed"
    assert body["refined_question"].startswith("[MOCK]")
    assert len(body["suggested_keywords"]) > 0


def test_refine_prompt_question_too_short(client):
    response = client.post(
        "/api/refine-prompt",
        json={"question": "a", "answer_purpose": "fact_check"},
    )
    assert response.status_code == 422


def test_refine_prompt_invalid_answer_purpose(client):
    response = client.post(
        "/api/refine-prompt",
        json={"question": "정상적인 질문입니다", "answer_purpose": "not_a_real_purpose"},
    )
    assert response.status_code == 422


def test_refine_prompt_calculation_detection(client):
    response = client.post(
        "/api/refine-prompt",
        json={"question": "25 × 4는 얼마인가요?", "answer_purpose": "fact_check"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["question_type"] == "calculation"
    assert body["verification_basis"] == "deterministic"
