import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24
    )

    styles = getSampleStyleSheet()

    # Custom styles tailored for single-page layout
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=19,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#2563EB'),
        spaceAfter=4
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=5,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=2
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#111827')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#1E3A8A')
    )

    note_box_style = ParagraphStyle(
        'NoteBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#1E40AF')
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph('10K Running Training Plan (Final 6-Week Compressed Schedule)', title_style))
    story.append(Paragraph('<b>Goal Time:</b> 60:30 &ndash; 61:30 (Pace: 6:03 &ndash; 6:09/km) &nbsp;|&nbsp; <b>Race Day:</b> Sunday, October 11, 2026 &nbsp;|&nbsp; <b>Current Date:</b> Friday, Aug 28, 2026 (Wk 7)', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#2563EB'), spaceBefore=1, spaceAfter=4))

    # Executive Summary / Mapping Status Box
    mapping_text = '''<b>Mapping Verification &amp; Schedule Alignment Analysis:</b><br/>
&bull; <b>Current Position:</b> Today is <b>Friday, August 28, 2026</b> (Week 7 Friday in plan). You have Friday's 5.5 km easy run + strides and Sunday's 13 km long run remaining in Week 7.<br/>
&bull; <b>Race Day Alignment:</b> Race day is <b>Sunday, October 11, 2026</b>. From Aug 31 to Oct 11 is <b>exactly 6 calendar weeks</b> (Weeks 8&ndash;13).<br/>
&bull; <b>Schedule Mapping Correction:</b> <i>10km_plan_compressed.pdf</i> assumed a Sat Oct 10 race. With your actual race on <b>Sunday Oct 11</b>, <b>Week 13 (Race Week) maps cleanly back to your standard Tue / Thu / Fri / Sun routine</b> (Tue 4x400m, Thu easy shakeout, Fri 3km easy + strides, Sun 10K Race Day).<br/>
&bull; <b>Preserved Safeguards:</b> All recovery weeks (Wk 8 &amp; Wk 11), peak week (Wk 10 @ 41 km), and sharpen week (Wk 12) from the compressed design are fully intact.
'''

    summary_table = Table([[Paragraph(mapping_text, note_box_style)]], colWidths=[564])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BORDER', (0,0), (-1,-1), 0.75, colors.HexColor('#BFDBFE')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4))

    # Remaining Week 7 Table
    story.append(Paragraph('Current Week: Remaining Sessions in Week 7 (Aug 28 &ndash; Aug 30)', h2_style))

    wk7_data = [
        [Paragraph('Day / Date', table_header_style), Paragraph('Prescribed Session Details', table_header_style), Paragraph('Target Pace &amp; Notes', table_header_style)],
        [Paragraph('<b>Friday 28 Aug (Today)</b>', table_cell_style), Paragraph('5.5 km Easy Run + 6x100m strides @ 5:30/km (100m jog recovery)', table_cell_style), Paragraph('Easy: 7:20&ndash;7:40/km | Strides: ~5:30/km', table_cell_style)],
        [Paragraph('<b>Sunday 30 Aug</b>', table_cell_style), Paragraph('13 km Long Easy Run + 6x100m strides @ 5:30/km (100m jog recovery)', table_cell_style), Paragraph('Easy: 7:20&ndash;7:40/km | Strides: ~5:30/km', table_cell_style)]
    ]
    wk7_table = Table(wk7_data, colWidths=[120, 264, 180])
    wk7_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
    ]))
    story.append(wk7_table)
    story.append(Spacer(1, 4))

    # Final Compressed 6-Week Plan Table
    story.append(Paragraph('Final 6-Week Compressed Plan (Weeks 8 &ndash; 13: Aug 31 &ndash; Oct 11)', h2_style))

    plan_data = [
        [
            Paragraph('Wk &amp; Role', table_header_style),
            Paragraph('Dates', table_header_style),
            Paragraph('Tuesday (Quality)', table_header_style),
            Paragraph('Thursday (Tempo/Thresh)', table_header_style),
            Paragraph('Friday (Easy)', table_header_style),
            Paragraph('Sunday (Long Run / Race)', table_header_style),
            Paragraph('Vol', table_header_style)
        ],
        [
            Paragraph('<b>Wk 8</b><br/><font color="#2563EB">Recovery</font>', table_cell_style),
            Paragraph('Aug 31 &ndash;<br/>Sep 6', table_cell_style),
            Paragraph('<b>5K Time Trial</b> (replaces hills) + w/u+c/d', table_cell_style),
            Paragraph('20 min tempo @ 6:18&ndash;6:28/km + w/u+c/d (~5.4 km)', table_cell_style),
            Paragraph('4 km Easy (7:20&ndash;7:40/km) + 4x100m strides', table_cell_style),
            Paragraph('9 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('~24.6 km', table_cell_bold)
        ],
        [
            Paragraph('<b>Wk 9</b><br/><font color="#059669">Build</font>', table_cell_style),
            Paragraph('Sep 7 &ndash;<br/>Sep 13', table_cell_style),
            Paragraph('5x1 km @ 6:03&ndash;6:09/km (2 min jog) + w/u+c/d (~8.2 km)', table_cell_style),
            Paragraph('2x20 min threshold @ 6:18&ndash;6:28/km (2 min jog) + w/u+c/d (~8.7 km)', table_cell_style),
            Paragraph('6 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('13 km Easy (last 2 km @ 6:45&ndash;6:55/km) + 6x100m strides', table_cell_style),
            Paragraph('37.5 km', table_cell_bold)
        ],
        [
            Paragraph('<b>Wk 10</b><br/><font color="#DC2626">Peak Load</font>', table_cell_style),
            Paragraph('Sep 14 &ndash;<br/>Sep 20', table_cell_style),
            Paragraph('6x1 km @ 6:03&ndash;6:09/km (90s jog) + w/u+c/d (~9.1 km)', table_cell_style),
            Paragraph('3x12 min threshold (2 min jog) + w/u+c/d (~8.3 km)', table_cell_style),
            Paragraph('7 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('15 km Easy (last 5 km @ 6:45&ndash;6:55/km) + 6x100m strides', table_cell_style),
            Paragraph('41.0 km', table_cell_bold)
        ],
        [
            Paragraph('<b>Wk 11</b><br/><font color="#2563EB">Cutback</font>', table_cell_style),
            Paragraph('Sep 21 &ndash;<br/>Sep 27', table_cell_style),
            Paragraph('4x800m @ 6:03&ndash;6:09/km (2 min jog) + w/u+c/d (~6.2 km)', table_cell_style),
            Paragraph('20 min tempo @ 6:18&ndash;6:28/km + w/u+c/d (~5.4 km)', table_cell_style),
            Paragraph('5 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('10 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('27.5 km', table_cell_bold)
        ],
        [
            Paragraph('<b>Wk 12</b><br/><font color="#D97706">Sharpen</font>', table_cell_style),
            Paragraph('Sep 28 &ndash;<br/>Oct 4', table_cell_style),
            Paragraph('4x1 km sharp @ 5:55&ndash;6:05/km (2 min jog) + w/u+c/d (~7 km)', table_cell_style),
            Paragraph('25 min tempo @ 6:18&ndash;6:28/km + w/u+c/d (~6.1 km)', table_cell_style),
            Paragraph('6 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('12 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('32.7 km', table_cell_bold)
        ],
        [
            Paragraph('<b>Wk 13</b><br/><font color="#7C3AED">Taper/Race</font>', table_cell_style),
            Paragraph('Oct 5 &ndash;<br/>Oct 11', table_cell_style),
            Paragraph('4x400m @ 5:38&ndash;5:48/km (90s jog) + w/u+c/d (~4.4 km)', table_cell_style),
            Paragraph('20 min Easy shakeout (~2.6 km)', table_cell_style),
            Paragraph('3 km Easy + 4x100m strides (no strides after today)', table_cell_style),
            Paragraph('<b>10K RACE DAY</b><br/>Goal: 60:30&ndash;61:30<br/>(6:03&ndash;6:09/km)', table_cell_bold),
            Paragraph('~20.5 km', table_cell_bold)
        ],
    ]

    plan_table = Table(plan_data, colWidths=[55, 55, 110, 110, 98, 98, 38])
    plan_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 2.5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FEF2F2')), # peak week highlight
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,5), (-1,5), colors.white),
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor('#F3E8FF')), # race week highlight
    ]))
    story.append(plan_table)
    story.append(Spacer(1, 4))

    # Pace Target Reference Table
    story.append(Paragraph('Pace Targets &amp; Zone Reference', h2_style))

    pace_data = [
        [Paragraph('Zone / Intensity', table_header_style), Paragraph('Target Pace', table_header_style), Paragraph('Offset from 10K Goal', table_header_style), Paragraph('Primary Purpose &amp; Application', table_header_style)],
        [Paragraph('<b>Easy / Long Run</b>', table_cell_style), Paragraph('7:20 &ndash; 7:40 /km', table_cell_style), Paragraph('71&ndash;91s slower', table_cell_style), Paragraph('Aerobic development (Zone 2-3 HR). Used for Fri easy &amp; Sun long runs.', table_cell_style)],
        [Paragraph('<b>Marathon Effort</b>', table_cell_style), Paragraph('6:45 &ndash; 6:55 /km', table_cell_style), Paragraph('40&ndash;50s slower', table_cell_style), Paragraph('Moderate steady effort. Used for long-run finishes (Weeks 9 &amp; 10).', table_cell_style)],
        [Paragraph('<b>Tempo / Threshold</b>', table_cell_style), Paragraph('6:18 &ndash; 6:28 /km', table_cell_style), Paragraph('13&ndash;23s slower', table_cell_style), Paragraph('Comfortably hard. Core Thursday session to build stamina.', table_cell_style)],
        [Paragraph('<b>10K Goal Pace</b>', table_cell_style), Paragraph('6:03 &ndash; 6:09 /km', table_cell_style), Paragraph('Target Race Pace', table_cell_bold), Paragraph('Hard but sustainable. Used for 800m&ndash;1km quality reps &amp; Race Day.', table_cell_style)],
        [Paragraph('<b>5K Pace</b>', table_cell_style), Paragraph('5:38 &ndash; 5:48 /km', table_cell_style), Paragraph('14&ndash;22s faster', table_cell_style), Paragraph('Very hard. Used for 400m reps &amp; Week 8 5K Time Trial.', table_cell_style)],
        [Paragraph('<b>Strides</b>', table_cell_style), Paragraph('~5:30 /km (~33s/100m)', table_cell_style), Paragraph('Faster than 5K pace', table_cell_style), Paragraph('Fast, relaxed 100m reps after Friday &amp; Sunday runs to maintain leg speed.', table_cell_style)]
    ]

    pace_table = Table(pace_data, colWidths=[110, 100, 110, 244])
    pace_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 2.5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#EFF6FF')),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,6), (-1,6), colors.white),
    ]))
    story.append(pace_table)
    story.append(Spacer(1, 4))

    # Core Protocols
    story.append(Paragraph('Core Training Protocols &amp; Guidelines', h2_style))

    protocols_text = '''<b>1. Stride Protocol:</b> Execute after Friday easy runs &amp; Sunday long runs (not standalone). Sequence: (1) Finish main run; (2) 3&ndash;5 min walk/light jog transition; (3) 100m reps @ ~5:30/km (~33s/rep), fast &amp; relaxed (focus on form &amp; turnover); (4) 100m jog recovery; (5) 5 min cool-down. Regular weeks: 6x100m. Recovery weeks (8, 11) &amp; Wk 13 Friday: 4x100m.<br/>
<b>2. Warm-Up &amp; Cooldown:</b> Quality/tempo days require: 10&ndash;15 min easy jog + 3&ndash;4 strides before main rep/tempo block. Cooldown: 5&ndash;10 min easy jog.<br/>
<b>3. Peak-to-Race Gap Safeguard:</b> Exactly 3 weeks between peak load (Wk 10 @ 41 km) and race day. Prioritize recovery over forcing volume if fatigued.
'''

    proto_table = Table([[Paragraph(protocols_text, body_style)]], colWidths=[564])
    proto_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BORDER', (0,0), (-1,-1), 0.75, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(proto_table)

    doc.build(story)
    print("PDF generated successfully at:", output_path)

if __name__ == '__main__':
    target_path = '10K_Training_Plan_60-61_Final.pdf'
    generate_pdf(target_path)
