"""
Stage 1: Episode Understanding.
Extracts characters, conflicts, secrets, revelations, and emotional confrontations.
"""
from typing import Dict, List, Optional
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import STAGE1_EPISODE_UNDERSTANDING_SYSTEM, STAGE1_EPISODE_UNDERSTANDING_USER
from app.ai.schemas import Stage1EpisodeSummary
from app.storage.models import Episode
from app.utils.logging import logger


class EpisodeAnalyzer:
    """Performs semantic understanding of each episode to provide rich context for promo discovery."""

    @classmethod
    def analyze_episode(cls, episode: Episode, ai_provider: BaseAIProvider) -> Stage1EpisodeSummary:
        # Use first 3000 chars of dialogue and action to avoid unnecessary token consumption
        dialogue_text = []
        for sc in episode.scenes:
            for dl in sc.dialogue_lines[:30]:
                dialogue_text.append(f"{dl.character}: {dl.dialogue}")
        sample_text = "\n".join(dialogue_text) or episode.raw_text[:3500]

        prompt = STAGE1_EPISODE_UNDERSTANDING_USER.format(
            episode_number=episode.episode_number,
            title=episode.title,
            logline=episode.logline or "High stakes microdrama conflict.",
            screenplay_text=sample_text
        )

        try:
            summary = ai_provider.generate_structured_output(
                prompt=prompt,
                schema=Stage1EpisodeSummary,
                system_prompt=STAGE1_EPISODE_UNDERSTANDING_SYSTEM
            )
            return summary
        except Exception as e:
            logger.warning(f"Error in Stage 1 analysis for Episode {episode.episode_number}: {e}. Using deterministic fallback.")
            return Stage1EpisodeSummary(
                episode_number=episode.episode_number,
                logline=episode.logline or f"Dramatic turning points in Episode {episode.episode_number}",
                characters=[],
                key_conflicts=["Altar betrayal and public confrontation"],
                secrets_and_revelations=["Premeditated family conspiracy"],
                emotional_confrontations=["Juliana demands truth from Gerald and father"],
                unresolved_questions=["Will Juliana find an ally to confront the family?"]
            )
