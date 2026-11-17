"""PDF generation service for exporting study notes and conversations."""

from __future__ import annotations

import io
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def _format_markdown_for_reportlab(text: str) -> str:
    """Sanitize and convert markdown formatting to ReportLab XML tags."""
    if not text:
        return ""
    # XML entity escapes
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic *text*
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Inline code `text`
    text = re.sub(r"`(.+?)`", r"<b>\1</b>", text)
    # Line breaks
    text = text.replace("\r\n", "<br/>").replace("\n", "<br/>")
    return text


def build_conversation_pdf(
    title: str,
    subject_name: str | None,
    messages: list[Any],
) -> bytes:
    """Generate a clean, printable PDF document of an AI study session."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#043634")
    accent_color = colors.HexColor("#0d9488")
    text_dark = colors.HexColor("#1e293b")
    border_color = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        "ChatTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    meta_style = ParagraphStyle(
        "ChatMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    role_user_style = ParagraphStyle(
        "RoleUser",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=3,
    )

    role_ai_style = ParagraphStyle(
        "RoleAI",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=3,
    )

    msg_body_style = ParagraphStyle(
        "MsgBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=text_dark,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    user_text_style = ParagraphStyle(
        "UserMsgBody",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=primary_color,
        alignment=TA_LEFT,
        leftIndent=8,
        spaceAfter=6,
    )

    story = []

    # Document Header
    story.append(Paragraph(title or "AI Study Session", title_style))
    sub_text = f"Subject: {subject_name} &bull; " if subject_name else ""
    story.append(Paragraph(f"{sub_text}Smart AI Academic Assistant Study Notes", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=12))

    for msg in messages:
        role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "assistant")
        content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
        if not content:
            continue

        is_user = role == "user"
        sender_label = "Student Question" if is_user else "AI Tutor Explanation"
        sender_style = role_user_style if is_user else role_ai_style
        line_color = primary_color if is_user else accent_color

        story.append(Paragraph(f"<b>{sender_label}</b>", sender_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=line_color, spaceAfter=5))

        # Split content into smaller paragraph chunks so ReportLab can paginate freely
        raw_paras = content.split("\n\n")
        for raw_p in raw_paras:
            raw_p = raw_p.strip()
            if not raw_p:
                continue
            formatted_p = _format_markdown_for_reportlab(raw_p)
            style_to_use = user_text_style if is_user else msg_body_style
            story.append(Paragraph(formatted_p, style_to_use))
            story.append(Spacer(1, 3))

        story.append(Spacer(1, 8))

    if not messages:
        story.append(Paragraph("<i>No messages in this session.</i>", meta_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))
    story.append(Paragraph("<i>Generated by Smart AI Academic Assistant</i>", meta_style))

    doc.build(story)
    return buffer.getvalue()
