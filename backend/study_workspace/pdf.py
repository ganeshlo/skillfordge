from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def note_pdf(note):
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"{note.resource.title} - LearnOS notes",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="NoteTitle", parent=styles["Title"], textColor=colors.HexColor("#4F46E5"), alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name="Meta", parent=styles["Normal"], textColor=colors.HexColor("#64748B"), alignment=TA_CENTER, fontSize=8, spaceAfter=16))
    styles.add(ParagraphStyle(name="NoteBody", parent=styles["BodyText"], leading=16, spaceAfter=7))
    styles.add(ParagraphStyle(name="NoteBullet", parent=styles["BodyText"], leftIndent=12, firstLineIndent=-7, leading=15, bulletIndent=4, spaceAfter=4))
    story = [
        Paragraph(escape(note.resource.title), styles["NoteTitle"]),
        Paragraph(f"LearnOS study notes · {escape(note.resource.channel_name or 'YouTube')} · {'AI generated' if note.source == 'ai' else 'Personal note'}", styles["Meta"]),
    ]
    for raw_line in note.content.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 5))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), styles["Heading3"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), styles["Heading2"]))
        elif line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), styles["Heading1"]))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph(f"• {escape(line[2:])}", styles["NoteBullet"]))
        else:
            story.append(Paragraph(escape(line), styles["NoteBody"]))
    document.build(story)
    return output.getvalue()
