"""
Chart Generation Module
All charts use institutional dark theme consistent with Bloomberg/FactSet aesthetics.
Built with Plotly for interactive, export-ready visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

# Institutional color palette
COLORS = {
    'gold': '#C9A84C',
    'gold_light': '#E8C87A',
    'blue': '#2563EB',
    'blue_light': '#60A5FA',
    'green': '#10B981',
    'red': '#EF4444',
    'purple': '#8B5CF6',
    'teal': '#14B8A6',
    'bg': '#0F1629',
    'card': '#131C32',
    'grid': '#1E2D4A',
    'text': '#F0F4FF',
    'text_muted': '#8B9CB8',
    'border': '#1E2D4A',
}

BASE_LAYOUT = dict(
    paper_bgcolor=COLORS['bg'],
    plot_bgcolor=COLORS['card'],
    font=dict(family="Inter, Arial, sans-serif", color=COLORS['text'], size=12),
    margin=dict(l=50, r=30, t=50, b=50),
    xaxis=dict(
        gridcolor=COLORS['grid'],
        linecolor=COLORS['grid'],
        tickcolor=COLORS['text_muted'],
        tickfont=dict(color=COLORS['text_muted'], size=11),
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor=COLORS['grid'],
        linecolor=COLORS['grid'],
        tickcolor=COLORS['text_muted'],
        tickfont=dict(color=COLORS['text_muted'], size=11),
        showgrid=True,
        zeroline=False,
    ),
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        bordercolor=COLORS['grid'],
        font=dict(color=COLORS['text_muted'], size=11),
    ),
    hoverlabel=dict(
        bgcolor=COLORS['card'],
        bordercolor=COLORS['border'],
        font=dict(color=COLORS['text'], size=12),
    ),
)


def fmt_crore(val):
    """Format value in Indian Crores."""
    if val is None:
        return 'N/A'
    return f"₹{val/1e7:,.0f} Cr"


def revenue_chart(metrics: Dict) -> go.Figure:
    """Revenue & EBITDA trend with margin overlay."""
    years = metrics.get('years', [])
    rev = [r / 1e7 for r in metrics.get('revenue', [])]  # Convert to Crores
    ebitda = [e / 1e7 for e in metrics.get('ebitda', [])]
    margins = metrics.get('ebitda', [])
    rev_raw = metrics.get('revenue', [])
    ebitda_margins = []
    for r, e in zip(rev_raw, margins):
        if r and r > 0 and e is not None:
            ebitda_margins.append(round(e / r * 100, 1))
        else:
            ebitda_margins.append(None)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Revenue bars
    fig.add_trace(
        go.Bar(
            x=years, y=rev,
            name='Revenue (₹Cr)',
            marker_color=COLORS['blue'],
            marker_line_width=0,
            opacity=0.85,
        ),
        secondary_y=False,
    )

    # EBITDA bars
    fig.add_trace(
        go.Bar(
            x=years, y=ebitda,
            name='EBITDA (₹Cr)',
            marker_color=COLORS['gold'],
            marker_line_width=0,
            opacity=0.85,
        ),
        secondary_y=False,
    )

    # EBITDA Margin line
    fig.add_trace(
        go.Scatter(
            x=years, y=ebitda_margins,
            name='EBITDA Margin %',
            mode='lines+markers',
            line=dict(color=COLORS['green'], width=2, dash='dot'),
            marker=dict(size=6, color=COLORS['green']),
        ),
        secondary_y=True,
    )

    layout = dict(**BASE_LAYOUT)
    layout.update(
        title=dict(text='Revenue & EBITDA Trend', font=dict(color=COLORS['text'], size=14), x=0.02),
        barmode='group',
        yaxis=dict(**BASE_LAYOUT['yaxis'], title='₹ Crores'),
        yaxis2=dict(
            title='EBITDA Margin %',
            ticksuffix='%',
            gridcolor='rgba(0,0,0,0)',
            tickfont=dict(color=COLORS['green'], size=11),
        ),
        height=350,
    )
    fig.update_layout(**layout)
    return fig


def margin_chart(metrics: Dict, ratios: Dict) -> go.Figure:
    """Multi-margin trend chart."""
    years = metrics.get('years', [])
    rev = metrics.get('revenue', [])
    ebit = metrics.get('ebit', [])
    ni = metrics.get('net_income', [])
    ebitda = metrics.get('ebitda', [])

    def pct(num_list, den_list):
        result = []
        for n, d in zip(num_list, den_list):
            if d and d > 0 and n is not None:
                result.append(round(n / d * 100, 1))
            else:
                result.append(None)
        return result

    ebitda_margins = pct(ebitda, rev)
    ebit_margins = pct(ebit, rev)
    net_margins = pct(ni, rev)

    fig = go.Figure()
    for name, data, color in [
        ('EBITDA Margin', ebitda_margins, COLORS['gold']),
        ('EBIT Margin', ebit_margins, COLORS['blue_light']),
        ('Net Margin', net_margins, COLORS['green']),
    ]:
        fig.add_trace(go.Scatter(
            x=years, y=data, name=name,
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color),
        ))

    layout = dict(**BASE_LAYOUT)
    layout.update(
        title=dict(text='Margin Profile (%)', font=dict(color=COLORS['text'], size=14), x=0.02),
        yaxis=dict(**BASE_LAYOUT['yaxis'], ticksuffix='%'),
        height=300,
    )
    fig.update_layout(**layout)
    return fig


def returns_chart(ratios: Dict, metrics: Dict) -> go.Figure:
    """ROE, ROCE, ROA trend chart."""
    years = metrics.get('years', [])
    
    def safe_list(lst):
        if not lst:
            return [None] * len(years)
        return [round(v, 1) if v is not None else None for v in lst]

    fig = go.Figure()
    for name, key, color in [
        ('ROE', 'roe', COLORS['gold']),
        ('ROCE', 'roce', COLORS['blue_light']),
        ('ROA', 'roa', COLORS['green']),
    ]:
        data = safe_list(ratios.get(key, []))
        if len(data) < len(years):
            data = data + [None] * (len(years) - len(data))
        fig.add_trace(go.Scatter(
            x=years[:len(data)], y=data, name=name,
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color),
        ))

    layout = dict(**BASE_LAYOUT)
    layout.update(
        title=dict(text='Return Ratios (%)', font=dict(color=COLORS['text'], size=14), x=0.02),
        yaxis=dict(**BASE_LAYOUT['yaxis'], ticksuffix='%'),
        height=300,
    )
    fig.update_layout(**layout)
    return fig


def fcf_chart(metrics: Dict) -> go.Figure:
    """Operating CF vs Free Cash Flow waterfall."""
    years = metrics.get('years', [])
    ocf = [v / 1e7 for v in metrics.get('operating_cf', [])]
    capex = [-abs(v / 1e7) for v in metrics.get('capex', [])]
    fcf = [v / 1e7 for v in metrics.get('free_cash_flow', [])]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=ocf, name='Operating CF',
        marker_color=COLORS['blue'], opacity=0.85, marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        x=years, y=capex, name='Capex',
        marker_color=COLORS['red'], opacity=0.85, marker_line_width=0,
    ))
    fig.add_trace(go.Scatter(
        x=years, y=fcf, name='Free Cash Flow',
        mode='lines+markers',
        line=dict(color=COLORS['gold'], width=2),
        marker=dict(size=7, color=COLORS['gold']),
    ))

    layout = dict(**BASE_LAYOUT)
    layout.update(
        title=dict(text='Cash Flow Analysis (₹ Cr)', font=dict(color=COLORS['text'], size=14), x=0.02),
        barmode='group',
        yaxis=dict(**BASE_LAYOUT['yaxis'], title='₹ Crores'),
        height=300,
    )
    fig.update_layout(**layout)
    return fig


def price_chart(history, info: Dict) -> go.Figure:
    """52-week price chart with volume."""
    if history is None or history.empty:
        return go.Figure()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.03)

    # Candlestick
    if all(col in history.columns for col in ['Open', 'High', 'Low', 'Close']):
        fig.add_trace(go.Candlestick(
            x=history.index,
            open=history['Open'],
            high=history['High'],
            low=history['Low'],
            close=history['Close'],
            name='Price',
            increasing_line_color=COLORS['green'],
            decreasing_line_color=COLORS['red'],
            increasing_fillcolor=COLORS['green'],
            decreasing_fillcolor=COLORS['red'],
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=history.index, y=history['Close'],
            line=dict(color=COLORS['gold'], width=1.5),
            name='Price',
        ), row=1, col=1)

    # Volume
    if 'Volume' in history.columns:
        fig.add_trace(go.Bar(
            x=history.index, y=history['Volume'],
            name='Volume',
            marker_color=COLORS['blue'],
            opacity=0.5,
            marker_line_width=0,
        ), row=2, col=1)

    for row in [1, 2]:
        fig.update_xaxes(gridcolor=COLORS['grid'], row=row, col=1)
        fig.update_yaxes(gridcolor=COLORS['grid'], row=row, col=1,
                         tickfont=dict(color=COLORS['text_muted']))

    fig.update_layout(
        paper_bgcolor=COLORS['bg'],
        plot_bgcolor=COLORS['card'],
        font=dict(family="Inter, Arial", color=COLORS['text']),
        margin=dict(l=50, r=30, t=50, b=30),
        title=dict(text='Price & Volume (2Y)', font=dict(color=COLORS['text'], size=14), x=0.02),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        height=380,
        hoverlabel=dict(bgcolor=COLORS['card'], font=dict(color=COLORS['text'])),
    )
    return fig


def dcf_projection_chart(dcf_result: Dict) -> go.Figure:
    """DCF Revenue & FCFF projection chart."""
    years = dcf_result.get('years', [])
    revenues = [r / 1e7 for r in dcf_result.get('revenues', [])]
    fcffs = [f / 1e7 for f in dcf_result.get('fcffs', [])]
    pv_fcffs = [p / 1e7 for p in dcf_result.get('pv_fcffs', [])]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=years, y=revenues, name='Projected Revenue',
        marker_color=COLORS['blue'], opacity=0.7, marker_line_width=0,
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=years, y=fcffs, name='FCFF',
        mode='lines+markers',
        line=dict(color=COLORS['gold'], width=2),
        marker=dict(size=6),
    ), secondary_y=True)

    fig.add_trace(go.Scatter(
        x=years, y=pv_fcffs, name='PV of FCFF',
        mode='lines+markers',
        line=dict(color=COLORS['green'], width=2, dash='dot'),
        marker=dict(size=6),
    ), secondary_y=True)

    fig.update_layout(
        **{**BASE_LAYOUT,
           'title': dict(text='DCF Projections (₹ Cr)', font=dict(color=COLORS['text'], size=14), x=0.02),
           'height': 320,
           'barmode': 'group',
           'yaxis': dict(**BASE_LAYOUT['yaxis'], title='Revenue (₹ Cr)'),
           }
    )
    return fig


def valuation_waterfall(dcf_result: Dict) -> go.Figure:
    """Valuation bridge: EV → Net Debt → Equity Value."""
    pv_explicit = dcf_result.get('sum_pv_fcffs', 0) / 1e7
    pv_tv = dcf_result.get('pv_terminal', 0) / 1e7
    ev = dcf_result.get('enterprise_value', 0) / 1e7
    net_debt = dcf_result.get('net_debt', 0) / 1e7
    eq_val = dcf_result.get('equity_value', 0) / 1e7

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "total", "relative", "total"],
        x=["PV Explicit FCFFs", "PV Terminal Value", "Enterprise Value", "Less: Net Debt", "Equity Value"],
        y=[pv_explicit, pv_tv, 0, -net_debt, 0],
        connector=dict(line=dict(color=COLORS['grid'], width=1)),
        increasing=dict(marker=dict(color=COLORS['green'])),
        decreasing=dict(marker=dict(color=COLORS['red'])),
        totals=dict(marker=dict(color=COLORS['gold'])),
        text=[f"₹{pv_explicit:,.0f}", f"₹{pv_tv:,.0f}", f"₹{ev:,.0f}", f"-₹{net_debt:,.0f}", f"₹{eq_val:,.0f}"],
        textposition="outside",
        textfont=dict(color=COLORS['text'], size=11),
    ))

    layout = dict(**BASE_LAYOUT)
    layout.update(
        title=dict(text='Valuation Bridge (₹ Cr)', font=dict(color=COLORS['text'], size=14), x=0.02),
        showlegend=False,
        height=340,
        yaxis=dict(**BASE_LAYOUT['yaxis'], title='₹ Crores'),
    )
    fig.update_layout(**layout)
    return fig


def sensitivity_heatmap(sensitivity_df: pd.DataFrame) -> go.Figure:
    """WACC vs TGR sensitivity heatmap."""
    z = sensitivity_df.values.tolist()
    x = list(sensitivity_df.columns)
    y = list(sensitivity_df.index)

    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y,
        colorscale=[
            [0.0, '#EF4444'],
            [0.25, '#F97316'],
            [0.5, COLORS['gold']],
            [0.75, '#22C55E'],
            [1.0, '#10B981'],
        ],
        showscale=True,
        text=[[f"₹{v:,.0f}" if v else 'N/A' for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=10, color='white'),
        hoverongaps=False,
    ))

    layout = dict(**BASE_LAYOUT)
    layout.update(
        title=dict(text='Sensitivity: Equity Value (₹ Cr) | TGR vs WACC', font=dict(color=COLORS['text'], size=13), x=0.02),
        xaxis=dict(**BASE_LAYOUT['xaxis'], title='WACC'),
        yaxis=dict(**BASE_LAYOUT['yaxis'], title='Terminal Growth Rate'),
        height=300,
    )
    fig.update_layout(**layout)
    return fig


def peer_multiples_chart(peer_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of peer EV/EBITDA multiples."""
    if peer_df is None or peer_df.empty:
        return go.Figure()

    df = peer_df.dropna(subset=['EV/EBITDA (x)'])
    if df.empty:
        return go.Figure()

    df = df.sort_values('EV/EBITDA (x)')

    colors = [COLORS['gold'] if i == len(df) - 1 else COLORS['blue'] for i in range(len(df))]

    fig = go.Figure(go.Bar(
        x=df['EV/EBITDA (x)'],
        y=df['Company'],
        orientation='h',
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:.1f}x" for v in df['EV/EBITDA (x)']],
        textposition='outside',
        textfont=dict(color=COLORS['text'], size=11),
    ))

    layout = dict(**BASE_LAYOUT)
    layout.update(
        title=dict(text='EV/EBITDA Peer Comparison', font=dict(color=COLORS['text'], size=14), x=0.02),
        xaxis=dict(**BASE_LAYOUT['xaxis'], title='EV/EBITDA (x)', ticksuffix='x'),
        yaxis=dict(**BASE_LAYOUT['yaxis'], title=''),
        height=max(250, len(df) * 45),
        margin=dict(l=140, r=60, t=50, b=40),
        showlegend=False,
    )
    fig.update_layout(**layout)
    return fig
