"""
Stage 3: Hook Analyzer.
Evaluates the first 3 seconds of each candidate promo.
"""
from typing import Tuple
from app.storage.models import PromoCandidate
from app.utils.logging import logger


class HookAnalyzer:
    """Evaluates opening hook power in the first 3 seconds."""

    @classmethod
    def evaluate_hook(cls, candidate: PromoCandidate, first_3s_text: str) -> Tuple[float, str]:
        """
        Evaluates whether something arresting happens in the first 3 seconds:
        - Verbal slap / shocking statement
        - Physical confrontation or reveal
        - High curiosity / low context dependency
        """
        text_lower = first_3s_text.lower()
        score = 7.5
        reasons = []

        # High stopping-power patterns
        if any(w in text_lower for w in ("slap", "stop", "turn around", "not anymore", "marrying", "mistake", "betray", "liar", "killed")):
            score += 1.8
            reasons.append("High stopping power: shocking revelation or confrontational line in first 3 seconds.")

        if any(w in text_lower for w in ("?", "why", "how long", "what do you mean")):
            score += 0.5
            reasons.append("Creates immediate curiosity through an urgent question.")

        if len(first_3s_text.strip()) < 10:
            score -= 2.0
            reasons.append("Weak opening: lacks immediate dialogue or visually arresting action in the first 3 seconds.")

        final_hook_score = round(min(10.0, max(1.0, score)), 1)
        rationale = " ".join(reasons) or "Clear opening moment that establishes character conflict."
        return final_hook_score, rationale
