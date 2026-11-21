"""
Screenplay parser for microdrama and standard screenplay formats.
Extracts scenes, dialogue lines, camera/action blocks, timestamps, and characters.
"""
import re
from typing import List, Optional, Tuple, Set
from app.storage.models import Episode, Scene, DialogueLine, ActionBlock
from app.utils.timestamps import parse_timestamp_to_seconds, calculate_duration
from app.utils.logging import logger
from app.ingestion.episode_detector import extract_episode_number_from_text_or_name


# Timestamp extraction patterns
TS_PATTERN = re.compile(
    r"(?:Start|Scene start|Time|Timestamp):\s*\(?\[?([0-9:.]+)\)?\]?\s*(?:\||-|to)\s*(?:End|Scene end)?:\s*\(?\[?([0-9:.]+)\)?\]?",
    re.IGNORECASE
)
SINGLE_TS_PATTERN = re.compile(r"\(?\[?(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\)?\]?")

# Microdrama block header: e.g. **LADY JULIANA (Confused):** or **CAMERA:** or **ACTION:**
BLOCK_HEADER_PATTERN = re.compile(r"^\*\*([^*]+?):?\*\*:?\s*$", re.MULTILINE)

# Scene heading: e.g. SCENE 01 or INT. CATHEDRAL – DAY
SCENE_SPLIT_PATTERN = re.compile(r"^(?:SCENE\s+\d+|INT\.|EXT\.|I/E\.)", re.IGNORECASE | re.MULTILINE)


