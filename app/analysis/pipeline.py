"""
Master Promo Discovery Pipeline Orchestrator.
Executes the end-to-end multi-stage pipeline across all uploaded episodes.
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.ai.base_provider import BaseAIProvider
from app.ai.provider_factory import AIProviderFactory
from app.analysis.candidate_detector import CandidateDetector
from app.analysis.episode_analyzer import EpisodeAnalyzer
from app.analysis.quality_checker import QualityChecker
from app.analysis.ranker import PromoRanker
from app.analysis.segment_builder import SegmentBuilder
from app.analysis.validator import PromoValidator
from app.config import Config
from app.storage.models import AnalysisResult, Episode, PromoCandidate
from app.storage.repository import StorageRepository
from app.utils.logging import logger


class PromoDiscoveryPipeline:
    """Orchestrates end-to-end promo discovery, scoring, ranking, and quality auditing."""

    def __init__(self, ai_provider: Optional[BaseAIProvider] = None, repository: Optional[StorageRepository] = None):
        self.ai_provider = ai_provider or AIProviderFactory.get_provider()
        self.repository = repository or StorageRepository()

    def run(
        self,
        episodes: List[Episode],
        screenplay_title: str = "Microdrama Screenplay",
        scan_mode: str = "Standard"
    ) -> AnalysisResult:
        analysis_id = f"RUN_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        logger.info(f"Starting analysis run {analysis_id} on {len(episodes)} episodes (Mode: {scan_mode})")

        if not episodes:
            raise ValueError("No episodes provided for analysis.")

        all_candidates: List[PromoCandidate] = []
        raw_ai_logs: List[Dict] = []
        total_scenes = sum(len(ep.scenes) for ep in episodes)

        # Stage 1 & Stage 2: Process episodes
        # Limit batch according to scan_mode for large packs
        max_episodes_to_scan = len(episodes)
        if scan_mode == "Quick":
            max_episodes_to_scan = min(5, len(episodes))
        elif scan_mode == "Standard":
            max_episodes_to_scan = min(15, len(episodes))
        
        episodes_to_process = episodes[:max_episodes_to_scan]

        candidate_index = 1
        for ep in episodes_to_process:
            logger.info(f"Processing Episode {ep.episode_number} ({len(ep.scenes)} scenes)...")
            
            # Stage 1: Episode Understanding
            ep_summary = EpisodeAnalyzer.analyze_episode(ep, self.ai_provider)
            raw_ai_logs.append({
                "stage": "Stage 1: Episode Understanding",
                "episode": ep.episode_number,
                "summary": ep_summary.model_dump()
            })

            # Stage 2: Candidate Discovery
            moments = CandidateDetector.detect_candidates(ep, self.ai_provider, scan_mode=scan_mode)
            raw_ai_logs.append({
                "stage": "Stage 2: Candidate Discovery",
                "episode": ep.episode_number,
                "moments_count": len(moments),
                "moments": [m.model_dump() for m in moments]
            })

            # Stages 3-6: Continuous Candidate Construction & Validation
            for m in moments:
                cand = SegmentBuilder.build_continuous_candidate(m, ep, candidate_idx=candidate_index)
                if cand:
                    all_candidates.append(cand)
                    candidate_index += 1

        # Stage 7: Multi-segment candidate assembly
        multi_cand = SegmentBuilder.build_multi_segment_candidate(episodes_to_process, candidate_idx=candidate_index)
        if multi_cand:
            all_candidates.append(multi_cand)
            candidate_index += 1

        # Duplicate suppression
        all_candidates = PromoValidator.detect_and_suppress_duplicates(all_candidates)

        # Deterministic Ranking
        ranked_candidates = PromoRanker.rank_promos(all_candidates)

        # Partition into eligible, rejected, and review lists
        eligible_promos = [c for c in ranked_candidates if c.is_eligible and not c.is_near_duplicate_of]
        rejected_promos = [c for c in ranked_candidates if not c.is_eligible]
        review_promos = [c for c in ranked_candidates if c.is_near_duplicate_of or len(c.validation_flags) > 0]

        # Quality audit & failure analysis
        quality_issues, failure_report = QualityChecker.audit_candidates(all_candidates)

        # Determine special designations
        best_overall = eligible_promos[0].promo_id if eligible_promos else None
        
        strongest_hook = max(
            eligible_promos,
            key=lambda c: c.scores.hook_score,
            default=None
        )
        strongest_cliffhanger = max(
            eligible_promos,
            key=lambda c: c.scores.cliffhanger_score,
            default=None
        )
        best_standalone = max(
            eligible_promos,
            key=lambda c: c.scores.standalone_score,
            default=None
        )
        best_multi = next(
            (c for c in eligible_promos if c.promo_type.value == "Multi-segment"),
            None
        )

        result = AnalysisResult(
            analysis_id=analysis_id,
            created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            screenplay_title=screenplay_title,
            total_episodes=len(episodes),
            total_scenes=total_scenes,
            scan_mode=scan_mode,
            ai_provider=self.ai_provider.__class__.__name__,
            ai_model=self.ai_provider.get_model_name(),
            ranked_promos=eligible_promos,
            rejected_promos=rejected_promos,
            review_promos=review_promos,
            quality_issues=quality_issues,
            failure_report=failure_report,
            best_overall_id=best_overall,
            strongest_hook_id=strongest_hook.promo_id if strongest_hook else None,
            strongest_cliffhanger_id=strongest_cliffhanger.promo_id if strongest_cliffhanger else None,
            best_standalone_id=best_standalone.promo_id if best_standalone else None,
            best_multisegment_id=best_multi.promo_id if best_multi else None
        )

        # Persist results
        self.repository.save_analysis(result, raw_responses=raw_ai_logs)
        logger.info(f"Pipeline completed successfully. {len(eligible_promos)} eligible promos discovered.")
        return result
