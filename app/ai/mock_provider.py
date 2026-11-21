"""
Deterministic, offline Mock AI Provider for testing and local analysis without consuming credits.
Provides realistic, contextual candidate evaluations based on screenplay content.
"""
import json
import re
from typing import Optional, Tuple, Type
from pydantic import BaseModel
from app.ai.base_provider import BaseAIProvider
from app.ai.schemas import (
    Stage1EpisodeSummary,
    CharacterProfile,
    Stage2CandidateDiscovery,
    CandidateMoment,
    Stage3Evaluation
)
from app.utils.timestamps import parse_timestamp_to_seconds, calculate_duration, format_seconds_to_timestamp


class MockAIProvider(BaseAIProvider):
    """
    Mock AI Provider that inspects screenplay text deterministically to generate
    plausible, high-quality promotional candidates without making external network calls.
    """

    def __init__(self, model_name: str = "mock-deterministic-v1", temperature: float = 0.2, timeout: int = 120, max_retries: int = 2):
        super().__init__(model_name, temperature, timeout, max_retries)

    def check_connection(self) -> Tuple[bool, str]:
        return True, "Mock AI Provider is active (Offline / Zero Credit Consumption mode)."

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "Mock AI Provider text response for analysis."

    def generate_structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        """Generates realistic structured responses matching the schema."""
        if schema == Stage1EpisodeSummary:
            return self._generate_stage1_summary(prompt)
        elif schema == Stage2CandidateDiscovery:
            return self._generate_stage2_candidates(prompt)
        elif schema == Stage3Evaluation:
            return self._generate_stage3_evaluation(prompt)
        else:
            # Fallback to schema default or mock dictionary
            try:
                return schema()
            except Exception:
                return schema.model_validate({})

    def _generate_stage1_summary(self, prompt: str) -> Stage1EpisodeSummary:
        ep_match = re.search(r"Episode Number:\s*(\d+)", prompt)
        ep_num = int(ep_match.group(1)) if ep_match else 1
        
        return Stage1EpisodeSummary(
            episode_number=ep_num,
            logline=f"High-stakes confrontation and public betrayal unfolds in Episode {ep_num}.",
            characters=[
                CharacterProfile(name="LADY JULIANA", role_or_relationship="Betrayed Bride / Protagonist", motivation_or_conflict="Demands dignity and truth after being humiliated at the altar."),
                CharacterProfile(name="GERALD", role_or_relationship="Former Groom / Antagonist", motivation_or_conflict="Coldly abandons Juliana for Clarissa to secure noble alliances."),
                CharacterProfile(name="CLARISSA / LADY IN GOLD GOWN", role_or_relationship="Cruel Sister / Rival", motivation_or_conflict="Ruthlessly usurps Juliana's betrothal and family status."),
                CharacterProfile(name="MATRIARCH", role_or_relationship="Family Matriarch", motivation_or_conflict="Enforces family ruthless ambition over Juliana's happiness.")
            ],
            key_conflicts=[
                "Altar betrayal: Gerald rejects Juliana for her sister in front of high society.",
                "Family collusion: Juliana's father and matriarch openly support Clarissa's usurpation.",
                "Public humiliation: Juliana is cast out while wearing her late mother's wedding gown."
            ],
            secrets_and_revelations=[
                "The wedding switch was premeditated by the entire family.",
                "Juliana's dowry and inheritance are tied to the rejected match."
            ],
            emotional_confrontations=[
                "Juliana confronts Gerald holding Clarissa's hand at the altar.",
                "Matriarch commands Juliana to leave and silences her protests.",
                "Juliana begs her silent father for support before turning into righteous fury."
            ],
            unresolved_questions=[
                "Will Juliana submit to the family's decree or defy them publicly?",
                "Who will step forward to rescue or ally with the abandoned bride?"
            ]
        )

    def _generate_stage2_candidates(self, prompt: str) -> Stage2CandidateDiscovery:
        ep_match = re.search(r"Episode Number:\s*(\d+)", prompt)
        ep_num = int(ep_match.group(1)) if ep_match else 1

        # Extract timestamps present in the prompt to form realistic continuous clips
        timestamps = re.findall(r"\((\d{1,2}:\d{2}(?:\.\d+)?)\)", prompt)
        valid_seconds = sorted(list(set(filter(None, [parse_timestamp_to_seconds(ts) for ts in timestamps]))))

        candidates = []
        if len(valid_seconds) >= 4:
            # Candidate 1: Altar Shock (38s)
            s1 = valid_seconds[min(3, len(valid_seconds)-1)]
            target_e1 = s1 + 38.0
            # Find closest timestamp
            e1 = min(valid_seconds, key=lambda x: abs(x - target_e1) if x > s1 + 22.0 else 999.0)
            if e1 <= s1 or (e1 - s1) < 20.0 or (e1 - s1) > 60.0:
                e1 = s1 + 38.0

            candidates.append(CandidateMoment(
                candidate_id=f"EP{ep_num:02d}_CAND_01",
                episode_number=ep_num,
                scene_heading="INT. CATHEDRAL – DAY",
                start_time_str=format_seconds_to_timestamp(s1),
                end_time_str=format_seconds_to_timestamp(e1),
                dramatic_core="Juliana arrives at the altar only to discover her groom holding her sister's hand.",
                opening_hook_description="Juliana freezes as the Matriarch bluntly declares: 'You should turn around, Juliana. Gerald is marrying Clarissa.'",
                cliffhanger_description="Gerald looks down callously and whispers 'I changed my mind' just as Juliana raises her hand in fury.",
                standalone_summary="A bride realizes her fiancé is at the altar with her own sister; the emotional stakes are universally understood."
            ))

            # Candidate 2: Father's Betrayal & Family Ultimatum (45s)
            if len(valid_seconds) >= 8:
                s2 = valid_seconds[min(7, len(valid_seconds)-1)]
                target_e2 = s2 + 45.0
                e2 = min(valid_seconds, key=lambda x: abs(x - target_e2) if x > s2 + 22.0 else 999.0)
                if e2 <= s2 or (e2 - s2) < 20.0 or (e2 - s2) > 60.0:
                    e2 = s2 + 45.0

                candidates.append(CandidateMoment(
                    candidate_id=f"EP{ep_num:02d}_CAND_02",
                    episode_number=ep_num,
                    scene_heading="INT. CATHEDRAL – DAY",
                    start_time_str=format_seconds_to_timestamp(s2),
                    end_time_str=format_seconds_to_timestamp(e2),
                    dramatic_core="Juliana begs her father to speak, but he turns his face away in cold complicity.",
                    opening_hook_description="Juliana falls to her knees before her father crying 'Tell them this is a mistake!'",
                    cliffhanger_description="The Matriarch declares 'You have embarrassed us enough—guards, remove her!' leaving Juliana trapped.",
                    standalone_summary="A woman stripped of her dignity pleads with her parent, who refuses to look her in the eye."
                ))
        else:
            # Fallback realistic candidate
            candidates.append(CandidateMoment(
                candidate_id=f"EP{ep_num:02d}_CAND_01",
                episode_number=ep_num,
                scene_heading="INT. CATHEDRAL – DAY",
                start_time_str="00:11.30",
                end_time_str="00:49.30",
                dramatic_core="Public altar rejection and sisterly betrayal.",
                opening_hook_description="Matriarch coldly steps in: 'You should turn around, Juliana. Gerald is marrying your sister.'",
                cliffhanger_description="Juliana shrieks 'You knew this before I walked through those doors!' as Gerald looks on coldly.",
                standalone_summary="The betrayal is immediate and self-explanatory: the bride's fiancé is marrying her sister."
            ))

        return Stage2CandidateDiscovery(
            episode_number=ep_num,
            candidate_moments=candidates
        )

    def _generate_stage3_evaluation(self, prompt: str) -> Stage3Evaluation:
        cid_match = re.search(r"Candidate ID:\s*(\S+)", prompt)
        cid = cid_match.group(1) if cid_match else "CAND_01"

        # Determine scores based on candidate characteristics in prompt
        is_candidate_01 = "CAND_01" in cid
        hook_score = 9.2 if is_candidate_01 else 8.5
        cliff_score = 9.4 if is_candidate_01 else 8.8
        standalone_score = 9.0 if is_candidate_01 else 8.6
        emo_score = 9.5 if is_candidate_01 else 8.7
        curiosity_score = 9.3 if is_candidate_01 else 8.4
        coherence_score = 9.0 if is_candidate_01 else 8.9

        return Stage3Evaluation(
            candidate_id=cid,
            hook_score=hook_score,
            hook_rationale="The first 3 seconds feature a devastating verbal slap ('You should turn around, Juliana') that creates instant stopping power.",
            cliffhanger_score=cliff_score,
            cliffhanger_rationale="Ends on Gerald's cold refusal with Juliana on the verge of physical retaliation, cutting before the blow lands.",
            standalone_score=standalone_score,
            standalone_rationale="A bride discovering her groom at the altar with her sister requires zero prior lore to grasp immediately.",
            emotional_impact_score=emo_score,
            curiosity_score=curiosity_score,
            coherence_score=coherence_score,
            why_it_works="Combines an instantaneous high-society betrayal hook with an agonizing cliffhanger that forces viewers to seek the next episode.",
            potential_weakness="The cathedral setting is classical drama; rapid pacing must ensure casual mobile viewers catch the sisterly relationship instantly.",
            posting_recommendation="Post as Primary Campaign Opener (#1 Launch Promo) to maximize top-of-funnel scroll-stop rates on TikTok and Instagram Reels.",
            confidence="High"
        )
