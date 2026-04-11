"""pdf_generator.py - ReportLab PDF generation with custom styling."""
import io
import logging
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from fastapi import HTTPException

logger = logging.getLogger(__name__)

FONT_MAP = {
    "Helvetica": "Helvetica",
    "Times-Roman": "Times-Roman",
    "Courier": "Courier",
}

def generate_pdf(
    content: str,
    font_size: int = 12,
    font_style: str = "Helvetica",
    header: Optional[str] = None,
    footer: Optional[str] = None,
    watermark_text: Optional[str] = None,
) -> bytes:
    """
    Generate a styled PDF as bytes.
    Embeds repeating digital watermark on every page.
    """
    try:
        font = FONT_MAP.get(font_style, "Helvetica")
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2.5 * cm,
            leftMargin=2.5 * cm,
            topMargin=3 * cm,
            bottomMargin=3 * cm,
        )

        styles = getSampleStyleSheet()
        body_style = ParagraphStyle(
            name="Body",
            fontName=font,
            fontSize=font_size,
            leading=font_size * 1.5,
            spaceAfter=6,
        )
        header_style = ParagraphStyle(
            name="Header",
            fontName=font + "-Bold" if font == "Helvetica" else font,
            fontSize=font_size - 2,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        footer_style = ParagraphStyle(
            name="Footer",
            fontName=font,
            fontSize=font_size - 3,
            textColor=colors.HexColor("#888888"),
            alignment=TA_CENTER,
        )

        def draw_watermark(canvas, doc):
            # Draw repeating diagonal watermark (refined)
            if not watermark_text:
                return
            canvas.saveState()
            canvas.setFont(font, 18)
            canvas.setStrokeColor(colors.gray, alpha=0.1)
            canvas.setFillColor(colors.gray, alpha=0.1)
            
            # Start from the left-most possible coordinate and tile
            for x in range(-50, int(A4[0]) + 100, 200):
                for y in range(0, int(A4[1]) + 100, 150):
                    canvas.saveState()
                    canvas.translate(x, y)
                    canvas.rotate(-35)
                    canvas.drawString(0, 0, watermark_text)
                    canvas.restoreState()
            canvas.restoreState()

        story = []

        if header:
            story.append(Paragraph(header, header_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
            story.append(Spacer(1, 0.3 * cm))

        for para in content.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para.replace("\n", "<br/>"), body_style))
                story.append(Spacer(1, 0.2 * cm))

        if footer:
            story.append(Spacer(1, 0.5 * cm))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
            story.append(Paragraph(footer, footer_style))

        # Build doc with repeating watermark on every page
        doc.build(story, onFirstPage=draw_watermark, onLaterPages=draw_watermark)
        return buffer.getvalue()

    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc
