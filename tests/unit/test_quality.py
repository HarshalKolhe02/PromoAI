"""
Unit tests for Quality Control, Failure Analysis, and Human Review tracking.
"""
import pytest
from app.analysis.quality_checker import QualityChecker
from app.storage.models import PromoCandidate, PromoSegment, ScoreBreakdown
from app.analysis.ranker import PromoRanker
from app.storage.repository import StorageRepository


def test_quality_audit_flags_short_duration():
    seg = PromoSegment(
        segment_index=1, episode_number=1,
        start_time_str="00:00", end_time_str="00:15",
        start_seconds=0.0, end_seconds=15.0, duration_seconds=15.0
    )
    cand = PromoCandidate(
        promo_id="QC_SHORT", title="Too Short", episodes_involved=[1],
        total_duration_seconds=15.0, segments=[seg],
        scores=PromoRanker.calculate_weighted_score(8, 8, 8, 8, 8, 8),
        hook_explanation="", cliffhanger_explanation="", standalone_explanation="",
        why_it_works="", potential_weakness="", posting_recommendation=""
    )
    issues, failures = QualityChecker.audit_candidates([cand])
    assert any(i.issue_type == "Duration Under Minimum (Too Short)" for i in issues)
    assert len(failures) >= 3


def test_human_review_isolation():
    repo = StorageRepository()
    # Ensure review update preserves original AI version
    seg = PromoSegment(
        segment_index=1, episode_number=1,
        start_time_str="00:10", end_time_str="00:45",
        start_seconds=10.0, end_seconds=45.0, duration_seconds=35.0
    )
    cand = PromoCandidate(
        promo_id="REV_001", title="Original Title", episodes_involved=[1],
        total_duration_seconds=35.0, segments=[seg],
        scores=PromoRanker.calculate_weighted_score(9, 9, 9, 9, 9, 9),
        hook_explanation="Original AI hook", cliffhanger_explanation="Original AI cliff",
        standalone_explanation="Original AI standalone", why_it_works="", potential_weakness="",
        posting_recommendation=""
    )
    from app.storage.models import AnalysisResult
    res = AnalysisResult(
        analysis_id="TEST_RUN_REV", created_at="2026-11-20", screenplay_title="Test",
        total_episodes=1, total_scenes=1, ai_provider="Mock", ai_model="mock",
        ranked_promos=[cand]
    )
    repo.save_analysis(res)

    updated = repo.update_candidate_review(
        analysis_id="TEST_RUN_REV",
        promo_id="REV_001",
        review_status="Approved",
        human_notes="Approved by senior editor for launch campaign.",
        edited_timestamps="00:10 -> 00:48"
    )
    assert updated is True

    loaded = repo.load_analysis("TEST_RUN_REV")
    assert loaded is not None
    p = loaded.ranked_promos[0]
    assert p.review_status.value == "Approved"
    assert "Approved by senior editor" in p.human_notes
    assert p.original_ai_version is not None
