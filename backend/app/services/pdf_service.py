"""PDF report generation."""
from __future__ import annotations

import io
from datetime import date


def build_report_pdf(title: str, lines: list[str]) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return (title + "\n\n" + "\n".join(lines)).encode("utf-8")

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 72

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, y, title)
    y -= 28
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, y, f"Generated on {date.today().isoformat()}")
    y -= 36

    pdf.setFont("Helvetica", 11)
    for line in lines:
        for chunk in _wrap(line, 92):
            if y < 72:
                pdf.showPage()
                y = height - 72
                pdf.setFont("Helvetica", 11)
            pdf.drawString(72, y, chunk)
            y -= 18
        y -= 8

    pdf.save()
    return buffer.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]