class ScreenplayParser:
    """Parses raw screenplay text into structured Episode domain models."""

    @classmethod
    def parse_episode_text(cls, raw_text: str, filename: str = "") -> Episode:
        ep_num, detected_title = extract_episode_number_from_text_or_name(raw_text, filename)
        
        # Extract logline & continuity notes if present
        logline = ""
        continuity = ""
        logline_match = re.search(r"EPISODE LOGLINE:\s*(.*?)(?=\n[A-Z\s]+:|\n---|\nSCENE|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
        if logline_match:
            logline = logline_match.group(1).strip()
            
        continuity_match = re.search(r"CONTINUITY NOTES:\s*(.*?)(?=\n[A-Z\s]+:|\n---|\nSCENE|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
        if continuity_match:
            continuity = continuity_match.group(1).strip()

        # Parse scenes
        scenes = cls._parse_scenes(raw_text, ep_num)
        
        # Collect distinct characters
        characters: Set[str] = set()
        for sc in scenes:
            for dl in sc.dialogue_lines:
                if dl.character and dl.character.upper() not in ("CAMERA", "ACTION", "UNKNOWN"):
                    characters.add(dl.character.strip())

        return Episode(
            episode_id=f"EP_{ep_num:03d}",
            episode_number=ep_num,
            title=detected_title or f"Episode {ep_num}",
            logline=logline,
            continuity_notes=continuity,
            scenes=scenes,
            characters=sorted(list(characters)),
            source_filename=filename,
            raw_text=raw_text
        )

    @classmethod
    def _parse_scenes(cls, raw_text: str, ep_num: int) -> List[Scene]:
        """Splits screenplay text into structured scenes."""
        scenes: List[Scene] = []
        
        # Find scene blocks
        scene_blocks = re.split(r"\n(?=SCENE\s+\d+|INT\.|EXT\.)", raw_text, flags=re.IGNORECASE)
        
        scene_counter = 1
        for block in scene_blocks:
            clean_block = block.strip()
            if not clean_block or clean_block.startswith("EPISODE NUMBER"):
                continue

            # Heading line
            lines = clean_block.splitlines()
            first_line = lines[0].strip()
            
            heading = first_line
            scene_start_str = None
            scene_end_str = None
            
            # Check for explicit Scene start / Scene end lines
            for l in lines[1:6]:
                l_strip = l.strip()
                s_match = re.search(r"Scene start:\s*([0-9:.]+)", l_strip, re.IGNORECASE)
                if s_match:
                    scene_start_str = s_match.group(1).strip()
                e_match = re.search(r"Scene end:\s*([0-9:.]+)", l_strip, re.IGNORECASE)
                if e_match:
                    scene_end_str = e_match.group(1).strip()
                h_match = re.search(r"Scene heading:\s*(.*)", l_strip, re.IGNORECASE)
                if h_match:
                    heading = h_match.group(1).strip()

            # Parse dialogue and actions in this scene block
            dialogue_lines, action_blocks = cls._parse_dialogue_and_actions(clean_block)
            
            # If scene start/end not explicitly found, infer from first/last element
            start_sec = parse_timestamp_to_seconds(scene_start_str)
            end_sec = parse_timestamp_to_seconds(scene_end_str)

            if start_sec is None and dialogue_lines:
                for dl in dialogue_lines:
                    if dl.start_seconds is not None:
                        start_sec = dl.start_seconds
                        scene_start_str = dl.start_time_str
                        break

            if end_sec is None and dialogue_lines:
                for dl in reversed(dialogue_lines):
                    if dl.end_seconds is not None:
                        end_sec = dl.end_seconds
                        scene_end_str = dl.end_time_str
                        break

            scene_obj = Scene(
                scene_id=f"EP_{ep_num:03d}_SC_{scene_counter:02d}",
                scene_number=scene_counter,
                heading=heading,
                start_time_str=scene_start_str,
                end_time_str=scene_end_str,
                start_seconds=start_sec,
                end_seconds=end_sec,
                dialogue_lines=dialogue_lines,
                action_blocks=action_blocks,
                raw_text=clean_block
            )
            scenes.append(scene_obj)
            scene_counter += 1

        # Fallback if no scenes were parsed: create single full scene
        if not scenes:
            dialogue_lines, action_blocks = cls._parse_dialogue_and_actions(raw_text)
            scenes.append(Scene(
                scene_id=f"EP_{ep_num:03d}_SC_01",
                scene_number=1,
                heading=f"Episode {ep_num} Full Scene",
                start_time_str="00:00.00",
                end_time_str=None,
                start_seconds=0.0,
                end_seconds=None,
                dialogue_lines=dialogue_lines,
                action_blocks=action_blocks,
                raw_text=raw_text
            ))

        return scenes

    @classmethod
    def _parse_dialogue_and_actions(cls, text: str) -> Tuple[List[DialogueLine], List[ActionBlock]]:
        """
        Parses structured blocks like:
        **CAMERA:**
        Start: (00:00.00) | End: (00:04.80)
        Description...

        **LADY JULIANA (Confused, Breathless):**
        Start: (00:13.50) | End: (00:14.30)
        "Why?"
        """
        dialogue_lines: List[DialogueLine] = []
        action_blocks: List[ActionBlock] = []

        matches = list(BLOCK_HEADER_PATTERN.finditer(text))
        if matches:
            for idx, match in enumerate(matches):
                raw_header = match.group(1).rstrip(':').strip()
                body_start = match.end()
                body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
                body = text[body_start:body_end].strip()

                # Extract timestamps
                start_str = None
                end_str = None
                content_lines = []

                for line in body.splitlines():
                    ts_match = TS_PATTERN.search(line)
                    if ts_match:
                        start_str = ts_match.group(1).strip()
                        end_str = ts_match.group(2).strip()
                    else:
                        content_lines.append(line.strip())

                content = " ".join(l for l in content_lines if l).strip()
                clean_content = content.strip('"\'')

                start_sec = parse_timestamp_to_seconds(start_str)
                end_sec = parse_timestamp_to_seconds(end_str)

                header_upper = raw_header.upper()
                if "CAMERA" in header_upper:
                    action_blocks.append(ActionBlock(
                        block_type="CAMERA",
                        description=content,
                        start_time_str=start_str,
                        end_time_str=end_str,
                        start_seconds=start_sec,
                        end_seconds=end_sec
                    ))
                elif "ACTION" in header_upper:
                    action_blocks.append(ActionBlock(
                        block_type="ACTION",
                        description=content,
                        start_time_str=start_str,
                        end_time_str=end_str,
                        start_seconds=start_sec,
                        end_seconds=end_sec
                    ))
                else:
                    char_name = raw_header
                    tone = None
                    tone_match = re.search(r"^(.*?)\s*\((.*?)\)$", raw_header)
                    if tone_match:
                        char_name = tone_match.group(1).strip()
                        tone = tone_match.group(2).strip()

                    dialogue_lines.append(DialogueLine(
                        character=char_name,
                        tone=tone,
                        dialogue=clean_content or content,
                        start_time_str=start_str,
                        end_time_str=end_str,
                        start_seconds=start_sec,
                        end_seconds=end_sec
                    ))

        # Also support standard fountain / standard dialogue if no **HEADER:** blocks found
        if not dialogue_lines and not action_blocks:
            lines = text.splitlines()
            for line in lines:
                single_ts = SINGLE_TS_PATTERN.search(line)
                ts_val = single_ts.group(1) if single_ts else None
                ts_sec = parse_timestamp_to_seconds(ts_val)
                line_clean = line.strip()
                
                # Check for standard CHARACTER: Dialogue
                std_match = re.match(r"^([A-Z\s]{2,25}):\s*(.*)$", line_clean)
                if std_match:
                    cname = std_match.group(1).strip()
                    dial = std_match.group(2).strip()
                    dialogue_lines.append(DialogueLine(
                        character=cname,
                        dialogue=dial,
                        start_time_str=ts_val,
                        end_time_str=None,
                        start_seconds=ts_sec,
                        end_seconds=None
                    ))
                elif line_clean:
                    action_blocks.append(ActionBlock(
                        block_type="ACTION",
                        description=line_clean,
                        start_time_str=ts_val,
                        end_time_str=None,
                        start_seconds=ts_sec,
                        end_seconds=None
                    ))

        return dialogue_lines, action_blocks
