"""
Unit tests for screenplay ingestion, episode detection, and multi-format parsing.
"""
import pytest
from pathlib import Path
from app.ingestion.episode_detector import split_multi_episode_text, extract_episode_number_from_text_or_name
from app.ingestion.screenplay_parser import ScreenplayParser
from app.ingestion.file_loader import FileLoader


def test_episode_detection_from_single_document():
    multi_ep_doc = """
EPISODE 1: The Altar
Some intro lines...

EPISODE 2: The Aftermath
Some second episode lines...

EPISODE 3: The Return
Some third episode lines...
"""
    ep_blocks = split_multi_episode_text(multi_ep_doc)
    assert len(ep_blocks) == 3
    assert ep_blocks[0]["episode_number"] == 1
    assert ep_blocks[1]["episode_number"] == 2
    assert ep_blocks[2]["episode_number"] == 3


def test_synthetic_screenplay_parsing():
    demo_file = Path("data/demo/synthetic_microdrama_episodes.txt")
    assert demo_file.exists(), "Synthetic demo dataset must exist"
    
    episodes = FileLoader.load_from_file(demo_file)
    assert len(episodes) == 3
    
    ep1 = episodes[0]
    assert ep1.episode_number == 1
    assert len(ep1.scenes) >= 1
    assert "MAYA" in ep1.characters
    assert "DAMON" in ep1.characters


def test_real_dataset_ingestion():
    real_dir = Path("script/I Married a Broken Soldier. He was a Duke")
    if real_dir.exists():
        episodes = FileLoader.load_from_directory(real_dir)
        assert len(episodes) == 50
        ep1 = episodes[0]
        assert ep1.episode_number == 1
        assert len(ep1.scenes[0].dialogue_lines) > 20
