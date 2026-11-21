"""
Multi-format file ingestion loader.
Loads TXT, MD, PDF, DOCX, JSON, ZIP files and directories into structured Episode objects.
"""
import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Union, Dict
from app.ingestion.docx_parser import extract_text_from_docx
from app.ingestion.episode_detector import split_multi_episode_text
from app.ingestion.pdf_parser import extract_text_from_pdf
from app.ingestion.screenplay_parser import ScreenplayParser
from app.storage.models import Episode
from app.utils.logging import logger


class FileLoader:
    """Loads and normalizes screenplays from various formats into Episode models."""

    @classmethod
    def load_from_directory(cls, dir_path: Union[str, Path]) -> List[Episode]:
        """Loads all supported screenplay files from a directory."""
        dir_path = Path(dir_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        episodes: List[Episode] = []
        files = sorted(
            [f for f in dir_path.iterdir() if f.is_file() and not f.name.startswith(".")],
            key=lambda x: x.name
        )
        
        for file in files:
            try:
                eps = cls.load_from_file(file)
                episodes.extend(eps)
            except Exception as e:
                logger.warning(f"Skipping file {file.name} due to error: {e}")

        # Sort episodes by episode number
        episodes.sort(key=lambda ep: ep.episode_number)
        return episodes

    @classmethod
    def load_from_file(cls, file_path: Path) -> List[Episode]:
        """Loads an individual file (TXT, MD, PDF, DOCX, JSON, ZIP)."""
        suffix = file_path.suffix.lower()

        if suffix in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return cls._process_raw_text(content, filename=file_path.name)

        elif suffix == ".pdf":
            content = extract_text_from_pdf(file_path)
            return cls._process_raw_text(content, filename=file_path.name)

        elif suffix == ".docx":
            content = extract_text_from_docx(file_path)
            return cls._process_raw_text(content, filename=file_path.name)

        elif suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls._process_json_content(data, filename=file_path.name)

        elif suffix == ".zip":
            return cls.load_from_zip(file_path)

        else:
            logger.warning(f"Unsupported file format: {suffix} for {file_path.name}")
            return []

    @classmethod
    def load_from_zip(cls, zip_path: Path) -> List[Episode]:
        """Extracts and parses all screenplay files inside a ZIP archive."""
        episodes: List[Episode] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(temp_path)

            # Recursively walk extracted files
            for root, _, files in os.walk(temp_path):
                for f in sorted(files):
                    fp = Path(root) / f
                    if not f.startswith(".") and fp.suffix.lower() in (".txt", ".md", ".pdf", ".docx", ".json"):
                        try:
                            eps = cls.load_from_file(fp)
                            episodes.extend(eps)
                        except Exception as e:
                            logger.warning(f"Error parsing zip entry {f}: {e}")

        episodes.sort(key=lambda ep: ep.episode_number)
        return episodes

    @classmethod
    def load_from_uploaded_bytes(cls, filename: str, content_bytes: bytes) -> List[Episode]:
        """Loads from an in-memory uploaded file."""
        suffix = Path(filename).suffix.lower()

        if suffix in (".txt", ".md"):
            text = content_bytes.decode("utf-8", errors="replace")
            return cls._process_raw_text(text, filename=filename)

        elif suffix == ".pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                tf.write(content_bytes)
                tf_path = Path(tf.name)
            try:
                text = extract_text_from_pdf(tf_path)
                return cls._process_raw_text(text, filename=filename)
            finally:
                if tf_path.exists():
                    tf_path.unlink()

        elif suffix == ".docx":
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
                tf.write(content_bytes)
                tf_path = Path(tf.name)
            try:
                text = extract_text_from_docx(tf_path)
                return cls._process_raw_text(text, filename=filename)
            finally:
                if tf_path.exists():
                    tf_path.unlink()

        elif suffix == ".json":
            data = json.loads(content_bytes.decode("utf-8", errors="replace"))
            return cls._process_json_content(data, filename=filename)

        elif suffix == ".zip":
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
                tf.write(content_bytes)
                tf_path = Path(tf.name)
            try:
                return cls.load_from_zip(tf_path)
            finally:
                if tf_path.exists():
                    tf_path.unlink()

        return []

    @classmethod
    def _process_raw_text(cls, text: str, filename: str) -> List[Episode]:
        """Splits multi-episode text if needed and parses each into Episode objects."""
        ep_blocks = split_multi_episode_text(text)
        episodes = []
        for blk in ep_blocks:
            ep = ScreenplayParser.parse_episode_text(blk["text"], filename=filename)
            # If multiple episodes found in single file, update number if detected
            if blk["episode_number"] != 1 or len(ep_blocks) > 1:
                ep.episode_number = blk["episode_number"]
                ep.episode_id = f"EP_{blk['episode_number']:03d}"
            episodes.append(ep)
        return episodes

    @classmethod
    def _process_json_content(cls, data: Union[Dict, List], filename: str) -> List[Episode]:
        """Parses structured JSON containing episode scripts."""
        episodes = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "text" in item:
                    ep = ScreenplayParser.parse_episode_text(item["text"], filename=filename)
                    if "episode_number" in item:
                        ep.episode_number = int(item["episode_number"])
                        ep.episode_id = f"EP_{ep.episode_number:03d}"
                    episodes.append(ep)
        elif isinstance(data, dict):
            if "episodes" in data and isinstance(data["episodes"], list):
                for item in data["episodes"]:
                    text = item.get("text") or item.get("content") or ""
                    ep = ScreenplayParser.parse_episode_text(text, filename=filename)
                    if "episode_number" in item:
                        ep.episode_number = int(item["episode_number"])
                        ep.episode_id = f"EP_{ep.episode_number:03d}"
                    episodes.append(ep)
            elif "text" in data:
                ep = ScreenplayParser.parse_episode_text(data["text"], filename=filename)
                episodes.append(ep)
        return episodes
