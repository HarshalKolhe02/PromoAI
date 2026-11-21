"""
Storage repository for managing persistent analysis runs, raw AI responses, and human feedback.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from app.config import Config, OUTPUT_DIR, RAW_AI_DIR
from app.storage.models import AnalysisResult, PromoCandidate
from app.utils.logging import logger


class StorageRepository:
    """Manages persistence of parsed screenplays, AI responses, analysis runs, and human edits."""

    def __init__(self, output_dir: Path = OUTPUT_DIR, raw_ai_dir: Path = RAW_AI_DIR):
        self.output_dir = output_dir
        self.raw_ai_dir = raw_ai_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_ai_dir.mkdir(parents=True, exist_ok=True)

    def save_analysis(self, result: AnalysisResult, raw_responses: Optional[List[Dict]] = None) -> Path:
        """
        Saves a full analysis result and isolates raw AI responses.
        """
        run_folder = self.output_dir / result.analysis_id
        run_folder.mkdir(parents=True, exist_ok=True)

        # 1. Main analysis result JSON
        result_file = run_folder / "analysis_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        # 2. Ranked promos specifically for fast access
        ranked_file = run_folder / "ranked_promos.json"
        with open(ranked_file, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in result.ranked_promos], f, indent=2)

        # 3. Quality report & failure analysis
        quality_file = run_folder / "quality_report.json"
        with open(quality_file, "w", encoding="utf-8") as f:
            json.dump({
                "quality_issues": [q.model_dump() for q in result.quality_issues],
                "failure_report": result.failure_report
            }, f, indent=2)

        # 4. Save raw AI responses separately to isolate provenance
        if raw_responses:
            raw_file = self.raw_ai_dir / f"raw_ai_{result.analysis_id}.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(raw_responses, f, indent=2)

        logger.info(f"Successfully saved analysis run {result.analysis_id} to {run_folder}")
        return run_folder

    def load_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Loads an analysis result by its ID."""
        result_file = self.output_dir / analysis_id / "analysis_result.json"
        if not result_file.exists():
            return None
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return AnalysisResult.model_validate(data)

    def list_analyses(self) -> List[Dict]:
        """Lists metadata of all stored analyses."""
        analyses = []
        if not self.output_dir.exists():
            return []
        
        for folder in sorted(self.output_dir.iterdir(), key=os.path.getmtime, reverse=True):
            if folder.is_dir():
                res_file = folder / "analysis_result.json"
                if res_file.exists():
                    try:
                        with open(res_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            analyses.append({
                                "analysis_id": data.get("analysis_id", folder.name),
                                "created_at": data.get("created_at", ""),
                                "screenplay_title": data.get("screenplay_title", "Unknown"),
                                "total_episodes": data.get("total_episodes", 0),
                                "eligible_promos": len(data.get("ranked_promos", [])),
                                "model": f"{data.get('ai_provider')}:{data.get('ai_model')}"
                            })
                    except Exception as e:
                        logger.warning(f"Error reading {res_file}: {e}")
        return analyses

    def update_candidate_review(self, analysis_id: str, promo_id: str, review_status: str, human_notes: str, edited_timestamps: Optional[str] = None) -> bool:
        """
        Updates human review status for a specific promo candidate while preserving the original AI output.
        """
        from app.storage.models import ReviewStatus
        result = self.load_analysis(analysis_id)
        if not result:
            return False

        found = False
        status_enum = ReviewStatus(review_status) if isinstance(review_status, str) else review_status
        for promo in result.ranked_promos + result.rejected_promos + result.review_promos:
            if promo.promo_id == promo_id:
                if promo.original_ai_version is None:
                    # Preserve original AI output before editing
                    promo.original_ai_version = promo.model_dump()
                promo.review_status = status_enum
                promo.human_notes = human_notes
                if edited_timestamps:
                    promo.validation_flags.append(f"Editor note: timestamps updated to {edited_timestamps}")
                found = True
                break

        if found:
            self.save_analysis(result)
            return True
        return False
