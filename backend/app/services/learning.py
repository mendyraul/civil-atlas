from app.schemas import AttemptFeedback, AttemptRequest, LearningActivity, LearningQuestion, Lesson


QUESTIONS = {
    "q-map-rome": ("roman-empire", ["roman empire", "rome"]),
    "q-order": ("roman-empire", ["han dynasty", "roman empire", "aksumite kingdom"]),
    "q-source": ("han-dynasty", []),
    "q-explain": ("parthian-empire", []),
}

LESSONS = [
    Lesson(
        id="lesson-evidence-117", slug="evidence-at-117", title="Reading the world at 117 CE",
        summary="Practice spatial, chronological, and source-based historical reasoning without treating map boundaries as settled fact.",
        activities=[
            LearningActivity(id="activity-map", lesson_id="lesson-evidence-117", activity_type="map_identification", title="Identify an extent", instructions="Use the map or its equivalent table. Cite one visible label or boundary note.", questions=[LearningQuestion(id="q-map-rome", activity_id="activity-map", question_type="map_identification", prompt="Which polity surrounds Roma at 117 CE?", options=["Roman Empire", "Han Dynasty", "Kingdom of Kush"], claim_id="roman-empire", source_id="roman-cambridge")]),
            LearningActivity(id="activity-order", lesson_id="lesson-evidence-117", activity_type="chronological_order", title="Order the polities", instructions="Arrange by start date, earliest first.", questions=[LearningQuestion(id="q-order", activity_id="activity-order", question_type="chronological_order", prompt="Order Han Dynasty, Roman Empire, and Aksumite Kingdom by start date.", options=["Han Dynasty", "Roman Empire", "Aksumite Kingdom"], claim_id="roman-empire", source_id="roman-cambridge")]),
            LearningActivity(id="activity-source", lesson_id="lesson-evidence-117", activity_type="source_analysis", title="Analyze a source", instructions="Explain what the visible confidence and review labels permit us to infer.", questions=[LearningQuestion(id="q-source", activity_id="activity-source", question_type="source_analysis", prompt="Why should the Han boundary be treated as approximate? Cite visible evidence.", claim_id="han-dynasty", source_id="han-cambridge")]),
            LearningActivity(id="activity-compare", lesson_id="lesson-evidence-117", activity_type="compare_contrast", title="Compare and contrast", instructions="Open the comparison workspace and compare at least two polities across governance and evidence quality.", questions=[]),
            LearningActivity(id="activity-explain", lesson_id="lesson-evidence-117", activity_type="short_explanation", title="Explain with evidence", instructions="Write a short explanation and cite a visible map label, table value, source, or uncertainty note.", questions=[LearningQuestion(id="q-explain", activity_id="activity-explain", question_type="short_explanation", prompt="How did Parthia's position support exchange? Cite visible evidence.", claim_id="parthian-empire", source_id="parthia-curtis")]),
        ],
    )
]


def grade_attempt(payload: AttemptRequest) -> AttemptFeedback:
    if payload.question_id not in QUESTIONS:
        raise KeyError(payload.question_id)
    claim_id, expected = QUESTIONS[payload.question_id]
    answer = payload.response if isinstance(payload.response, list) else payload.response.strip().lower()
    correct = answer == expected if isinstance(answer, list) else (not expected or answer in expected)
    evidence_ok = bool(payload.visible_evidence.strip())
    score = (0.7 if correct else 0.0) + (0.3 if evidence_ok else 0.0)
    source_id = next(q.source_id for lesson in LESSONS for activity in lesson.activities for q in activity.questions if q.id == payload.question_id)
    message = ("Correct. " if correct else "Revisit the chronology or active polity. ") + ("Your visible evidence supports the response." if evidence_ok else "Add a visible label, table value, uncertainty note, or source citation.")
    return AttemptFeedback(correct=correct and evidence_ok, score=score, message=message, claim_id=claim_id, claim_url=f"/api/claims#{claim_id}", source_id=source_id, source_url=f"/api/sources#{source_id}", persisted=payload.consent and payload.storage_mode == "account")
