"""
PDF Report Generator
Generates institutional-quality equity research reports using ReportLab.
Output is suitable for sharing with recruiters and admissions committees.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Color palette
C_BLACK = colors.HexColor('#0A0E1A')
C_DARK = colors.HexColor('#0F1629')
C_GOLD = colors.HexColor('#C9A84C')
C_BLUE = colors.HexColor('#2563EB')
C_GREEN = colors.HexColor('#10B981')
C_RED = colors.HexColor('#EF4444')
C_TEXT = colors.HexColor('#1A1A2E')
C_TEXT_MUTED = colors.HexColor('#4A5568')
C_BORDER = colors.HexColor('#CBD5E0')
C_LIGHT_BG = colors.HexColor('#F7F9FC')
C_HEADER_BG = colors.HexColor('#0F1629')
C_WHITE = colors.white


def fmt(val, suffix='', prefix='', decimals=1, divisor=1, na='N/A'):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return na
    try:
        return f"{prefix}{float(val)/divisor:,.{decimals}f}{suffix}"
    except Exception:
        return na


def build_styles():
    styles = getSampleStyleSheet()
    
    custom = {
        'ReportTitle': ParagraphStyle(
            'ReportTitle', fontSize=22, textColor=C_WHITE,
            fontName='Helvetica-Bold', leading=28, alignment=TA_LEFT,
        ),
        'ReportSubtitle': ParagraphStyle(
            'ReportSubtitle', fontSize=11, textColor=C_GOLD,
            fontName='Helvetica', leading=16, alignment=TA_LEFT,
        ),
        'SectionHeader': ParagraphStyle(
            'SectionHeader', fontSize=11, textColor=C_GOLD,
            fontName='Helvetica-Bold', leading=16, spaceBefore=14, spaceAfter=6,
            borderPad=4,
        ),
        'BodyText': ParagraphStyle(
            'BodyText', fontSize=9, textColor=C_TEXT,
            fontName='Helvetica', leading=14, alignment=TA_JUSTIFY,
            spaceBefore=4, spaceAfter=4,
        ),
        'SmallText': ParagraphStyle(
            'SmallText', fontSize=8, textColor=C_TEXT_MUTED,
            fontName='Helvetica', leading=12,
        ),
        'KPILabel': ParagraphStyle(
            'KPILabel', fontSize=8, textColor=C_TEXT_MUTED,
            fontName='Helvetica', leading=11, alignment=TA_CENTER,
        ),
        'KPIValue': ParagraphStyle(
            'KPIValue', fontSize=14, textColor=C_TEXT,
            fontName='Helvetica-Bold', leading=18, alignment=TA_CENTER,
        ),
        'Recommendation': ParagraphStyle(
            'Recommendation', fontSize=16, textColor=C_WHITE,
            fontName='Helvetica-Bold', leading=20, alignment=TA_CENTER,
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader', fontSize=8, textColor=C_WHITE,
            fontName='Helvetica-Bold', leading=12, alignment=TA_CENTER,
        ),
        'TableCell': ParagraphStyle(
            'TableCell', fontSize=8.5, textColor=C_TEXT,
            fontName='Helvetica', leading=12, alignment=TA_RIGHT,
        ),
        'TableCellLeft': ParagraphStyle(
            'TableCellLeft', fontSize=8.5, textColor=C_TEXT,
            fontName='Helvetica', leading=12, alignment=TA_LEFT,
        ),
        'Disclaimer': ParagraphStyle(
            'Disclaimer', fontSize=7, textColor=C_TEXT_MUTED,
            fontName='Helvetica-Oblique', leading=10, alignment=TA_JUSTIFY,
        ),
        'AILabel': ParagraphStyle(
            'AILabel', fontSize=7.5, textColor=C_BLUE,
            fontName='Helvetica-Bold', leading=10,
        ),
        'BulletText': ParagraphStyle(
            'BulletText', fontSize=9, textColor=C_TEXT,
            fontName='Helvetica', leading=13, leftIndent=12,
            bulletIndent=4, spaceBefore=2,
        ),
    }
    return custom


def header_footer(canvas, doc, company_name, ticker, recommendation):
    """Draw header and footer on every page."""
    W, H = A4
    canvas.saveState()

    # Header bar
    canvas.setFillColor(C_HEADER_BG)
    canvas.rect(0, H - 2.2*cm, W, 2.2*cm, fill=1, stroke=0)

    canvas.setFillColor(C_GOLD)
    canvas.rect(0, H - 2.2*cm, 0.4*cm, 2.2*cm, fill=1, stroke=0)

    canvas.setFont('Helvetica-Bold', 11)
    canvas.setFillColor(C_WHITE)
    canvas.drawString(1.0*cm, H - 1.4*cm, f"EQUITY RESEARCH  |  {company_name.upper()}")

    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(C_GOLD)
    canvas.drawString(1.0*cm, H - 1.9*cm, f"{ticker}  •  AI-Assisted Research Platform")

    # Recommendation badge
    rec_colors = {
        'BUY': C_GREEN, 'ADD': C_GREEN,
        'HOLD': C_GOLD,
        'REDUCE': C_RED, 'SELL': C_RED,
    }
    rec_color = rec_colors.get(recommendation.upper(), C_GOLD)
    canvas.setFillColor(rec_color)
    canvas.roundRect(W - 3.5*cm, H - 1.9*cm, 2.8*cm, 1.0*cm, 4, fill=1, stroke=0)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(C_WHITE)
    canvas.drawCentredString(W - 2.1*cm, H - 1.35*cm, recommendation.upper())

    # Footer
    canvas.setFillColor(C_LIGHT_BG)
    canvas.rect(0, 0, W, 1.2*cm, fill=1, stroke=0)
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0, 1.2*cm, W, 1.2*cm)

    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(C_TEXT_MUTED)
    date_str = datetime.datetime.now().strftime("%d %B %Y")
    canvas.drawString(1.0*cm, 0.45*cm,
        f"AI-Assisted Equity Research Platform  |  Generated: {date_str}  |  "
        f"For educational purposes only. Not investment advice.")
    canvas.drawRightString(W - 1.0*cm, 0.45*cm, f"Page {doc.page}")

    canvas.restoreState()


def generate_pdf_report(
    info: Dict,
    metrics: Dict,
    ratios: Dict,
    dcf_result: Dict,
    peer_df: pd.DataFrame,
    memo_text: str,
    recommendation: str = "HOLD",
) -> bytes:
    """
    Generate a complete, professionally formatted PDF equity research report.
    Returns PDF as bytes for download.
    """
    buffer = io.BytesIO()
    styles = build_styles()

    company_name = info.get('longName', info.get('shortName', 'Company'))
    ticker = info.get('symbol', 'N/A')
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
    market_cap = info.get('marketCap')
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2.8*cm,
        bottomMargin=1.8*cm,
        title=f"Equity Research — {company_name}",
        author="AI-Assisted Equity Research Platform",
    )

    story = []

    # ── COVER SECTION ──────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(company_name.upper(), styles['ReportTitle']))
    story.append(Paragraph(f"{sector}  |  {industry}  |  {ticker}", styles['ReportSubtitle']))
    story.append(Spacer(1, 0.2*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_GOLD, spaceAfter=8))

    # Rating + date row
    date_str = datetime.datetime.now().strftime("%d %B %Y")
    rating_data = [[
        Paragraph(f"<b>RATING</b>", styles['KPILabel']),
        Paragraph(f"<b>PRICE</b>", styles['KPILabel']),
        Paragraph(f"<b>MARKET CAP</b>", styles['KPILabel']),
        Paragraph(f"<b>REPORT DATE</b>", styles['KPILabel']),
    ], [
        Paragraph(f"<b>{recommendation}</b>", styles['Recommendation']),
        Paragraph(f"<b>₹{current_price:,.1f}</b>" if current_price else "N/A", styles['KPIValue']),
        Paragraph(f"<b>₹{market_cap/1e7:,.0f} Cr</b>" if market_cap else "N/A", styles['KPIValue']),
        Paragraph(f"<b>{date_str}</b>", styles['KPIValue']),
    ]]

    rec_bg = {
        'BUY': C_GREEN, 'ADD': C_GREEN,
        'HOLD': C_GOLD,
        'REDUCE': C_RED, 'SELL': C_RED,
    }.get(recommendation.upper(), C_GOLD)

    rating_table = Table(rating_data, colWidths=['25%', '25%', '25%', '25%'])
    rating_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_LIGHT_BG),
        ('BACKGROUND', (0, 1), (0, 1), rec_bg),
        ('BACKGROUND', (1, 1), (-1, 1), C_WHITE),
        ('TEXTCOLOR', (0, 1), (0, 1), C_WHITE),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [C_LIGHT_BG, C_WHITE]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(rating_table)
    story.append(Spacer(1, 0.4*cm))

    # ── KEY METRICS KPI TABLE ──────────────────────────────────────────────
    story.append(Paragraph("KEY FINANCIAL METRICS", styles['SectionHeader']))

    rev = metrics.get('revenue', [])
    latest_rev = rev[-1] if rev else None
    ebitda_list = metrics.get('ebitda', [])
    latest_ebitda = ebitda_list[-1] if ebitda_list else None

    kpi_data = [
        ["Metric", "Value", "Metric", "Value", "Metric", "Value"],
        ["Revenue (LTM)", fmt(latest_rev, prefix='₹', divisor=1e7, suffix=' Cr'),
         "EBITDA Margin", fmt(ratios.get('latest_ebitda_margin'), suffix='%'),
         "Revenue CAGR", fmt(ratios.get('revenue_cagr'), suffix='%')],
        ["EBITDA (LTM)", fmt(latest_ebitda, prefix='₹', divisor=1e7, suffix=' Cr'),
         "Net Margin", fmt(ratios.get('latest_net_margin'), suffix='%'),
         "EBITDA CAGR", fmt(ratios.get('ebitda_cagr'), suffix='%')],
        ["EV/EBITDA", fmt(info.get('enterpriseToEbitda'), suffix='x'),
         "ROE", fmt(ratios.get('latest_roe'), suffix='%'),
         "D/E Ratio", fmt(ratios.get('latest_de'), decimals=2)],
        ["P/E (TTM)", fmt(info.get('trailingPE'), suffix='x'),
         "ROCE", fmt(ratios.get('latest_roce'), suffix='%'),
         "Beta", fmt(info.get('beta'), decimals=2)],
    ]

    kpi_table = Table(kpi_data, colWidths=[3.0*cm, 3.0*cm, 3.0*cm, 3.0*cm, 3.0*cm, 3.0*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (0, -1), C_LIGHT_BG),
        ('BACKGROUND', (2, 1), (2, -1), C_LIGHT_BG),
        ('BACKGROUND', (4, 1), (4, -1), C_LIGHT_BG),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.4*cm))

    # ── FINANCIAL HISTORY TABLE ────────────────────────────────────────────
    story.append(Paragraph("INCOME STATEMENT SUMMARY", styles['SectionHeader']))

    years = metrics.get('years', [])
    ni = metrics.get('net_income', [])
    ebitda_margins = []
    for r, e in zip(rev, ebitda_list):
        if r and r > 0 and e is not None:
            ebitda_margins.append(f"{e/r*100:.1f}%")
        else:
            ebitda_margins.append('N/A')

    fin_header = ['(₹ Crores)'] + years
    fin_rows = [
        ['Revenue'] + [fmt(v, divisor=1e7, decimals=0) for v in rev],
        ['EBITDA'] + [fmt(v, divisor=1e7, decimals=0) for v in ebitda_list],
        ['EBITDA Margin'] + ebitda_margins,
        ['EBIT'] + [fmt(v, divisor=1e7, decimals=0) for v in metrics.get('ebit', [])],
        ['Net Income'] + [fmt(v, divisor=1e7, decimals=0) for v in ni],
        ['Free Cash Flow'] + [fmt(v, divisor=1e7, decimals=0) for v in metrics.get('free_cash_flow', [])],
    ]

    n_cols = len(fin_header)
    col_w = [3.5*cm] + [(18.0 - 3.5) / max(n_cols - 1, 1) * cm] * (n_cols - 1)

    fin_data = [fin_header] + fin_rows
    fin_table = Table(fin_data, colWidths=col_w)
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (0, -1), 6),
        # Highlight margin row
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#EBF5FB')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#1A5276')),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 0.4*cm))

    # ── DCF VALUATION TABLE ────────────────────────────────────────────────
    if dcf_result and 'error' not in dcf_result:
        story.append(Paragraph("DCF VALUATION SUMMARY", styles['SectionHeader']))

        dcf_years = dcf_result.get('years', [])
        dcf_rev = dcf_result.get('revenues', [])
        dcf_ebitda = dcf_result.get('ebitdas', [])
        dcf_fcff = dcf_result.get('fcffs', [])
        pv_fcffs = dcf_result.get('pv_fcffs', [])

        dcf_proj_header = ['(₹ Cr)'] + dcf_years
        dcf_ebitda_margins = [f"{e/r*100:.1f}%" if r and r > 0 else 'N/A'
                               for r, e in zip(dcf_rev, dcf_ebitda)]
        dcf_proj_rows = [
            ['Revenue'] + [fmt(v, divisor=1e7, decimals=0) for v in dcf_rev],
            ['EBITDA'] + [fmt(v, divisor=1e7, decimals=0) for v in dcf_ebitda],
            ['EBITDA Margin'] + dcf_ebitda_margins,
            ['FCFF'] + [fmt(v, divisor=1e7, decimals=0) for v in dcf_fcff],
            ['PV of FCFF'] + [fmt(v, divisor=1e7, decimals=0) for v in pv_fcffs],
        ]

        dcf_n_cols = len(dcf_proj_header)
        dcf_col_w = [3.0*cm] + [(18.0 - 3.0) / max(dcf_n_cols - 1, 1) * cm] * (dcf_n_cols - 1)
        dcf_proj_data = [dcf_proj_header] + dcf_proj_rows

        dcf_proj_table = Table(dcf_proj_data, colWidths=dcf_col_w)
        dcf_proj_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, C_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (0, -1), 6),
        ]))
        story.append(dcf_proj_table)
        story.append(Spacer(1, 0.3*cm))

        # WACC & Valuation bridge
        wacc_val = dcf_result.get('wacc', 0)
        tgr = dcf_result.get('terminal_growth', 0)
        ev = dcf_result.get('enterprise_value', 0)
        eq_val = dcf_result.get('equity_value', 0)
        net_debt = dcf_result.get('net_debt', 0)
        sum_pv = dcf_result.get('sum_pv_fcffs', 0)
        pv_tv = dcf_result.get('pv_terminal', 0)

        wacc_data_rows = [
            ["WACC ASSUMPTIONS", "", "VALUATION BRIDGE", ""],
            ["Risk-Free Rate", fmt(dcf_result.get('wacc', 0) * 0.6, suffix='%'),
             "PV Explicit FCFFs (₹Cr)", fmt(sum_pv, divisor=1e7, decimals=0)],
            ["WACC", fmt(wacc_val * 100, suffix='%'),
             "PV Terminal Value (₹Cr)", fmt(pv_tv, divisor=1e7, decimals=0)],
            ["Terminal Growth Rate", fmt(tgr * 100, suffix='%'),
             "Enterprise Value (₹Cr)", fmt(ev, divisor=1e7, decimals=0)],
            ["Tax Rate", fmt(dcf_result.get('tax_rate', 0) * 100, suffix='%'),
             "Less: Net Debt (₹Cr)", fmt(net_debt, divisor=1e7, decimals=0)],
            ["EBITDA Margin (Target)", fmt(dcf_result.get('ebitda_margin_target', 0) * 100, suffix='%'),
             "Equity Value (₹Cr)", fmt(eq_val, divisor=1e7, decimals=0)],
        ]

        wacc_table = Table(wacc_data_rows, colWidths=[4.5*cm, 3.5*cm, 5.5*cm, 4.5*cm])
        wacc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), C_HEADER_BG),
            ('BACKGROUND', (2, 0), (3, 0), C_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, C_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (0, -1), 6),
            ('BACKGROUND', (2, -1), (3, -1), colors.HexColor('#D5F5E3')),
            ('TEXTCOLOR', (2, -1), (3, -1), colors.HexColor('#1E8449')),
            ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
        ]))
        story.append(wacc_table)
        story.append(Spacer(1, 0.4*cm))

    # ── PEER COMPARABLES TABLE ─────────────────────────────────────────────
    if peer_df is not None and not peer_df.empty:
        story.append(Paragraph("COMPARABLE COMPANY ANALYSIS", styles['SectionHeader']))

        peer_cols = list(peer_df.columns)
        peer_header = peer_cols

        peer_table_data = [peer_header]
        for _, row in peer_df.iterrows():
            table_row = []
            for col in peer_cols:
                val = row[col]
                if pd.isna(val) if isinstance(val, float) else val is None:
                    table_row.append('N/A')
                elif isinstance(val, float):
                    table_row.append(f"{val:,.1f}")
                else:
                    table_row.append(str(val))
            peer_table_data.append(table_row)

        n_peer_cols = len(peer_cols)
        peer_col_widths = [3.5*cm, 1.8*cm] + [(18.0 - 5.3) / max(n_peer_cols - 2, 1) * cm] * (n_peer_cols - 2)

        peer_table_obj = Table(peer_table_data, colWidths=peer_col_widths)
        peer_table_obj.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, C_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (1, -1), 6),
        ]))
        story.append(peer_table_obj)
        story.append(Spacer(1, 0.4*cm))

    # ── AI INVESTMENT MEMO ─────────────────────────────────────────────────
    if memo_text:
        story.append(PageBreak())
        story.append(Paragraph("INVESTMENT MEMO — AI ASSISTED ANALYSIS", styles['SectionHeader']))
        story.append(Paragraph(
            "⚠ AI-ASSISTED ANALYSIS — For educational purposes only. "
            "AI outputs are labeled and based on available data. "
            "Do not use as investment advice.",
            styles['AILabel']
        ))
        story.append(Spacer(1, 0.2*cm))

        for line in memo_text.split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.15*cm))
            elif line.startswith('##') or line.isupper() or line.endswith(':'):
                clean = line.replace('##', '').replace('#', '').strip()
                story.append(Paragraph(clean, styles['SectionHeader']))
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                clean = line.lstrip('•-* ').strip()
                story.append(Paragraph(f"• {clean}", styles['BulletText']))
            else:
                story.append(Paragraph(line, styles['BodyText']))

    # ── DISCLAIMER ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "DISCLAIMER: This report has been generated by an AI-Assisted Equity Research Platform "
        "for educational and portfolio demonstration purposes only. It does not constitute "
        "investment advice, a solicitation, or a recommendation to buy or sell any security. "
        "Financial data is sourced from publicly available market data via yfinance. "
        "AI-generated analysis sections (labeled accordingly) are produced by Claude (Anthropic) "
        "and may contain inaccuracies. Always conduct independent research and consult a "
        "registered financial advisor before making investment decisions. Past performance "
        "is not indicative of future results. The author makes no representations as to the "
        "accuracy or completeness of any information in this report.",
        styles['Disclaimer']
    ))

    # Build with header/footer callback
    doc.build(
        story,
        onFirstPage=lambda c, d: header_footer(c, d, company_name, ticker, recommendation),
        onLaterPages=lambda c, d: header_footer(c, d, company_name, ticker, recommendation),
    )

    buffer.seek(0)
    return buffer.read()
