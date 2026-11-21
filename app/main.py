"""
PromoFinder AI — Main Python Execution Engine & CLI.
A pure Python application for discovering, scoring, and ranking promotional moments in screenplays.
No web servers, no external frontend dependencies, no deployment required.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import Config
from app.ingestion.file_loader import FileLoader
from app.analysis.pipeline import PromoDiscoveryPipeline
from app.storage.repository import StorageRepository
from app.utils.exports import ExportGenerator
from app.utils.logging import logger


def run_promofinder(
    input_path: Optional[str] = None,
    scan_mode: str = "Standard",
    use_synthetic: bool = False,
    output_dir: Optional[str] = None
):
    print("\n" + "=" * 70)
    print("🎬 PROMOFINDER AI — MICRODRAMA PROMO DISCOVERY ENGINE")
    print("=" * 70)
    print(f"Active Provider: {Config.AI_PROVIDER}")
    print(f"Active Model:    {Config.AI_MODEL}")
    print(f"Scan Mode:       {scan_mode}")
    print("=" * 70)

    # 1. Determine input path
    repository = StorageRepository()
    episodes = []
    screenplay_title = "Screenplay Project"

    if use_synthetic:
        synth_file = BASE_DIR / "data" / "demo" / "synthetic_microdrama_episodes.txt"
        print(f"\n[1/4] Ingesting Synthetic Benchmark Suite: {synth_file.name}...")
        episodes = FileLoader.load_from_file(synth_file)
        screenplay_title = "The Billionaire's Secret Contract (Synthetic Benchmark)"
    elif input_path:
        p = Path(input_path)
        if not p.exists():
            print(f"\n[ERROR] Input path not found: {input_path}")
            sys.exit(1)
        print(f"\n[1/4] Ingesting custom screenplay input: {p}...")
        if p.is_dir():
            episodes = FileLoader.load_from_directory(p)
            screenplay_title = p.name
        else:
            episodes = FileLoader.load_from_file(p)
            screenplay_title = p.stem
    else:
        # Default show dataset
        show_dir = BASE_DIR / "script" / "I Married a Broken Soldier. He was a Duke"
        if show_dir.exists():
            print(f"\n[1/4] Ingesting provided show dataset: {show_dir.name}...")
            episodes = FileLoader.load_from_directory(show_dir)
            screenplay_title = show_dir.name
        else:
            synth_file = BASE_DIR / "data" / "demo" / "synthetic_microdrama_episodes.txt"
            print(f"\n[1/4] Show folder not found. Falling back to synthetic demo: {synth_file.name}...")
            episodes = FileLoader.load_from_file(synth_file)
            screenplay_title = "Synthetic Benchmark Dataset"

    if not episodes:
        print("[ERROR] No valid screenplay episodes found to process.")
        sys.exit(1)

    print(f"-> Successfully parsed {len(episodes)} episode(s) and {sum(len(ep.scenes) for ep in episodes)} scene(s).")

    # 2. Run Promo Discovery Pipeline
    print(f"\n[2/4] Executing 7-Stage Promo Discovery Pipeline ({scan_mode} mode)...")
    pipeline = PromoDiscoveryPipeline(repository=repository)
    result = pipeline.run(
        episodes=episodes,
        screenplay_title=screenplay_title,
        scan_mode=scan_mode
    )

    # 3. Print Results to Terminal
    print("\n" + "=" * 70)
    print("🏆 RANKED PROMOTIONAL OPPORTUNITIES (20s - 60s)")
    print("=" * 70)
    print(f"Analysis ID: {result.analysis_id}")
    print(f"Total Eligible Candidates: {len(result.ranked_promos)}")
    print(f"Review / Flagged:         {len(result.review_promos) + len(result.rejected_promos)}")
    print("-" * 70)

    for p in result.ranked_promos:
        badge = "👑 HERO PROMO" if p.rank == 1 else f"RANK #{p.rank}"
        print(f"\n{badge}: {p.title} ({p.promo_id})")
        print(f"  • Final Score:     {p.scores.final_score}/100 [Hook: {p.scores.hook_score} | Cliffhanger: {p.scores.cliffhanger_score} | Standalone: {p.scores.standalone_score}]")
        print(f"  • Total Duration:  {p.total_duration_seconds:.1f} seconds ({p.promo_type.value})")
        print(f"  • Episodes:        Episode {', '.join(map(str, p.episodes_involved))}")
        print("  • Segment Timestamps:")
        for s in p.segments:
            print(f"      - Ep {s.episode_number}: {s.start_time_str} -> {s.end_time_str} ({s.duration_seconds:.1f}s)")
        print(f"  • Opening Hook:    {p.hook_explanation[:100]}...")
        print(f"  • Cliffhanger:     {p.cliffhanger_explanation[:100]}...")
        print(f"  • Why It Works:    {p.why_it_works}")
        print(f"  • Posting Strategy:{p.posting_recommendation}")

    # 4. Generate All Export Deliverables
    print("\n" + "=" * 70)
    print("[4/4] Generating Export Production Files & Reports...")
    print("=" * 70)

    target_dir = Path(output_dir) if output_dir else (BASE_DIR / "data" / "outputs" / result.analysis_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    # CSV Production Sheet
    csv_path = target_dir / f"kuku_promos_{result.analysis_id}.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(ExportGenerator.generate_csv(result))

    # JSON Data
    json_path = target_dir / f"kuku_analysis_{result.analysis_id}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(ExportGenerator.generate_json(result))

    # Markdown Report
    md_path = target_dir / f"kuku_report_{result.analysis_id}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(ExportGenerator.generate_markdown(result))

    # Executive PDF Report
    pdf_path = target_dir / f"kuku_executive_report_{result.analysis_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(ExportGenerator.generate_pdf(result))

    print(f"✓ Video Editor CSV Sheet:  {csv_path}")
    print(f"✓ Structured JSON Output:   {json_path}")
    print(f"✓ Detailed Markdown Report: {md_path}")
    print(f"✓ Executive PDF Report:     {pdf_path}")
    print("\nPromoFinder AI run complete! Ready for editorial video assembly.\n")


def main():
    parser = argparse.ArgumentParser(
        description="PromoFinder AI — Autonomous Microdrama Promo Discovery Engine"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Path to screenplay file (.txt, .pdf, .docx, .json, .zip) or folder of episodes"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["Quick", "Standard", "Deep"],
        default="Standard",
        help="Discovery scan mode: Quick (fast preview), Standard (balanced), Deep (thorough)"
    )
    parser.add_argument(
        "--synthetic", "-s",
        action="store_true",
        help="Run discovery on the 3-episode synthetic benchmark dataset with edge cases"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Custom directory to save exported CSV, JSON, Markdown, and PDF deliverables"
    )

    args = parser.parse_args()
    run_promofinder(
        input_path=args.input,
        scan_mode=args.mode,
        use_synthetic=args.synthetic,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
