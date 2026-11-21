"""
Core domain models and Pydantic schemas for screenplay data and promo discovery.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PromoType(str, Enum):
    CONTINUOUS = "Continuous"
    MULTI_SEGMENT = "Multi-segment"


class ReviewStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    EDITED = "Edited"


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class SeverityLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DialogueLine(BaseModel):
    character: str
    tone: Optional[str] = None
    dialogue: str
    start_time_str: Optional[str] = None
    end_time_str: Optional[str] = None
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None


class ActionBlock(BaseModel):
    block_type: str = "ACTION"  # ACTION or CAMERA
    description: str
    start_time_str: Optional[str] = None
    end_time_str: Optional[str] = None
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None


class Scene(BaseModel):
    scene_id: str
    scene_number: int
    heading: str
    start_time_str: Optional[str] = None
    end_time_str: Optional[str] = None
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None
    dialogue_lines: List[DialogueLine] = Field(default_factory=list)
    action_blocks: List[ActionBlock] = Field(default_factory=list)
    raw_text: str = ""


class Episode(BaseModel):
    episode_id: str
    episode_number: int
    title: str = ""
    logline: str = ""
    continuity_notes: str = ""
    scenes: List[Scene] = Field(default_factory=list)
    characters: List[str] = Field(default_factory=list)
    source_filename: str = ""
    raw_text: str = ""


class PromoSegment(BaseModel):
    segment_index: int = 1
    episode_number: int
    start_time_str: str
    end_time_str: str
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    summary: str = ""


class ScoreBreakdown(BaseModel):
    hook_score: float = Field(ge=0, le=10, description="Hook strength (0-10)")
    cliffhanger_score: float = Field(ge=0, le=10, description="Cliffhanger strength (0-10)")
    standalone_score: float = Field(ge=0, le=10, description="Standalone comprehensibility (0-10)")
    emotional_score: float = Field(ge=0, le=10, description="Emotional impact (0-10)")
    curiosity_score: float = Field(ge=0, le=10, description="Narrative curiosity (0-10)")
    coherence_score: float = Field(ge=0, le=10, description="Segment pacing & coherence (0-10)")
    final_score: float = Field(ge=0, le=100, description="Weighted total score (0-100)")


class PromoCandidate(BaseModel):
    promo_id: str
    rank: int = 0
    title: str
    episodes_involved: List[int]
    promo_type: PromoType = PromoType.CONTINUOUS
    total_duration_seconds: float
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    is_eligible: bool = True
    
    segments: List[PromoSegment]
    scores: ScoreBreakdown
    
    hook_explanation: str
    cliffhanger_explanation: str
    standalone_explanation: str
    why_it_works: str
    potential_weakness: str
    posting_recommendation: str
    source_references: List[str] = Field(default_factory=list)
    
    # Quality & validation flags
    validation_flags: List[str] = Field(default_factory=list)
    has_missing_timestamps: bool = False
    is_near_duplicate_of: Optional[str] = None
    
    # Human Review tracking
    review_status: ReviewStatus = ReviewStatus.PENDING
    human_notes: str = ""
    original_ai_version: Optional[Dict] = None


class QualityIssue(BaseModel):
    issue_type: str
    candidate_id: Optional[str] = None
    episode_number: Optional[int] = None
    description: str
    severity: SeverityLevel = SeverityLevel.MEDIUM
    likely_reason: str = ""
    suggested_improvement: str = ""
    human_intervention_required: bool = True
    is_simulated_edge_case: bool = False


class AnalysisResult(BaseModel):
    analysis_id: str
    created_at: str
    screenplay_title: str
    total_episodes: int
    total_scenes: int
    scan_mode: str = "Standard"
    ai_provider: str
    ai_model: str
    
    ranked_promos: List[PromoCandidate] = Field(default_factory=list)
    rejected_promos: List[PromoCandidate] = Field(default_factory=list)
    review_promos: List[PromoCandidate] = Field(default_factory=list)
    
    quality_issues: List[QualityIssue] = Field(default_factory=list)
    failure_report: List[Dict] = Field(default_factory=list)
    
    # Editorial highlights
    best_overall_id: Optional[str] = None
    strongest_hook_id: Optional[str] = None
    strongest_cliffhanger_id: Optional[str] = None
    best_standalone_id: Optional[str] = None
    best_multisegment_id: Optional[str] = None
