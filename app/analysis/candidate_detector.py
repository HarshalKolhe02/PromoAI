"""
Stage 2: Candidate Moment Detection.
Scans screenplay dialogue and action timestamps to discover potential promo moments.
"""
from typing import List, Optional
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import STAGE2_CANDIDATE_DISCOVERY_SYSTEM, STAGE2_CANDIDATE_DISCOVERY_USER
from app.ai.schemas import Stage2CandidateDiscovery, CandidateMoment
from app.storage.models import Episode
from app.utils.logging import logger
from app.utils.timestamps import parse_timestamp_to_seconds, calculate_duration, format_seconds_to_timestamp


class CandidateDetector:
    """Discovers promotional candidate moments meeting the 20 to 60-second constraint."""

    @classmethod
    def detect_candidates(
        cls,
        episode: Episode,
        ai_provider: BaseAIProvider,
        scan_mode: str = "Standard"
    ) -> List[CandidateMoment]:
        # Form formatted script snippet with timestamps
        lines = []
        for sc in episode.scenes:
            lines.append(f"SCENE: {sc.heading} ({sc.start_time_str} -> {sc.end_time_str})")
            for dl in sc.dialogue_lines:
                lines.append(f"[{dl.start_time_str} - {dl.end_time_str}] {dl.character}: {dl.dialogue}")
            for ab in sc.action_blocks:
                if ab.block_type == "ACTION":
                    lines.append(f"[{ab.start_time_str} - {ab.end_time_str}] ACTION: {ab.description}")

        script_text = "\n".join(lines[:80]) or episode.raw_text[:4000]

        prompt = STAGE2_CANDIDATE_DISCOVERY_USER.format(
            episode_number=episode.episode_number,
            characters=", ".join(episode.characters) or "Ensemble",
            screenplay_text=script_text
        )

        try:
            discovery = ai_provider.generate_structured_output(
                prompt=prompt,
                schema=Stage2CandidateDiscovery,
                system_prompt=STAGE2_CANDIDATE_DISCOVERY_SYSTEM
            )
            candidates = discovery.candidate_moments
        except Exception as e:
            logger.warning(f"Error in Stage 2 candidate detection for Episode {episode.episode_number}: {e}")
            candidates = []

        # If LLM didn't return valid candidates, generate deterministic candidates from timestamps
        if not candidates:
            candidates = cls._generate_deterministic_candidates(episode)

        # Filter and adjust candidate limits based on scan_mode
        if scan_mode == "Quick":
            return candidates[:1]
        elif scan_mode == "Standard":
            return candidates[:3]
        else:  # Deep scan
            return candidates[:5]

    @classmethod
    def _generate_deterministic_candidates(cls, episode: Episode) -> List[CandidateMoment]:
        """Generates continuous candidates directly from scene dialogue timestamps."""
        candidates = []
        for sc in episode.scenes:
            if not sc.dialogue_lines:
                continue
            
            # Find dialogue spans between 20s and 60s
            for i, d_start in enumerate(sc.dialogue_lines):
                if d_start.start_seconds is None:
                    continue
                s_sec = d_start.start_seconds
                for j in range(i + 2, len(sc.dialogue_lines)):
                    d_end = sc.dialogue_lines[j]
                    if d_end.end_seconds is None:
                        continue
                    dur = d_end.end_seconds - s_sec
                    if 25.0 <= dur <= 55.0:
                        cand_id = f"EP{episode.episode_number:02d}_CAND_{len(candidates)+1:02d}"
                        candidates.append(CandidateMoment(
                            candidate_id=cand_id,
                            episode_number=episode.episode_number,
                            scene_heading=sc.heading,
                            start_time_str=d_start.start_time_str or format_seconds_to_timestamp(s_sec),
                            end_time_str=d_end.end_time_str or format_seconds_to_timestamp(d_end.end_seconds),
                            dramatic_core=f"Dramatic confrontation between {d_start.character} and {d_end.character}.",
                            opening_hook_description=f"{d_start.character}: '{d_start.dialogue[:60]}...'",
                            cliffhanger_description=f"Ends abruptly on {d_end.character}: '{d_end.dialogue[:60]}...'",
                            standalone_summary="A sharp emotional confrontation between characters that communicates immediate conflict."
                        ))
                        break
                if len(candidates) >= 2:
                    break

        return candidates
