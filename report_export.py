from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor('#153A63')
TEXT = colors.HexColor('#121826')
MUTED = colors.HexColor('#667085')
LIGHT = colors.HexColor('#F3F5F7')
HEADER = colors.HexColor('#E9EDF2')
BORDER = colors.HexColor('#B9C3CE')
WHITE = colors.white


def _safe(value) -> str:
    if value in (None, ''):
        return ''
    return escape(str(value)).replace('\n', '<br/>')


def _grade_text(value) -> str:
    return '-' if value in (None, '', '-') else str(value)


def build_report_pdf(
    profile: dict,
    impact: str,
    grades: list[dict],
    summary: str,
    observations: dict,
    overall: dict | None = None,
) -> bytes:
    """Generate the report-facing PDF used by the scouting grader.

    Reading order:
      Profile -> Overall Projection -> Impact -> Tool Grades -> Summary -> Observations

    Overall Projection is omitted when all three grades are blank.
    """
    out = BytesIO()
    doc = SimpleDocTemplate(
        out,
        pagesize=letter,
        rightMargin=0.48 * inch,
        leftMargin=0.48 * inch,
        topMargin=0.38 * inch,
        bottomMargin=0.38 * inch,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        'ScoutTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=17, leading=19, textColor=TEXT, spaceAfter=3,
    )
    subtitle = ParagraphStyle(
        'ScoutSubtitle', parent=styles['BodyText'], fontName='Helvetica',
        fontSize=8.3, leading=10, textColor=MUTED, spaceAfter=4,
    )
    h = ParagraphStyle(
        'ScoutH', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=10.5, leading=12, textColor=NAVY, spaceBefore=7, spaceAfter=4,
    )
    body = ParagraphStyle(
        'ScoutBody', parent=styles['BodyText'], fontName='Helvetica',
        fontSize=8.7, leading=11.2, textColor=TEXT, alignment=TA_LEFT,
    )
    small = ParagraphStyle(
        'ScoutSmall', parent=body, fontSize=7.5, leading=9.2,
    )
    label = ParagraphStyle(
        'ScoutLabel', parent=small, fontName='Helvetica-Bold', textColor=MUTED,
    )
    card_head = ParagraphStyle(
        'CardHead', parent=small, fontName='Helvetica-Bold', fontSize=8.4,
        leading=9.5, textColor=NAVY,
    )

    player = _safe(profile.get('name') or 'Player')
    bats = str(profile.get('bats') or '').strip().upper()
    throws = str(profile.get('throws') or '').strip().upper()
    if throws == 'RHP':
        throws = 'R'
    elif throws == 'LHP':
        throws = 'L'
    bt = ''
    if bats or throws:
        bt = f"B/T: {bats or '--'}/{throws or '--'}"

    subtitle_parts = []
    if profile.get('position'):
        subtitle_parts.append(str(profile['position']))
    if profile.get('school'):
        subtitle_parts.append(str(profile['school']))
    if bt:
        subtitle_parts.append(bt)
    if profile.get('height'):
        subtitle_parts.append(f"Ht: {profile['height']}")
    if profile.get('weight'):
        subtitle_parts.append(f"Wt: {profile['weight']}")
    if profile.get('draft_class'):
        subtitle_parts.append(f"Draft: {profile['draft_class']}")

    story = [Paragraph(player, title)]
    if subtitle_parts:
        story.append(Paragraph(_safe('  |  '.join(subtitle_parts)), subtitle))

    # thin organizational divider
    divider = Table([['']], colWidths=[7.48 * inch], rowHeights=[0.02 * inch])
    divider.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY)]))
    story.extend([divider, Spacer(1, 4)])

    overall = overall or {}
    overall_vals = [overall.get('floor'), overall.get('most_likely'), overall.get('ceiling')]
    if any(v not in (None, '', '-') for v in overall_vals):
        story.append(Paragraph('OVERALL PROJECTION', h))
        overall_data = [
            [Paragraph('Floor', label), Paragraph('Most Likely', label), Paragraph('Ceiling', label)],
            [Paragraph(_grade_text(overall.get('floor')), body),
             Paragraph(_grade_text(overall.get('most_likely')), body),
             Paragraph(_grade_text(overall.get('ceiling')), body)],
        ]
        ot = Table(overall_data, colWidths=[2.49 * inch] * 3, rowHeights=[0.23 * inch, 0.34 * inch])
        ot.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.35, BORDER),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(ot)

    story.append(Paragraph('IMPACT STATEMENT', h))
    impact_box = Table([[Paragraph(_safe(impact or '-'), body)]], colWidths=[7.47 * inch])
    impact_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.35, LIGHT),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(impact_box)

    story.append(Paragraph('TOOL GRADES', h))
    data = [[
        Paragraph('Tool', ParagraphStyle('th1', parent=small, fontName='Helvetica-Bold', textColor=TEXT)),
        Paragraph('Present', ParagraphStyle('th2', parent=small, fontName='Helvetica-Bold', textColor=TEXT)),
        Paragraph('Future', ParagraphStyle('th3', parent=small, fontName='Helvetica-Bold', textColor=TEXT)),
        Paragraph('Velo / Range', ParagraphStyle('th4', parent=small, fontName='Helvetica-Bold', textColor=TEXT)),
    ]]
    for row in grades:
        data.append([
            Paragraph(_safe(row.get('Tool', '')), ParagraphStyle('tb', parent=small, fontName='Helvetica-Bold', textColor=TEXT)),
            _grade_text(row.get('Present')),
            _grade_text(row.get('Future')),
            _safe(row.get('Velo / Range', '-')) or '-',
        ])
    t = Table(data, colWidths=[3.22 * inch, 0.9 * inch, 0.9 * inch, 2.45 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, colors.HexColor('#FAFBFC')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    story.append(Paragraph('SUMMARY', h))
    summary_box = Table([[Paragraph(_safe(summary or '-'), body)]], colWidths=[7.47 * inch])
    summary_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(summary_box)

    # Supporting observations in three visual cards. Physical is intentionally omitted;
    # body/projection belongs in Summary in this report style.
    look_pairs = [
        ('Date', observations.get('date')),
        ('Games Seen', observations.get('games_seen')),
        ('Innings Seen', observations.get('innings_seen')),
        ('Role', observations.get('role')),
    ]
    delivery_pairs = [
        ('Grade', observations.get('delivery_grade')),
        ('Arm Action', observations.get('arm_action')),
        ('Arm Angle', observations.get('arm_angle')),
    ]
    makeup_pairs = [
        ('Aggressiveness', observations.get('aggressiveness')),
        ('Instincts', observations.get('instincts')),
        ('Poise', observations.get('poise')),
    ]

    def has_value(v):
        return v not in (None, '', '-')

    has_obs = any(has_value(v) for _, v in look_pairs + delivery_pairs + makeup_pairs) or \
        has_value(observations.get('delivery_notes')) or has_value(observations.get('makeup'))

    if has_obs:
        story.append(Paragraph('OBSERVATIONS', h))

        def card(title_text: str, pairs: list[tuple[str, object]], note_label: str | None = None, note_value: object = None):
            rows = [[Paragraph(title_text, card_head), '']]
            for lab, value in pairs:
                if has_value(value):
                    rows.append([Paragraph(_safe(lab), label), Paragraph(_safe(value), small)])
            if note_label and has_value(note_value):
                rows.append([Paragraph(_safe(note_label), label), Paragraph(_safe(note_value), small)])
            tbl = Table(rows, colWidths=[1.10 * inch, 1.21 * inch])
            tbl.setStyle(TableStyle([
                ('SPAN', (0, 0), (1, 0)),
                ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BOX', (0, 0), (-1, -1), 0.35, colors.HexColor('#E3E7EB')),
            ]))
            return tbl

        look_card = card('LOOK', look_pairs)
        delivery_card = card('DELIVERY', delivery_pairs, 'Delivery Notes', observations.get('delivery_notes'))
        makeup_card = card('MAKEUP', makeup_pairs, 'On-Field Makeup', observations.get('makeup'))
        cards = Table([[look_card, delivery_card, makeup_card]], colWidths=[2.42 * inch] * 3, hAlign='LEFT')
        cards.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(KeepTogether(cards))

    doc.build(story)
    return out.getvalue()
