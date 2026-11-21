"""
Timestamp parsing, normalization, duration calculation and interval utilities.
Handles HH:MM:SS, MM:SS, MM:SS.mmm, (MM:SS.ss), ranges, and seconds conversion.
"""
import re
from typing import Optional, Tuple


def parse_timestamp_to_seconds(ts_str: Optional[str]) -> Optional[float]:
    """
    Parses a timestamp string into total seconds (float).
    Supports:
      - '01:23' -> 83.0
      - '01:23.45' -> 83.45
      - '00:01:23' -> 83.0
      - '00:01:23.450' -> 83.45
      - '(00:04.80)' -> 4.80
      - '123' -> 123.0
    Returns None if the timestamp is missing, empty, or unparseable.
    """
    if not ts_str:
        return None
    
    clean_ts = str(ts_str).strip()
    clean_ts = clean_ts.lstrip("(").rstrip(")")
    clean_ts = clean_ts.lstrip("[").rstrip("]")
    clean_ts = clean_ts.strip()

    if not clean_ts or clean_ts.lower() in ("none", "n/a", "null", "missing"):
        return None

    # Match HH:MM:SS or HH:MM:SS.mmm
    hms_match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d+))?$", clean_ts)
    if hms_match:
        hours = int(hms_match.group(1))
        minutes = int(hms_match.group(2))
        seconds = int(hms_match.group(3))
        fraction = float(f"0.{hms_match.group(4)}") if hms_match.group(4) else 0.0
        return (hours * 3600) + (minutes * 60) + seconds + fraction

    # Match MM:SS or MM:SS.mmm
    ms_match = re.match(r"^(\d{1,2}):(\d{2})(?:\.(\d+))?$", clean_ts)
    if ms_match:
        minutes = int(ms_match.group(1))
        seconds = int(ms_match.group(2))
        fraction = float(f"0.{ms_match.group(3)}") if ms_match.group(3) else 0.0
        return (minutes * 60) + seconds + fraction

    # Direct float/int string
    try:
        val = float(clean_ts)
        return val if val >= 0 else None
    except ValueError:
        return None


def format_seconds_to_timestamp(seconds: Optional[float], include_millis: bool = False) -> str:
    """
    Formats seconds (float) to standard timestamp string 'MM:SS' or 'HH:MM:SS'.
    """
    if seconds is None or seconds < 0:
        return "00:00"
    
    total_seconds = int(seconds)
    fraction = seconds - total_seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        base = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        base = f"{minutes:02d}:{secs:02d}"

    if include_millis:
        millis = int(round(fraction * 100))
        return f"{base}.{millis:02d}"
    return base


def calculate_duration(start_seconds: Optional[float], end_seconds: Optional[float]) -> Optional[float]:
    """
    Calculates duration in seconds given start and end seconds.
    Returns None if either timestamp is invalid or if end <= start.
    """
    if start_seconds is None or end_seconds is None:
        return None
    if end_seconds < start_seconds:
        return None
    return round(end_seconds - start_seconds, 2)


def is_duration_within_promo_bounds(duration: Optional[float], min_dur: float = 20.0, max_dur: float = 60.0) -> bool:
    """
    Validates if duration is strictly within [min_dur, max_dur].
    """
    if duration is None:
        return False
    return min_dur <= duration <= max_dur


def compute_interval_overlap(start1: float, end1: float, start2: float, end2: float) -> float:
    """
    Computes overlap duration in seconds between two intervals [start1, end1] and [start2, end2].
    """
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    if overlap_end > overlap_start:
        return overlap_end - overlap_start
    return 0.0


def compute_jaccard_overlap(start1: float, end1: float, start2: float, end2: float) -> float:
    """
    Computes Jaccard similarity (Intersection over Union) of two time ranges.
    """
    overlap = compute_interval_overlap(start1, end1, start2, end2)
    if overlap <= 0:
        return 0.0
    union = (end1 - start1) + (end2 - start2) - overlap
    return overlap / union if union > 0 else 0.0
