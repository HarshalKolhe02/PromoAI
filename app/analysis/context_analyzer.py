"""
Stage 5: Standalone Context Analyzer.
Evaluates whether a candidate makes sense to a viewer who has never watched the series.
"""
from typing import Tuple
from app.storage.models import PromoCandidate


class ContextAnalyzer:
    """Evaluates standalone comprehensibility for uninitiated social media viewers."""

    @classmethod
    def evaluate_standalone(cls, candidate: PromoCandidate, full_clip_text: str) -> Tuple[float, str]:
        text_lower = full_clip_text.lower()
        score = 8.5
        reasons = []

        # Archetypal, universally understood conflicts boost standalone appeal
        if any(w in text_lower for w in ("marry", "wedding", "husband", "sister", "father", "betray", "love")):
            score += 0.8
            reasons.append("Universal interpersonal stakes (marriage, family, betrayal) require minimal backstory.")

        # Overly dense jargon or deep obscure references reduce standalone appeal
        if any(w in text_lower for w in ("treaty of", "decree 402", "the ancient prophecy", "chapter 4")):
            score -= 2.0
            reasons.append("Contains serialized jargon or lore that may confuse casual first-time viewers.")

        final_score = round(min(10.0, max(1.0, score)), 1)
        rationale = " ".join(reasons) or "Clear character dynamic where the immediate interpersonal conflict is readily discernible."
        return final_score, rationale
