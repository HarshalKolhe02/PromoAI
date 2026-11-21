"""
Candidate validation and hard eligibility verification.
Enforces 20-60s duration, valid timestamps, segment ordering, and duplicate suppression.
"""
from typing import List, Tuple
from app.config import Config
from app.storage.models import PromoCandidate, PromoSegment
from app.utils.logging import logger
from app.utils.timestamps import compute_jaccard_overlap


class PromoValidator:
    """Validates candidate eligibility, timestamp consistency, and detects near-duplicates."""

    @classmethod
    def validate_candidate(cls, candidate: PromoCandidate) -> Tuple[bool, List[str]]:
        """
        Runs deterministic hard eligibility checks on a candidate promo.
        Returns (is_eligible, list_of_warning_flags).
        """
        flags: List[str] = []
        is_eligible = True

        # 1. Total Duration validation (strictly 20s to 60s)
        total_duration = sum(seg.duration_seconds for seg in candidate.segments)
        candidate.total_duration_seconds = round(total_duration, 2)

        if total_duration < Config.MIN_PROMO_DURATION:
            flags.append(f"Hard constraint failed: Total duration ({total_duration:.1f}s) is below minimum of 20.0s.")
            is_eligible = False
        elif total_duration > Config.MAX_PROMO_DURATION:
            flags.append(f"Hard constraint failed: Total duration ({total_duration:.1f}s) exceeds maximum of 60.0s.")
            is_eligible = False

        # 2. Segment timestamp checks
        for idx, seg in enumerate(candidate.segments):
            if seg.start_seconds is None or seg.end_seconds is None:
                flags.append(f"Segment {idx+1} has missing or unparseable timestamps.")
                candidate.has_missing_timestamps = True
                is_eligible = False
            elif seg.end_seconds <= seg.start_seconds:
                flags.append(f"Segment {idx+1} has invalid timestamp sequence: end ({seg.end_time_str}) <= start ({seg.start_time_str}).")
                is_eligible = False

        # 3. Multi-segment chronological and non-overlap checks within the same episode
        if len(candidate.segments) > 1:
            for i in range(len(candidate.segments) - 1):
                cur_seg = candidate.segments[i]
                next_seg = candidate.segments[i + 1]
                if cur_seg.episode_number == next_seg.episode_number:
                    if cur_seg.end_seconds > next_seg.start_seconds:
                        flags.append(f"Segments {i+1} and {i+2} overlap within Episode {cur_seg.episode_number}.")
                        is_eligible = False

        # 4. Hook and Cliffhanger presence check
        if candidate.scores.hook_score < 4.0:
            flags.append("Warning: Weak opening hook (score < 4.0). Requires editorial hook punch-up.")
        if candidate.scores.cliffhanger_score < 4.0:
            flags.append("Warning: Ending has low unresolved tension (score < 4.0).")
        if candidate.scores.standalone_score < 4.0:
            flags.append("Warning: High lore/context dependency (standalone score < 4.0).")

        candidate.validation_flags = flags
        candidate.is_eligible = is_eligible
        return is_eligible, flags

    @classmethod
    def detect_and_suppress_duplicates(
        cls,
        candidates: List[PromoCandidate],
        jaccard_threshold: float = 0.65
    ) -> List[PromoCandidate]:
        """
        Suppresses near-duplicate candidates that reuse substantially the same scene/dialogue timestamps.
        Keeps the higher scoring candidate and marks the other as a near-duplicate.
        """
        for i in range(len(candidates)):
            cand_a = candidates[i]
            if not cand_a.is_eligible or cand_a.is_near_duplicate_of:
                continue

            for j in range(i + 1, len(candidates)):
                cand_b = candidates[j]
                if not cand_b.is_eligible or cand_b.is_near_duplicate_of:
                    continue

                # Check if they share the same primary episode
                if set(cand_a.episodes_involved) & set(cand_b.episodes_involved):
                    # Compute max overlap between primary segments
                    for seg_a in cand_a.segments:
                        for seg_b in cand_b.segments:
                            if seg_a.episode_number == seg_b.episode_number:
                                jaccard = compute_jaccard_overlap(
                                    seg_a.start_seconds, seg_a.end_seconds,
                                    seg_b.start_seconds, seg_b.end_seconds
                                )
                                if jaccard >= jaccard_threshold:
                                    cand_b.is_near_duplicate_of = cand_a.promo_id
                                    cand_b.validation_flags.append(
                                        f"Near-duplicate ({jaccard*100:.0f}% overlap with higher-ranking {cand_a.promo_id})."
                                    )
                                    logger.info(f"Marked {cand_b.promo_id} as near-duplicate of {cand_a.promo_id}")
                                    break
        return candidates
