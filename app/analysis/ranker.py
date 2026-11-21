"""
Deterministic weighted promo scoring, ranking, and editorial recommendations.
"""
from typing import Dict, List, Optional
from app.config import Config
from app.storage.models import PromoCandidate, ScoreBreakdown
from app.utils.logging import logger


class PromoRanker:
    """Calculates weighted scores, applies ranking, and determines editorial highlights."""

    @classmethod
    def calculate_weighted_score(
        cls,
        hook: float,
        cliffhanger: float,
        standalone: float,
        emotional: float,
        curiosity: float,
        coherence: float,
        weights: Optional[Dict[str, float]] = None
    ) -> ScoreBreakdown:
        """
        Calculates deterministic final score out of 100 using configured weights.
        Formula:
          Final Score = (Hook × 2.5) + (Cliffhanger × 2.5) + (Standalone × 2.0) +
                        (Emotional × 1.5) + (Curiosity × 1.0) + (Coherence × 0.5)
        """
        w = weights or Config.DEFAULT_WEIGHTS
        
        # Multipliers based on 0-10 input scale to yield 0-100 total
        h_mult = w.get("hook", 25.0) / 10.0          # 2.5
        c_mult = w.get("cliffhanger", 25.0) / 10.0   # 2.5
        s_mult = w.get("standalone", 20.0) / 10.0    # 2.0
        e_mult = w.get("emotional", 15.0) / 10.0     # 1.5
        cu_mult = w.get("curiosity", 10.0) / 10.0    # 1.0
        co_mult = w.get("coherence", 5.0) / 10.0     # 0.5

        raw_final = (
            (hook * h_mult) +
            (cliffhanger * c_mult) +
            (standalone * s_mult) +
            (emotional * e_mult) +
            (curiosity * cu_mult) +
            (coherence * co_mult)
        )
        final_score = round(min(100.0, max(0.0, raw_final)), 1)

        return ScoreBreakdown(
            hook_score=round(hook, 1),
            cliffhanger_score=round(cliffhanger, 1),
            standalone_score=round(standalone, 1),
            emotional_score=round(emotional, 1),
            curiosity_score=round(curiosity, 1),
            coherence_score=round(coherence, 1),
            final_score=final_score
        )

    @classmethod
    def rank_promos(cls, candidates: List[PromoCandidate]) -> List[PromoCandidate]:
        """
        Ranks eligible candidates by final_score descending, with hook_score and cliffhanger_score as tie-breakers.
        Ineligible and duplicate candidates are positioned after eligible candidates.
        """
        eligible = [c for c in candidates if c.is_eligible and not c.is_near_duplicate_of]
        ineligible_or_dup = [c for c in candidates if not c.is_eligible or c.is_near_duplicate_of]

        eligible.sort(
            key=lambda c: (
                c.scores.final_score,
                c.scores.hook_score,
                c.scores.cliffhanger_score,
                c.scores.standalone_score
            ),
            reverse=True
        )

        ineligible_or_dup.sort(
            key=lambda c: c.scores.final_score,
            reverse=True
        )

        ranked_list = eligible + ineligible_or_dup

        # Assign rank numbers
        for rank_num, candidate in enumerate(ranked_list, start=1):
            candidate.rank = rank_num
            # Generate editorial posting rationale if not set
            if not candidate.posting_recommendation:
                candidate.posting_recommendation = cls._generate_posting_reason(rank_num, candidate)

        return ranked_list

    @classmethod
    def _generate_posting_reason(cls, rank: int, candidate: PromoCandidate) -> str:
        if not candidate.is_eligible:
            return "Requires review: do not post until duration/timestamps are resolved."
        if candidate.is_near_duplicate_of:
            return f"Alternative cut: consider posting later as variant of {candidate.is_near_duplicate_of}."
        if rank == 1:
            return "Post first as Primary Campaign Hero Promo: optimal scroll-stopping hook and highest completion potential."
        elif rank == 2:
            return "Post second (Day 2 Retargeting): high dramatic intensity and strong curiosity driver."
        elif rank == 3:
            return "Post third (Day 3 Expansion): excellent standalone story clarity to convert hesitant viewers."
        elif rank <= 5:
            return f"Post in mid-campaign wave (Rank {rank}): solid secondary promo for demographic testing."
        else:
            return f"Post as supplementary social teaser (Rank {rank})."
