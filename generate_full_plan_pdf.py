import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=28,
        rightMargin=28,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()

    # Custom styles
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
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=6,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=3
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#111827')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1E3A8A')
    )

    note_box_style = ParagraphStyle(
        'NoteBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E40AF')
    )

    story = []

    # ================= PAGE 1 =================
    # Title & Metadata Header
    story.append(Paragraph('10K Running Training Plan &mdash; Full Master Schedule (Weeks 1 to Race Day)', title_style))
    story.append(Paragraph('<b>Goal Time:</b> 60:30 &ndash; 61:30 (Pace: 6:03 &ndash; 6:09/km) &nbsp;|&nbsp; <b>Race Day:</b> Sunday, October 11, 2026 &nbsp;|&nbsp; <b>Current Position:</b> Week 7 Friday (Aug 28, 2026)', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#2563EB'), spaceBefore=1, spaceAfter=4))

    # Executive Summary / Mapping Status Box
    mapping_text = '''<b>Master Schedule Architecture &amp; Date Mapping Verification:</b><br/>
&bull; <b>Weeks 1 &ndash; 7 (Base &amp; Current Progress):</b> Built from <i>10km_plan_60-61.pdf</i>. Today is <b>Friday, August 28, 2026 (Week 7 Friday)</b>.<br/>
&bull; <b>Weeks 8 &ndash; 13 (Compressed Buildup):</b> Seamlessly transitions into the compressed schedule from <i>10km_plan_compressed.pdf</i> leading to <b>Race Day on Sunday, October 11, 2026</b>.<br/>
&bull; <b>Race Day Alignment Correction:</b> Race day is Sunday Oct 11, so <b>Week 13 (Race Week) maps cleanly back to your standard Tue / Thu / Fri / Sun routine</b> (Tue 4x400m, Thu easy shakeout, Fri 3km easy + strides, Sun 10K Race Day).
'''

    summary_table = Table([[Paragraph(mapping_text, note_box_style)]], colWidths=[556])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BORDER', (0,0), (-1,-1), 0.75, colors.HexColor('#BFDBFE')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4))

    # Full Master Table (Weeks 1 to 13)
    story.append(Paragraph('Master Weekly Training Plan (Weeks 1 &ndash; 13)', h2_style))

    plan_data = [
        [
            Paragraph('Wk &amp; Role', table_header_style),
            Paragraph('Dates / Phase', table_header_style),
            Paragraph('Tuesday (Quality)', table_header_style),
            Paragraph('Thursday (Tempo/Thresh)', table_header_style),
            Paragraph('Friday (Easy)', table_header_style),
            Paragraph('Sunday (Long Run / Race)', table_header_style),
            Paragraph('Vol', table_header_style)
        ],
        # Week 1
        [
            Paragraph('<b>Wk 1</b>', table_cell_style),
            Paragraph('Base', table_cell_style),
            Paragraph('6x400m @ 5:38&ndash;5:48/km (90s jog) + w/u+c/d (~5.5 km)', table_cell_style),
            Paragraph('20 min tempo @ 6:18&ndash;6:28/km + w/u+c/d (~5.4 km)', table_cell_style),
            Paragraph('3 km Easy (7:20&ndash;7:40/km) + 6x100m strides', table_cell_style),
            Paragraph('8 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('23.5 km', table_cell_bold)
        ],
        # Week 2
        [
            Paragraph('<b>Wk 2</b>', table_cell_style),
            Paragraph('Base', table_cell_style),
            Paragraph('8x400m @ 5:38&ndash;5:48/km (90s jog) + w/u+c/d (~6.7 km)', table_cell_style),
            Paragraph('20 min tempo + w/u+c/d (~5.4 km)', table_cell_style),
            Paragraph('3.5 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('9 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('26.1 km', table_cell_bold)
        ],
        # Week 3
        [
            Paragraph('<b>Wk 3</b>', table_cell_style),
            Paragraph('Base', table_cell_style),
            Paragraph('5x600m @ 5:38&ndash;5:48/km (2 min jog) + w/u+c/d (~6.2 km)', table_cell_style),
            Paragraph('22 min tempo + w/u+c/d (~5.7 km)', table_cell_style),
            Paragraph('4 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('10 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('27.5 km', table_cell_bold)
        ],
        # Week 4
        [
            Paragraph('<b>Wk 4</b><br/><font color="#2563EB">Recovery</font>', table_cell_style),
            Paragraph('Cutback', table_cell_style),
            Paragraph('6x400m @ 5:38&ndash;5:48/km (90s jog) + w/u+c/d (~5.5 km)', table_cell_style),
            Paragraph('18 min tempo + w/u+c/d (~5.1 km)', table_cell_style),
            Paragraph('3 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('7 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('21.6 km', table_cell_bold)
        ],
        # Week 5
        [
            Paragraph('<b>Wk 5</b>', table_cell_style),
            Paragraph('Build', table_cell_style),
            Paragraph('5x800m @ 6:03&ndash;6:09/km (2 min jog) + w/u+c/d (~7.2 km)', table_cell_style),
            Paragraph('25 min tempo + w/u+c/d (~6.1 km)', table_cell_style),
            Paragraph('4.5 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('11 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('30.4 km', table_cell_bold)
        ],
        # Week 6
        [
            Paragraph('<b>Wk 6</b>', table_cell_style),
            Paragraph('Build', table_cell_style),
            Paragraph('10x60s hill repeats + w/u+c/d (~6.0 km)', table_cell_style),
            Paragraph('3x10 min tempo (2 min jog) + w/u+c/d (~7.4 km)', table_cell_style),
            Paragraph('5 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('12 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('32.0 km', table_cell_bold)
        ],
        # Week 7 (CURRENT WEEK)
        [
            Paragraph('<b>Wk 7</b><br/><font color="#D97706">CURRENT</font>', table_cell_bold),
            Paragraph('Aug 24 &ndash;<br/>Aug 30', table_cell_bold),
            Paragraph('6x800m @ 6:03&ndash;6:09/km (2 min jog) (~8.2 km)', table_cell_style),
            Paragraph('30 min tempo + w/u+c/d (~6.9 km)', table_cell_style),
            Paragraph('<b>5.5 km Easy + 6 strides (TODAY Aug 28)</b>', table_cell_bold),
            Paragraph('13 km Easy + 6 strides @ 5:30/km (Aug 30)', table_cell_bold),
            Paragraph('35.2 km', table_cell_bold)
        ],
        # Week 8
        [
            Paragraph('<b>Wk 8</b><br/><font color="#2563EB">Recovery</font>', table_cell_style),
            Paragraph('Aug 31 &ndash;<br/>Sep 6', table_cell_style),
            Paragraph('<b>5K Time Trial</b> (replaces hills) + w/u+c/d', table_cell_style),
            Paragraph('20 min tempo @ 6:18&ndash;6:28/km + w/u+c/d (~5.4 km)', table_cell_style),
            Paragraph('4 km Easy (7:20&ndash;7:40/km) + 4x100m strides', table_cell_style),
            Paragraph('9 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('~24.6 km', table_cell_bold)
        ],
        # Week 9
        [
            Paragraph('<b>Wk 9</b><br/><font color="#059669">Build</font>', table_cell_style),
            Paragraph('Sep 7 &ndash;<br/>Sep 13', table_cell_style),
            Paragraph('5x1 km @ 6:03&ndash;6:09/km (2 min jog) + w/u+c/d (~8.2 km)', table_cell_style),
            Paragraph('2x20 min threshold @ 6:18&ndash;6:28/km (2 min jog) + w/u+c/d (~8.7 km)', table_cell_style),
            Paragraph('6 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('13 km Easy (last 2 km @ 6:45&ndash;6:55/km) + 6x100m strides', table_cell_style),
            Paragraph('37.5 km', table_cell_bold)
        ],
        # Week 10
        [
            Paragraph('<b>Wk 10</b><br/><font color="#DC2626">Peak Load</font>', table_cell_style),
            Paragraph('Sep 14 &ndash;<br/>Sep 20', table_cell_style),
            Paragraph('6x1 km @ 6:03&ndash;6:09/km (90s jog) + w/u+c/d (~9.1 km)', table_cell_style),
            Paragraph('3x12 min threshold (2 min jog) + w/u+c/d (~8.3 km)', table_cell_style),
            Paragraph('7 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('15 km Easy (last 5 km @ 6:45&ndash;6:55/km) + 6x100m strides', table_cell_style),
            Paragraph('41.0 km', table_cell_bold)
        ],
        # Week 11
        [
            Paragraph('<b>Wk 11</b><br/><font color="#2563EB">Cutback</font>', table_cell_style),
            Paragraph('Sep 21 &ndash;<br/>Sep 27', table_cell_style),
            Paragraph('4x800m @ 6:03&ndash;6:09/km (2 min jog) + w/u+c/d (~6.2 km)', table_cell_style),
            Paragraph('20 min tempo @ 6:18&ndash;6:28/km + w/u+c/d (~5.4 km)', table_cell_style),
            Paragraph('5 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('10 km Easy + 4x100m strides @ 5:30/km', table_cell_style),
            Paragraph('27.5 km', table_cell_bold)
        ],
        # Week 12
        [
            Paragraph('<b>Wk 12</b><br/><font color="#D97706">Sharpen</font>', table_cell_style),
            Paragraph('Sep 28 &ndash;<br/>Oct 4', table_cell_style),
            Paragraph('4x1 km sharp @ 5:55&ndash;6:05/km (2 min jog) + w/u+c/d (~7 km)', table_cell_style),
            Paragraph('25 min tempo @ 6:18&ndash;6:28/km + w/u+c/d (~6.1 km)', table_cell_style),
            Paragraph('6 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('12 km Easy + 6x100m strides @ 5:30/km', table_cell_style),
            Paragraph('32.7 km', table_cell_bold)
        ],
        # Week 13
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

    plan_table = Table(plan_data, colWidths=[52, 52, 108, 108, 98, 98, 40])
    plan_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 1.5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,6), (-1,6), colors.white),
        ('BACKGROUND', (0,7), (-1,7), colors.HexColor('#FEF9C3')), # highlight CURRENT week 7
        ('BACKGROUND', (0,8), (-1,8), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,9), (-1,9), colors.white),
        ('BACKGROUND', (0,10), (-1,10), colors.HexColor('#FEF2F2')), # highlight PEAK week 10
        ('BACKGROUND', (0,11), (-1,11), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,12), (-1,12), colors.white),
        ('BACKGROUND', (0,13), (-1,13), colors.HexColor('#F3E8FF')), # highlight RACE week 13
    ]))
    story.append(plan_table)

    # Page Break to Page 2
    story.append(PageBreak())

    # ================= PAGE 2 =================
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

    pace_table = Table(pace_data, colWidths=[110, 100, 110, 236])
    pace_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#EFF6FF')),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,6), (-1,6), colors.white),
    ]))
    story.append(pace_table)
    story.append(Spacer(1, 8))

    # Core Protocols
    story.append(Paragraph('Core Training Protocols &amp; Guidelines', h2_style))

    protocols_text = '''<b>1. Stride Protocol:</b> Execute after Friday easy runs &amp; Sunday long runs (not standalone). Sequence: (1) Finish main run; (2) 3&ndash;5 min walk/light jog transition; (3) 100m reps @ ~5:30/km (~33s/rep), fast &amp; relaxed (focus on form &amp; turnover); (4) 100m jog recovery; (5) 5 min cool-down. Regular weeks: 6x100m. Recovery weeks (4, 8, 11) &amp; Wk 13 Friday: 4x100m. <i>No strides on Race Day!</i><br/><br/>
<b>2. Warm-Up &amp; Cooldown Protocol:</b> Quality (Tuesday) and tempo (Thursday) days require: <b>Warm-up:</b> 10&ndash;15 min easy jog + 3&ndash;4 light accelerations before main rep/tempo block. <b>Cooldown:</b> 5&ndash;10 min easy jog.<br/><br/>
<b>3. Compression Rationale &amp; Safeguards:</b> Weeks 1&ndash;7 follow the original progression. Weeks 8&ndash;13 compress the remaining buildup so Race Day lands on Sunday, October 11, 2026 while preserving all recovery cutback weeks (Wk 8 &amp; Wk 11) and the peak load week (Wk 10 @ 41 km).
'''

    proto_table = Table([[Paragraph(protocols_text, body_style)]], colWidths=[556])
    proto_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BORDER', (0,0), (-1,-1), 0.75, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(proto_table)
    story.append(Spacer(1, 8))

    # Recalibration History & Background Log
    story.append(Paragraph('Recalibration &amp; Update History', h2_style))

    history_text = '''<b>Basis for Recalibration (Aug 4):</b> Earlier versions were anchored to a 6.47km race (~69-min 10K equivalent, target 62:00&ndash;64:00). That was superseded by a clean <b>5K time trial of 28:57 (Aug 4)</b>, which Riegel-projects to 60:22. The <b>60:30&ndash;61:30 goal</b> includes a small buffer to account for double-distance fueling/aerobic demands.<br/>
&bull; <b>July 19 Update:</b> Tightened easy/long-run pace from 8:00&ndash;8:20 to 7:40&ndash;8:00/km based on Zone 2 HR stability.<br/>
&bull; <b>July 31 Update:</b> Tightened easy/long-run pace to 7:20&ndash;7:40/km after consistent runs in 28&ndash;31&deg;C heat stayed in HR Zone 2-3.
'''

    hist_table = Table([[Paragraph(history_text, body_style)]], colWidths=[556])
    hist_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFBEB')),
        ('BORDER', (0,0), (-1,-1), 0.75, colors.HexColor('#FDE68A')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(hist_table)

    doc.build(story)
    print("PDF generated successfully at:", output_path)

if __name__ == '__main__':
    target_path = '10K_Training_Plan_Master_W1-W13.pdf'
    generate_pdf(target_path)
