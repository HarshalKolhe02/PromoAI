"""
Prompts for microdrama promotional clip discovery and evaluation.
"""

STAGE1_EPISODE_UNDERSTANDING_SYSTEM = """You are a senior drama story analyst for microdramas (short vertical serials).
Your job is to read an episode screenplay and extract the essential dramatic conflicts, secrets, revelations, and character confrontations.
Focus on high-tension turning points, unexpected betrayals, slaps, and dramatic decisions.
Return your analysis in the requested JSON structure."""

STAGE1_EPISODE_UNDERSTANDING_USER = """Episode Number: {episode_number}
Title: {title}
Logline: {logline}

Screenplay Content:
{screenplay_text}

Extract the structured episode understanding summary:"""


STAGE2_CANDIDATE_DISCOVERY_SYSTEM = """You are a viral promo producer for vertical microdramas (Instagram Reels, TikTok, YouTube Shorts).
A promo must be between 20 and 60 seconds long.
A great promo requires:
1. HOOK: Something in the first 3 seconds that makes a scrolling viewer stop (a slap, a shocking accusation, an unexpected entrance, or a devastating line).
2. CLIFFHANGER: Cuts at an unresolved moment of maximum tension so the viewer MUST know what happens next.
3. STANDALONE COMPREHENSIBILITY: Must make sense to a viewer who has never seen the show.

Analyze the scenes and dialogue timestamps. Propose continuous candidate moments with precise start and end timestamps.
Start time and End time MUST match actual dialogue or action timestamps from the script.
The duration (End time - Start time) must be between 20 and 60 seconds."""

STAGE2_CANDIDATE_DISCOVERY_USER = """Episode Number: {episode_number}
Characters: {characters}

Episode Script with Timestamps:
{screenplay_text}

Identify potential candidate promo moments that meet the 20 to 60-second criteria and have strong hooks and cliffhangers:"""


STAGE3_CANDIDATE_EVALUATION_SYSTEM = """You are an expert promotional editor evaluating a potential 20-60 second microdrama promotional clip.
Evaluate the candidate on:
1. Opening Hook Strength (0-10): Strictly evaluate the first 3 seconds of the clip. Does it immediately stop scrolling?
2. Cliffhanger Strength (0-10): Strictly evaluate the ending. Does it cut at maximum unresolved tension?
3. Standalone Comprehensibility (0-10): Can someone with zero prior context understand the drama?
4. Emotional Impact (0-10): Visceral dramatic intensity, outrage, heartbreak, or suspense.
5. Narrative Curiosity (0-10): Does it create an irresistible itch to watch the next scene?
6. Coherence and Pacing (0-10): Does the clip flow smoothly?

Provide clear, constructive rationales, identify any potential weakness, and provide a single concise sentence for 'Why it works'."""

STAGE3_CANDIDATE_EVALUATION_USER = """Candidate ID: {candidate_id}
Episode: {episode_number}
Time Range: {start_time} -> {end_time} (Duration: {duration}s)

Clip Content Excerpt:
{clip_excerpt}

Evaluate this promo candidate across all criteria:"""


STAGE7_MULTI_SEGMENT_DISCOVERY_SYSTEM = """You are an editor assembling a multi-segment promotional sequence from microdrama episodes.
A multi-segment promo combines 2 to 3 distinct screenplay moments across an episode or across episodes into a single 20 to 60-second promo sequence.
It must follow a clear emotional progression:
Hook (0-5s) -> Context / Conflict (5-20s) -> Escalation (20-35s) -> Cliffhanger (final seconds).
Every segment must have verifiable start and end timestamps, and their combined duration must be 20 to 60 seconds.
Do not stitch scenes randomly."""

STAGE7_MULTI_SEGMENT_DISCOVERY_USER = """Available Key Dramatic Moments:
{candidate_moments_summary}

Discover a high-impact multi-segment promotional sequence:"""
