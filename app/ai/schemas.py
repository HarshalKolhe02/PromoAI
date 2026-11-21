"""
Structured output Pydantic schemas for AI responses in the multi-stage pipeline.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class CharacterProfile(BaseModel):
    name: str
    role_or_relationship: str = ""
    motivation_or_conflict: str = ""


class Stage1EpisodeSummary(BaseModel):
    episode_number: int
    logline: str
    characters: List[CharacterProfile] = Field(default_factory=list)
    key_conflicts: List[str] = Field(default_factory=list)
    secrets_and_revelations: List[str] = Field(default_factory=list)
    emotional_confrontations: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)


class CandidateMoment(BaseModel):
    candidate_id: str
    episode_number: int
    scene_heading: str = ""
    start_time_str: str
    end_time_str: str
    dramatic_core: str = Field(description="What makes this moment high stakes or compelling")
    opening_hook_description: str = Field(description="What happens in the first 3 seconds")
    cliffhanger_description: str = Field(description="The unresolved tension at the end")
    standalone_summary: str = Field(description="Why this makes sense to a new viewer")


class Stage2CandidateDiscovery(BaseModel):
    episode_number: int
    candidate_moments: List[CandidateMoment] = Field(default_factory=list)


class MultiSegmentSequence(BaseModel):
    sequence_id: str
    title: str
    segments: List[dict] = Field(description="List of segments: episode, start, end, narrative role")
    progression: str = Field(description="Hook -> Context -> Escalation -> Cliffhanger flow")
    why_it_works: str


class Stage3Evaluation(BaseModel):
    candidate_id: str
    hook_score: float = Field(ge=0, le=10, description="Hook strength in the first 3 seconds")
    hook_rationale: str
    cliffhanger_score: float = Field(ge=0, le=10, description="Cliffhanger tension score (0-10)")
    cliffhanger_rationale: str
    standalone_score: float = Field(ge=0, le=10, description="Comprehensibility for a new viewer (0-10)")
    standalone_rationale: str
    emotional_impact_score: float = Field(ge=0, le=10, description="Dramatic intensity (0-10)")
    curiosity_score: float = Field(ge=0, le=10, description="Desire to know what happens next (0-10)")
    coherence_score: float = Field(ge=0, le=10, description="Pacing and continuity (0-10)")
    why_it_works: str
    potential_weakness: str
    posting_recommendation: str
    confidence: str = Field(default="High", description="High, Medium, or Low")
