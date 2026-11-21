"""
Export generators for PromoFinder AI: JSON, CSV, Markdown, and PDF.
"""
import csv
import io
import json
from typing import List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from app.storage.models import AnalysisResult, PromoCandidate


class ExportGenerator:
    """Generates JSON, CSV, Markdown, and PDF reports for an analysis result."""

    @classmethod
    def generate_json(cls, result: AnalysisResult) -> str:
        """Exports complete analysis result to formatted JSON string."""
        return result.model_dump_json(indent=2)

    @classmethod
    def generate_csv(cls, result: AnalysisResult) -> str:
        """Exports ranked promos into a structured CSV format for video editors."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([
            "Rank",
            "Promo ID",
            "Title",
            "Episodes",
            "Type",
            "Total Duration (s)",
            "Final Score (/100)",
            "Hook Score (/10)",
            "Cliffhanger Score (/10)",
            "Standalone Score (/10)",
            "Confidence",
            "Segment Count",
            "Segment Breakdown (Ep:Start-End)",
            "Opening Hook (First 3s)",
            "Cliffhanger Moment",
            "Why It Works",
            "Posting Recommendation",
            "Review Status",
            "Editor Notes"
        ])

        for p in result.ranked_promos:
            seg_str = "; ".join(f"Ep{s.episode_number}:{s.start_time_str}->{s.end_time_str}({s.duration_seconds}s)" for s in p.segments)
            writer.writerow([
                p.rank,
                p.promo_id,
                p.title,
                ", ".join(map(str, p.episodes_involved)),
                p.promo_type.value,
                p.total_duration_seconds,
                p.scores.final_score,
                p.scores.hook_score,
                p.scores.cliffhanger_score,
                p.scores.standalone_score,
                p.confidence.value,
                len(p.segments),
                seg_str,
                p.hook_explanation,
                p.cliffhanger_explanation,
                p.why_it_works,
                p.posting_recommendation,
                p.review_status.value,
                p.human_notes
            ])

        return output.getvalue()

    @classmethod
    def generate_markdown(cls, result: AnalysisResult) -> str:
        """Generates comprehensive Markdown report."""
        md = []
        md.append(f"# PromoFinder AI — Analysis Report: {result.screenplay_title}")
        md.append(f"**Analysis ID:** `{result.analysis_id}`  ")
        md.append(f"**Generated:** {result.created_at}  ")
        md.append(f"**Model:** {result.ai_provider} ({result.ai_model})  ")
        md.append(f"**Episodes Processed:** {result.total_episodes} | **Scenes:** {result.total_scenes}  \n")

        md.append("## Executive Highlights")
        md.append(f"- **Top Hero Promo:** `{result.best_overall_id}`")
        md.append(f"- **Strongest Opening Hook:** `{result.strongest_hook_id}`")
        md.append(f"- **Most Compelling Cliffhanger:** `{result.strongest_cliffhanger_id}`")
        md.append(f"- **Best Standalone Intro:** `{result.best_standalone_id}`")
        md.append(f"- **Best Multi-Segment Cut:** `{result.best_multisegment_id}`\n")

        md.append("## Ranked Promotional Candidates")
        for p in result.ranked_promos:
            md.append(f"### Rank {p.rank}: {p.title} (`{p.promo_id}`)")
            md.append(f"- **Final Score:** **{p.scores.final_score}/100** | **Duration:** {p.total_duration_seconds:.1f}s | **Type:** {p.promo_type.value}")
            md.append(f"- **Episodes Involved:** Episode {', '.join(map(str, p.episodes_involved))}")
            md.append(f"- **Scores:** Hook: {p.scores.hook_score}/10 | Cliffhanger: {p.scores.cliffhanger_score}/10 | Standalone: {p.scores.standalone_score}/10 | Emotional: {p.scores.emotional_score}/10")
            md.append(f"- **Opening Hook (First 3s):** {p.hook_explanation}")
            md.append(f"- **Cliffhanger Ending:** {p.cliffhanger_explanation}")
            md.append(f"- **Standalone Context:** {p.standalone_explanation}")
            md.append(f"- **Why It Works:** *{p.why_it_works}*")
            md.append(f"- **Posting Recommendation:** {p.posting_recommendation}")
            md.append("\n**Segments:**")
            for seg in p.segments:
                md.append(f"  - Ep {seg.episode_number}: `{seg.start_time_str}` to `{seg.end_time_str}` ({seg.duration_seconds:.1f}s)")
            if p.source_references:
                md.append("\n**Screenplay Excerpts:**")
                for s in p.source_references[:3]:
                    md.append(f"  > {s}")
            md.append("\n---\n")

        md.append("## Quality Assurance & Failure Analysis")
        md.append(f"- **Total Quality Issues Flagged:** {len(result.quality_issues)}")
        for issue in result.quality_issues[:5]:
            md.append(f"- **[{issue.severity.value}] {issue.issue_type}:** {issue.description}")

        return "\n".join(md)

    @classmethod
    def generate_pdf(cls, result: AnalysisResult) -> bytes:
        """Generates a clean, professional PDF report using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=20, leading=24, textColor=colors.HexColor('#1E293B'))
        h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=13, leading=17, textColor=colors.HexColor('#0F172A'), spaceAfter=8)
        body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#334155'))
        card_title = ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Bold', textColor=colors.HexColor('#0284C7'))

        story = []
        story.append(Paragraph(f"PromoFinder AI — Analysis Report", title_style))
        story.append(Paragraph(f"Screenplay: <b>{result.screenplay_title}</b> | Run: <code>{result.analysis_id}</code> | Date: {result.created_at}", body_style))
        story.append(Spacer(1, 14))

        # Highlights Table
        summary_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Episodes", str(result.total_episodes), "Total Scenes", str(result.total_scenes)],
            ["Eligible Promos", str(len(result.ranked_promos)), "Rejected / Review", str(len(result.rejected_promos) + len(result.review_promos))],
            ["Top Hero Promo", str(result.best_overall_id), "Strongest Hook", str(result.strongest_hook_id)]
        ]
        t = Table(summary_data, colWidths=[110, 150, 110, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

        # Ranked Promos section
        story.append(Paragraph("Ranked Promotional Opportunities", h2_style))
        for p in result.ranked_promos[:6]:
            promo_header = f"<b>Rank {p.rank}: {p.title} ({p.promo_id})</b> — Score: <b>{p.scores.final_score}/100</b> | Duration: {p.total_duration_seconds}s | {p.promo_type.value}"
            story.append(Paragraph(promo_header, card_title))
            
            seg_info = ", ".join(f"Ep {s.episode_number} [{s.start_time_str}->{s.end_time_str}]" for s in p.segments)
            details = (
                f"<b>Timestamps:</b> {seg_info}<br/>"
                f"<b>Hook (First 3s):</b> {p.hook_explanation}<br/>"
                f"<b>Cliffhanger:</b> {p.cliffhanger_explanation}<br/>"
                f"<b>Why It Works:</b> <i>{p.why_it_works}</i><br/>"
                f"<b>Posting Strategy:</b> {p.posting_recommendation}"
            )
            story.append(Paragraph(details, body_style))
            story.append(Spacer(1, 10))

        doc.build(story)
        return buffer.getvalue()
