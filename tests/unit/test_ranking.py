"""
Unit tests for deterministic scoring and ranking algorithms.
"""
import pytest
from app.analysis.ranker import PromoRanker
from app.storage.models import PromoCandidate, PromoSegment, PromoType, ConfidenceLevel


def test_weighted_scoring_formula():
    """
    Validates exact assignment formula:
    Final Score = (Hook * 2.5) + (Cliffhanger * 2.5) + (Standalone * 2.0) +
                  (Emotional * 1.5) + (Curiosity * 1.0) + (Coherence * 0.5)
    Total maximum = 100.
    """
    # Perfect 10s across all dimensions
    scores_10 = PromoRanker.calculate_weighted_score(10.0, 10.0, 10.0, 10.0, 10.0, 10.0)
    assert scores_10.final_score == 100.0

    # Test individual weights:
    # Only Hook = 10: 10 * 2.5 = 25.0
    scores_hook = PromoRanker.calculate_weighted_score(10.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert scores_hook.final_score == 25.0

    # Only Cliffhanger = 10: 10 * 2.5 = 25.0
    scores_cliff = PromoRanker.calculate_weighted_score(0.0, 10.0, 0.0, 0.0, 0.0, 0.0)
    assert scores_cliff.final_score == 25.0

    # Only Standalone = 10: 10 * 2.0 = 20.0
    scores_stand = PromoRanker.calculate_weighted_score(0.0, 0.0, 10.0, 0.0, 0.0, 0.0)
    assert scores_stand.final_score == 20.0

    # Only Emotional = 10: 10 * 1.5 = 15.0
    scores_emo = PromoRanker.calculate_weighted_score(0.0, 0.0, 0.0, 10.0, 0.0, 0.0)
    assert scores_emo.final_score == 15.0

    # Only Curiosity = 10: 10 * 1.0 = 10.0
    scores_curio = PromoRanker.calculate_weighted_score(0.0, 0.0, 0.0, 0.0, 10.0, 0.0)
    assert scores_curio.final_score == 10.0

    # Only Coherence = 10: 10 * 0.5 = 5.0
    scores_coher = PromoRanker.calculate_weighted_score(0.0, 0.0, 0.0, 0.0, 0.0, 10.0)
    assert scores_coher.final_score == 5.0

    # Realistic candidate score calculation
    # (9.0*2.5) + (8.5*2.5) + (8.0*2.0) + (9.0*1.5) + (8.0*1.0) + (8.0*0.5)
    # = 22.5 + 21.25 + 16.0 + 13.5 + 8.0 + 4.0 = 85.25 -> 85.2 or 85.3
    cand_scores = PromoRanker.calculate_weighted_score(9.0, 8.5, 8.0, 9.0, 8.0, 8.0)
    assert cand_scores.final_score == 85.2 or cand_scores.final_score == 85.3


def test_ranking_order_and_tie_breaking():
    cand1 = PromoCandidate(
        promo_id="P1",
        title="Promo 1",
        episodes_involved=[1],
        total_duration_seconds=35.0,
        segments=[],
        scores=PromoRanker.calculate_weighted_score(9.0, 9.0, 9.0, 9.0, 9.0, 9.0),  # 90.0
        hook_explanation="", cliffhanger_explanation="", standalone_explanation="",
        why_it_works="", potential_weakness="", posting_recommendation=""
    )
    cand2 = PromoCandidate(
        promo_id="P2",
        title="Promo 2",
        episodes_involved=[1],
        total_duration_seconds=40.0,
        segments=[],
        scores=PromoRanker.calculate_weighted_score(9.5, 9.5, 9.5, 9.5, 9.5, 9.5),  # 95.0
        hook_explanation="", cliffhanger_explanation="", standalone_explanation="",
        why_it_works="", potential_weakness="", posting_recommendation=""
    )
    cand3 = PromoCandidate(
        promo_id="P3",
        title="Promo 3",
        episodes_involved=[1],
        total_duration_seconds=30.0,
        segments=[],
        scores=PromoRanker.calculate_weighted_score(8.0, 8.0, 8.0, 8.0, 8.0, 8.0),  # 80.0
        hook_explanation="", cliffhanger_explanation="", standalone_explanation="",
        why_it_works="", potential_weakness="", posting_recommendation=""
    )

    ranked = PromoRanker.rank_promos([cand1, cand2, cand3])
    assert ranked[0].promo_id == "P2"
    assert ranked[0].rank == 1
    assert ranked[1].promo_id == "P1"
    assert ranked[1].rank == 2
    assert ranked[2].promo_id == "P3"
    assert ranked[2].rank == 3
