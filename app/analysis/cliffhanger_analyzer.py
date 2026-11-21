"""
Stage 4: Cliffhanger Analyzer.
Evaluates the final moments of a promo candidate for unresolved tension.
"""
from typing import Tuple
from app.storage.models import PromoCandidate


class CliffhangerAnalyzer:
    """Evaluates cliffhanger strength: cuts at maximum unresolved tension."""

    @classmethod
    def evaluate_cliffhanger(cls, candidate: PromoCandidate, ending_text: str) -> Tuple[float, str]:
        """
        Evaluates unresolved tension at the cut point:
        - Unanswered question
        - Interrupted action
        - Impending consequence / threat
        - Dramatic twist
        """
        text_lower = ending_text.lower()
        score = 8.0
        reasons = []

        # Indicators of unresolved tension
        if any(w in text_lower for w in ("never", "changed my mind", "remove her", "too late", "or else", "look at me", "who is that")):
            score += 1.5
            reasons.append("Cuts at peak emotional tension with an unaddressed challenge.")

        if ending_text.strip().endswith("?") or "?" in ending_text:
            score += 0.8
            reasons.append("Leaves an open question lingering in the viewer's mind.")

        # Penalize if it feels like a resolved, calm conclusion
        if any(w in text_lower for w in ("thank you", "goodbye", "everything is fine", "i agree", "resolved")):
            score -= 3.0
            reasons.append("Lower tension: ending resolves the scene instead of leaving it suspended.")

        final_cliffhanger_score = round(min(10.0, max(1.0, score)), 1)
        rationale = " ".join(reasons) or "Cuts abruptly before the conflict is resolved, driving viewers to watch the full episode."
        return final_cliffhanger_score, rationale
