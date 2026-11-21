"""
Detects episode boundaries from single multi-episode texts or extracts episode metadata from files.
"""
import re
from typing import List, Tuple, Dict


EPISODE_PATTERNS = [
    re.compile(r"^EPISODE\s+(?:NUMBER:\s*)?(?:Episode\s+)?(\d+)(?:\s*[-:–]\s*(.*))?$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^#+\s*EPISODE\s+(\d+)(?:\s*[-:–]\s*(.*))?$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^EPISODE\s+(\d+)\b(.*)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^EP\s*(\d+)\b(.*)$", re.IGNORECASE | re.MULTILINE),
]


def extract_episode_number_from_text_or_name(text: str, filename: str = "") -> Tuple[int, str]:
    """
    Extracts episode number and optional title from filename or text header.
    Defaults to 1 if undetected.
    """
    # 1. Try file name first (e.g. episode-001-Episode 1671703.txt, Ep_02.txt)
    fn_match = re.search(r"ep(?:isode)?[-_ ]*0*(\d+)", filename, re.IGNORECASE)
    if fn_match:
        ep_num = int(fn_match.group(1))
        # Check if title in filename
        return ep_num, filename

    # 2. Try text header
    for line in text.splitlines()[:20]:
        line_clean = line.strip()
        header_match = re.search(r"EPISODE\s+(?:NUMBER:\s*)?(?:Episode\s+)?0*(\d+)(?:\s*[-:–]\s*(.*))?", line_clean, re.IGNORECASE)
        if header_match:
            ep_num = int(header_match.group(1))
            title = (header_match.group(2) or "").strip()
            return ep_num, title

    return 1, "Episode 1"


def split_multi_episode_text(raw_text: str) -> List[Dict]:
    """
    Splits a single document containing multiple episodes into individual episode text blocks.
    If only one episode is detected, returns the full text as a single episode block.
    """
    # Find all episode markers and their positions
    markers = []
    lines = raw_text.splitlines()
    
    current_char_offset = 0
    for line in lines:
        for pat in EPISODE_PATTERNS:
            match = pat.match(line.strip())
            if match:
                ep_num = int(match.group(1))
                title = (match.group(2) or "").strip()
                markers.append((current_char_offset, ep_num, title, line))
                break
        current_char_offset += len(line) + 1  # newline

    if len(markers) <= 1:
        # Single episode or unmarked
        ep_num, title = extract_episode_number_from_text_or_name(raw_text)
        return [{
            "episode_number": ep_num,
            "title": title,
            "text": raw_text
        }]

    episodes = []
    for i, (offset, ep_num, title, line) in enumerate(markers):
        start_idx = offset
        end_idx = markers[i + 1][0] if (i + 1 < len(markers)) else len(raw_text)
        ep_text = raw_text[start_idx:end_idx].strip()
        episodes.append({
            "episode_number": ep_num,
            "title": title or f"Episode {ep_num}",
            "text": ep_text
        })

    return episodes
