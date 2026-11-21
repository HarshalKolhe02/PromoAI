"""
Unit tests for hard eligibility validation, duration limits, and duplicate suppression.
"""
import pytest
from app.analysis.validator import PromoValidator
from app.analysis.ranker import PromoRanker
from app.storage.models import PromoCandidate, PromoSegment, PromoType


def make_candidate(promo_id: str, start: float, end: float, ep: int = 1) -> PromoCandidate:
    dur = round(end - start, 2)
    seg = PromoSegment(
        segment_index=1,
        episode_number=ep,
        start_time_str=f"00:{int(start):02d}",
        end_time_str=f"00:{int(end):02d}",
        start_seconds=start,
        end_seconds=end,
        duration_seconds=dur,
        summary=""
    )
    return PromoCandidate(
        promo_id=promo_id,
        title=f"Promo {promo_id}",
        episodes_involved=[ep],
        total_duration_seconds=dur,
        segments=[seg],
        scores=PromoRanker.calculate_weighted_score(8.0, 8.0, 8.0, 8.0, 8.0, 8.0),
        hook_explanation="", cliffhanger_explanation="", standalone_explanation="",
        why_it_works="", potential_weakness="", posting_recommendation=""
    )


def test_duration_boundary_rejection():
    # 15s candidate -> must fail
    short_cand = make_candidate("SHORT", 0.0, 15.0)
    eligible, flags = PromoValidator.validate_candidate(short_cand)
    assert eligible is False
    assert any("below minimum" in f for f in flags)

    # 65s candidate -> must fail
    long_cand = make_candidate("LONG", 0.0, 65.0)
    eligible, flags = PromoValidator.validate_candidate(long_cand)
    assert eligible is False
    assert any("exceeds maximum" in f for f in flags)

    # 35s candidate -> must pass
    valid_cand = make_candidate("VALID", 0.0, 35.0)
    eligible, flags = PromoValidator.validate_candidate(valid_cand)
    assert eligible is True


def test_near_duplicate_suppression():
    # Cand A: [10s -> 45s] (35s)
    # Cand B: [12s -> 47s] (35s) - heavy overlap (>70% Jaccard)
    cand_a = make_candidate("CAND_A", 10.0, 45.0)
    cand_b = make_candidate("CAND_B", 12.0, 47.0)

    candidates = [cand_a, cand_b]
    processed = PromoValidator.detect_and_suppress_duplicates(candidates, jaccard_threshold=0.65)
    
    assert processed[0].is_near_duplicate_of is None
    assert processed[1].is_near_duplicate_of == "CAND_A"
