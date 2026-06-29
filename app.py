"""
AI-Assisted Equity Research Platform
=====================================
Production-ready institutional equity research tool.
Supports NSE / BSE / US tickers.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import time
import traceback
import datetime

st.set_page_config(
    page_title="Aryan's Equity Research Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-Assisted Equity Research Platform | Educational Use Only"
    }
)

sys.path.insert(0, os.path.dirname(__file__))

from utils.data_fetcher import (
    resolve_ticker, fetch_company_data, extract_financials,
    calculate_ratios, get_peer_tickers, fetch_peer_data
)
from modules.dcf_engine import estimate_wacc, project_fcff, sensitivity_analysis, valuation_bridge
from modules.charts import (
    revenue_chart, margin_chart, returns_chart, fcf_chart,
    price_chart, dcf_projection_chart, valuation_waterfall,
    sensitivity_heatmap, peer_multiples_chart
)
from modules.ai_research import get_client, build_context, run_ai_analysis, generate_investment_memo
from modules.pdf_generator import generate_pdf_report


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: #0a0e1a;
        color: #f0f4ff;
    }

    .main .block-container {
        background: #0a0e1a;
        padding: 1.5rem 2rem;
        max-width: 1400px;
    }

    /* ── SIDEBAR: always open, collapse button hidden ── */
    [data-testid="stSidebar"] {
        background: #0c1020 !important;
        border-right: 1px solid #1e2d4a;
        min-width: 280px !important;
        max-width: 280px !important;
        width: 280px !important;
        transform: translateX(0) !important;
        visibility: visible !important;
        display: block !important;
    }
    [data-testid="stSidebar"] .block-container {
        background: #0c1020 !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }
    button[kind="header"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] > div:first-child > div:first-child button {
        display: none !important;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    [data-testid="stMetric"] {
        background: #131c32;
        border: 1px solid #1e2d4a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
    }
    [data-testid="stMetricLabel"] {
        color: #8b9cb8 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 500;
    }
    [data-testid="stMetricValue"] {
        color: #f0f4ff !important;
        font-size: 1.4rem !important;
        font-weight: 600;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.78rem !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #0c1020;
        border-bottom: 1px solid #1e2d4a;
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8b9cb8 !important;
        background: transparent !important;
        border-bottom: 2px solid transparent !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .stTabs [aria-selected="true"] {
        color: #c9a84c !important;
        border-bottom: 2px solid #c9a84c !important;
        background: transparent !important;
    }

    .stButton > button {
        background: #c9a84c;
        color: #0a0e1a;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
        padding: 0.6rem 1.5rem;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: #e8c87a;
        color: #0a0e1a;
    }

    [data-testid="stDownloadButton"] > button {
        background: #131c32;
        color: #c9a84c;
        border: 1px solid #c9a84c;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: #c9a84c;
        color: #0a0e1a;
    }

    .stSlider [data-baseweb="slider"] { padding-top: 0.5rem; }

    .stSelectbox [data-baseweb="select"] {
        background: #131c32;
        border: 1px solid #1e2d4a;
        border-radius: 6px;
    }

    .stTextInput > div > div > input {
        background: #131c32;
        border: 1px solid #1e2d4a;
        color: #f0f4ff;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: #c9a84c;
        box-shadow: 0 0 0 1px #c9a84c20;
    }

    .stDataFrame { border: 1px solid #1e2d4a; border-radius: 8px; overflow: hidden; }
    .stDataFrame table { background: #0f1629; color: #f0f4ff; }
    .stDataFrame thead th {
        background: #0f1629 !important;
        color: #c9a84c !important;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        border-bottom: 1px solid #1e2d4a;
        font-weight: 600;
    }
    .stDataFrame tbody tr:nth-of-type(even) { background: #131c32 !important; }

    .streamlit-expanderHeader {
        background: #131c32;
        border: 1px solid #1e2d4a;
        border-radius: 6px;
        color: #8b9cb8 !important;
        font-size: 0.82rem !important;
    }

    .stAlert { border-radius: 6px; font-size: 0.83rem; }
    hr { border-color: #1e2d4a; }

    .er-card {
        background: #131c32;
        border: 1px solid #1e2d4a;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .er-card-title {
        font-size: 0.72rem; color: #8b9cb8;
        text-transform: uppercase; letter-spacing: 0.1em;
        font-weight: 600; margin-bottom: 0.4rem;
    }
    .er-kpi-val { font-size: 1.6rem; font-weight: 700; color: #f0f4ff; line-height: 1.1; }
    .er-kpi-sub { font-size: 0.78rem; color: #8b9cb8; margin-top: 0.2rem; }
    .er-section-header {
        font-size: 0.7rem; color: #c9a84c;
        text-transform: uppercase; letter-spacing: 0.15em;
        font-weight: 700; padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e2d4a; margin-bottom: 1rem;
    }
    .er-badge-buy {
        display: inline-block; background: #10b981; color: white;
        padding: 0.25rem 0.75rem; border-radius: 4px;
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;
    }
    .er-badge-hold {
        display: inline-block; background: #c9a84c; color: #0a0e1a;
        padding: 0.25rem 0.75rem; border-radius: 4px;
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;
    }
    .er-badge-sell {
        display: inline-block; background: #ef4444; color: white;
        padding: 0.25rem 0.75rem; border-radius: 4px;
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;
    }
    .er-disclaimer {
        background: #0c1020; border: 1px solid #1e2d4a;
        border-radius: 6px; padding: 0.6rem 1rem;
        font-size: 0.72rem; color: #4a5568; margin-top: 1rem;
    }
    .er-ai-label {
        display: inline-block; background: #2563eb20; color: #60a5fa;
        border: 1px solid #2563eb40; padding: 0.1rem 0.5rem;
        border-radius: 3px; font-size: 0.68rem; font-weight: 600;
        letter-spacing: 0.06em; margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)


def fmt_inr(val, divisor=1e7, decimals=0, suffix=' Cr'):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 'N/A'
    try:
        return f"₹{float(val)/divisor:,.{decimals}f}{suffix}"
    except Exception:
        return 'N/A'

def fmt_pct(val, decimals=1):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 'N/A'
    try:
        return f"{float(val):+.{decimals}f}%"
    except Exception:
        return 'N/A'

def fmt_num(val, suffix='', prefix='', decimals=1):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 'N/A'
    try:
        return f"{prefix}{float(val):,.{decimals}f}{suffix}"
    except Exception:
        return 'N/A'

def delta_color(val):
    if val and val > 0:
        return "normal"
    elif val and val < 0:
        return "inverse"
    return "off"


def init_state():
    defaults = {
        'data': None, 'metrics': None, 'ratios': None,
        'wacc_data': None, 'dcf_result': None, 'peer_df': None,
        'ticker_symbol': None, 'company_name': '', 'memo_text': '',
        'recommendation': 'HOLD', 'analysis_done': False,
        'last_ticker': '', 'ai_sections': {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="font-size:1.1rem; font-weight:700; color:#f0f4ff; letter-spacing:-0.02em;">
                📊 Aryan's Equity Research
            </div>
            <div style="font-size:0.72rem; color:#c9a84c; margin-top:0.2rem; font-weight:600;">
                AI-ASSISTED PLATFORM
            </div>
        </div>
        <hr style="border-color:#1e2d4a; margin:0.5rem 0 1rem 0;">
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.72rem; color:#8b9cb8; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">Company Search</div>', unsafe_allow_html=True)

        ticker_input = st.text_input(
            "Ticker / Company", value="TRENT",
            placeholder="e.g. TRENT, POLYCAB, DIXON...",
            label_visibility="collapsed", key="ticker_input_box"
        )

        col1, col2 = st.columns(2)
        with col1:
            exchange_hint = st.selectbox("Exchange", ["Auto", "NSE", "BSE", "US"], label_visibility="collapsed")
        with col2:
            analyze_btn = st.button("Analyse →", use_container_width=True)

        st.markdown('<div style="font-size:0.68rem; color:#4a5568; margin-top:0.8rem; margin-bottom:0.3rem;">QUICK PICKS</div>', unsafe_allow_html=True)
        quick_cols = st.columns(2)
        quick_tickers = ['TRENT', 'POLYCAB', 'DIXON', 'ICICIBANK', 'INFY', 'RELIANCE']
        for i, t in enumerate(quick_tickers):
            with quick_cols[i % 2]:
                if st.button(t, key=f"quick_{t}", use_container_width=True):
                    st.session_state['quick_pick'] = t
                    st.rerun()

        st.markdown('<hr style="border-color:#1e2d4a; margin:1rem 0;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem; color:#c9a84c; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">DCF Assumptions</div>', unsafe_allow_html=True)

        rev_growth = st.slider("Rev Growth Phase 1 (%)", 3.0, 40.0, 15.0, 0.5, key='rev_growth_s') / 100
        terminal_growth = st.slider("Terminal Growth Rate (%)", 2.0, 8.0, 5.0, 0.25, key='tgr_s') / 100
        forecast_years = st.slider("Forecast Years", 3, 10, 5, 1, key='fy_s')

        st.markdown('<hr style="border-color:#1e2d4a; margin:1rem 0;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem; color:#8b9cb8; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">AI Configuration</div>', unsafe_allow_html=True)

        api_key_input = st.text_input(
            "Anthropic API Key", type="password",
            placeholder="sk-ant-...", label_visibility="collapsed", key="api_key_input"
        )
        if api_key_input:
            os.environ['ANTHROPIC_API_KEY'] = api_key_input

        has_api_key = bool(os.environ.get('ANTHROPIC_API_KEY'))
        if has_api_key:
            st.markdown('<div style="font-size:0.72rem; color:#10b981;">✓ AI Engine Active</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:0.72rem; color:#4a5568;">○ AI Engine — Enter API key</div>', unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#1e2d4a; margin:1rem 0;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.68rem; color:#4a5568; line-height:1.5;">
        Data: Yahoo Finance (yfinance)<br>
        AI: Anthropic Claude<br>
        For educational use only.<br>
        Not investment advice.
        </div>
        """, unsafe_allow_html=True)

    return ticker_input, exchange_hint, analyze_btn, rev_growth, terminal_growth, forecast_years


def render_platform_header(info: dict):
    company_name = info.get('longName', info.get('shortName', '—'))
    ticker = info.get('symbol', '')
    sector = info.get('sector', '')
    industry = info.get('industry', '')
    price = info.get('currentPrice') or info.get('regularMarketPrice')
    prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
    change_pct = ((price - prev_close) / prev_close * 100) if price and prev_close and prev_close > 0 else None
    price_color = '#10b981' if (change_pct or 0) >= 0 else '#ef4444'
    change_arrow = '▲' if (change_pct or 0) >= 0 else '▼'

    st.markdown(f"""
    <div style="padding: 1.2rem 0 1rem 0; border-bottom: 1px solid #1e2d4a; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
            <div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f0f4ff; letter-spacing: -0.02em; line-height: 1.1;">
                    {company_name}
                </div>
                <div style="font-size: 0.8rem; color: #8b9cb8; margin-top: 0.3rem;">
                    <span style="color:#c9a84c; font-weight:600;">{ticker}</span>
                    &nbsp;·&nbsp; {sector} &nbsp;·&nbsp; {industry}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #f0f4ff; line-height: 1.1;">
                    ₹{price:,.2f}
                </div>
                <div style="font-size: 0.82rem; color: {price_color}; margin-top: 0.2rem;">
                    {change_arrow} {abs(change_pct):.2f}% today
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_overview(info: dict, history):
    st.markdown('<div class="er-section-header">Company Overview</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    price = info.get('currentPrice') or info.get('regularMarketPrice')
    mktcap = info.get('marketCap')
    ev = info.get('enterpriseValue')
    w52h = info.get('fiftyTwoWeekHigh')
    w52l = info.get('fiftyTwoWeekLow')
    beta = info.get('beta')
    div_yield = info.get('dividendYield')
    pe = info.get('trailingPE')
    fpe = info.get('forwardPE')
    pb = info.get('priceToBook')
    ev_ebitda = info.get('enterpriseToEbitda')
    ev_rev = info.get('enterpriseToRevenue')

    with col1:
        st.metric("Market Cap", fmt_inr(mktcap), help="Market Capitalisation = Price × Shares Outstanding")
    with col2:
        st.metric("Enterprise Value", fmt_inr(ev), help="EV = Market Cap + Net Debt")
    with col3:
        st.metric("52W High", f"₹{w52h:,.2f}" if w52h else "N/A")
    with col4:
        st.metric("52W Low", f"₹{w52l:,.2f}" if w52l else "N/A")
    with col5:
        st.metric("Beta", fmt_num(beta, decimals=2), help="Sensitivity to market movements")
    with col6:
        st.metric("Div Yield", fmt_num(div_yield, suffix='%', decimals=2) if div_yield else "N/A")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="er-section-header">Valuation Multiples</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("P/E (TTM)", fmt_num(pe, suffix='x'), help="Price / Trailing 12M EPS")
    with c2:
        st.metric("P/E (Fwd)", fmt_num(fpe, suffix='x'), help="Price / Forward EPS estimate")
    with c3:
        st.metric("P/B", fmt_num(pb, suffix='x', decimals=2), help="Price / Book Value per share")
    with c4:
        st.metric("EV/EBITDA", fmt_num(ev_ebitda, suffix='x'), help="Enterprise Value / EBITDA")
    with c5:
        st.metric("EV/Revenue", fmt_num(ev_rev, suffix='x', decimals=2), help="Enterprise Value / Revenue")

    st.markdown("<br>", unsafe_allow_html=True)

    if history is not None and not history.empty:
        st.plotly_chart(price_chart(history, info), use_container_width=True, config={'displayModeBar': False})

    description = info.get('longBusinessSummary', '')
    if description:
        st.markdown('<div class="er-section-header">Business Description</div>', unsafe_allow_html=True)
        with st.expander("View Business Description", expanded=True):
            st.markdown(f'<div style="font-size:0.85rem; color:#c8d3e6; line-height:1.7;">{description}</div>', unsafe_allow_html=True)

    st.markdown('<div class="er-section-header">Company Details</div>', unsafe_allow_html=True)
    details = {
        'Full Name': info.get('longName', 'N/A'),
        'Ticker Symbol': info.get('symbol', 'N/A'),
        'Exchange': info.get('exchange', 'N/A'),
        'Country': info.get('country', 'N/A'),
        'Sector': info.get('sector', 'N/A'),
        'Industry': info.get('industry', 'N/A'),
        'Employees': f"{info.get('fullTimeEmployees', 0):,}" if info.get('fullTimeEmployees') else 'N/A',
        'Website': info.get('website', 'N/A'),
        'Headquarters': f"{info.get('city', '')}, {info.get('state', '')}, {info.get('country', '')}".strip(', '),
    }
    details_df = pd.DataFrame({'Field': details.keys(), 'Value': details.values()})
    st.dataframe(details_df, hide_index=True, use_container_width=True)


def render_financials(metrics: dict, ratios: dict, info: dict):
    st.markdown('<div class="er-section-header">Financial Performance Summary</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        rev = metrics.get('revenue', [])
        latest_rev = rev[-1] if rev else None
        st.metric("Revenue (LTM)", fmt_inr(latest_rev))
    with c2:
        st.metric("Revenue CAGR", fmt_num(ratios.get('revenue_cagr'), suffix='%'), help="Compound Annual Growth Rate")
    with c3:
        st.metric("EBITDA CAGR", fmt_num(ratios.get('ebitda_cagr'), suffix='%'))
    with c4:
        st.metric("EBITDA Margin", fmt_num(ratios.get('latest_ebitda_margin'), suffix='%'))
    with c5:
        st.metric("Net Margin", fmt_num(ratios.get('latest_net_margin'), suffix='%'))

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("ROE", fmt_num(ratios.get('latest_roe'), suffix='%'), help="Net Income / Equity")
    with c2:
        st.metric("ROCE", fmt_num(ratios.get('latest_roce'), suffix='%'), help="EBIT / Capital Employed")
    with c3:
        st.metric("ROA", fmt_num(ratios.get('latest_roa'), suffix='%'), help="EBIT / Total Assets")
    with c4:
        st.metric("D/E Ratio", fmt_num(ratios.get('latest_de'), decimals=2), help="Total Debt / Equity")
    with c5:
        net_debt = ratios.get('net_debt', [])
        latest_nd = net_debt[-1] if net_debt else None
        st.metric("Net Debt", fmt_inr(latest_nd))

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(revenue_chart(metrics), use_container_width=True, config={'displayModeBar': False})
    with col_r:
        st.plotly_chart(margin_chart(metrics, ratios), use_container_width=True, config={'displayModeBar': False})

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(returns_chart(ratios, metrics), use_container_width=True, config={'displayModeBar': False})
    with col_r:
        st.plotly_chart(fcf_chart(metrics), use_container_width=True, config={'displayModeBar': False})

    st.markdown('<div class="er-section-header">Historical Income Statement (₹ Crores)</div>', unsafe_allow_html=True)
    years = metrics.get('years', [])
    rev_list = [v/1e7 for v in metrics.get('revenue', [])]
    ebitda_list = [v/1e7 for v in metrics.get('ebitda', [])]
    ebit_list = [v/1e7 for v in metrics.get('ebit', [])]
    ni_list = [v/1e7 for v in metrics.get('net_income', [])]
    ocf_list = [v/1e7 for v in metrics.get('operating_cf', [])]
    fcf_list = [v/1e7 for v in metrics.get('free_cash_flow', [])]
    capex_list = [v/1e7 for v in metrics.get('capex', [])]

    table_data = {
        'Metric': ['Revenue', 'YoY Growth', 'EBITDA', 'EBITDA Margin', 'EBIT', 'EBIT Margin',
                   'Net Income', 'Net Margin', 'Operating CF', 'Capex', 'Free Cash Flow'],
    }

    for i, yr in enumerate(years):
        vals = []
        vals.append(f"₹{rev_list[i]:,.0f}" if i < len(rev_list) else 'N/A')
        if i > 0 and i < len(rev_list) and rev_list[i-1] and abs(rev_list[i-1]) > 0:
            g = (rev_list[i] - rev_list[i-1]) / abs(rev_list[i-1]) * 100
            vals.append(f"{g:+.1f}%")
        else:
            vals.append('—')
        vals.append(f"₹{ebitda_list[i]:,.0f}" if i < len(ebitda_list) else 'N/A')
        if i < len(rev_list) and rev_list[i] and rev_list[i] > 0:
            vals.append(f"{ebitda_list[i]/rev_list[i]*100:.1f}%")
        else:
            vals.append('N/A')
        vals.append(f"₹{ebit_list[i]:,.0f}" if i < len(ebit_list) else 'N/A')
        if i < len(rev_list) and rev_list[i] and rev_list[i] > 0:
            vals.append(f"{ebit_list[i]/rev_list[i]*100:.1f}%")
        else:
            vals.append('N/A')
        vals.append(f"₹{ni_list[i]:,.0f}" if i < len(ni_list) else 'N/A')
        if i < len(rev_list) and rev_list[i] and rev_list[i] > 0 and i < len(ni_list):
            vals.append(f"{ni_list[i]/rev_list[i]*100:.1f}%")
        else:
            vals.append('N/A')
        vals.append(f"₹{ocf_list[i]:,.0f}" if i < len(ocf_list) else 'N/A')
        vals.append(f"₹{capex_list[i]:,.0f}" if i < len(capex_list) else 'N/A')
        vals.append(f"₹{fcf_list[i]:,.0f}" if i < len(fcf_list) else 'N/A')
        table_data[yr] = vals

    fin_df = pd.DataFrame(table_data)
    st.dataframe(fin_df, hide_index=True, use_container_width=True)


def render_dcf(dcf_result: dict, wacc_data: dict, info: dict, metrics: dict):
    if not dcf_result or 'error' in dcf_result:
        st.error(f"DCF Error: {dcf_result.get('error', 'Unable to run DCF model. Insufficient financial data.')}")
        return

    st.markdown('<div class="er-section-header">DCF Valuation — FCFF Model</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    ev = dcf_result.get('enterprise_value', 0)
    eq_val = dcf_result.get('equity_value', 0)
    pv_tv = dcf_result.get('pv_terminal', 0)
    sum_pv = dcf_result.get('sum_pv_fcffs', 0)
    net_debt = dcf_result.get('net_debt', 0)

    with c1:
        st.metric("Enterprise Value (DCF)", fmt_inr(ev))
    with c2:
        st.metric("Equity Value (DCF)", fmt_inr(eq_val))
    with c3:
        st.metric("PV Explicit FCFFs", fmt_inr(sum_pv))
    with c4:
        st.metric("PV Terminal Value", fmt_inr(pv_tv))
    with c5:
        tv_pct = pv_tv / ev * 100 if ev > 0 else 0
        st.metric("Terminal Value %", f"{tv_pct:.1f}%", help="% of EV from terminal value (typically 60-80%)")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="er-section-header">WACC Assumptions</div>', unsafe_allow_html=True)
    wc1, wc2, wc3, wc4, wc5, wc6 = st.columns(6)
    with wc1:
        st.metric("WACC", f"{wacc_data.get('wacc', 0)*100:.2f}%")
    with wc2:
        st.metric("Cost of Equity (Ke)", f"{wacc_data.get('ke', 0)*100:.2f}%", help="Rf + Beta × ERP (CAPM)")
    with wc3:
        st.metric("Cost of Debt (Kd)", f"{wacc_data.get('kd', 0)*100:.2f}%")
    with wc4:
        st.metric("Beta", f"{wacc_data.get('beta', 0):.2f}")
    with wc5:
        st.metric("Tax Rate", f"{wacc_data.get('tax_rate', 0)*100:.1f}%")
    with wc6:
        st.metric("Terminal Growth", f"{dcf_result.get('terminal_growth', 0)*100:.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(dcf_projection_chart(dcf_result), use_container_width=True, config={'displayModeBar': False})
    with col_r:
        st.plotly_chart(valuation_waterfall(dcf_result), use_container_width=True, config={'displayModeBar': False})

    st.markdown('<div class="er-section-header">DCF Projection Detail (₹ Crores)</div>', unsafe_allow_html=True)
    proj_data = {
        'Year': dcf_result['years'],
        'Revenue': [f"₹{v/1e7:,.0f}" for v in dcf_result['revenues']],
        'EBITDA': [f"₹{v/1e7:,.0f}" for v in dcf_result['ebitdas']],
        'EBITDA Mg': [f"{e/r*100:.1f}%" if r > 0 else 'N/A' for e, r in zip(dcf_result['ebitdas'], dcf_result['revenues'])],
        'EBIT': [f"₹{v/1e7:,.0f}" for v in dcf_result['ebits']],
        'NOPAT': [f"₹{v/1e7:,.0f}" for v in dcf_result['nopats']],
        'D&A': [f"₹{v/1e7:,.0f}" for v in dcf_result['das']],
        'Capex': [f"₹{v/1e7:,.0f}" for v in dcf_result['capexs']],
        'ΔWC': [f"₹{v/1e7:,.0f}" for v in dcf_result['delta_wcs']],
        'FCFF': [f"₹{v/1e7:,.0f}" for v in dcf_result['fcffs']],
        'PV(FCFF)': [f"₹{v/1e7:,.0f}" for v in dcf_result['pv_fcffs']],
        'Disc Factor': [f"{d:.4f}" for d in dcf_result['discount_factors']],
    }
    st.dataframe(pd.DataFrame(proj_data), hide_index=True, use_container_width=True)

    st.markdown('<div class="er-section-header" style="margin-top:1.5rem;">Sensitivity Analysis — Equity Value (₹ Cr) | WACC vs Terminal Growth Rate</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.75rem; color:#8b9cb8; margin-bottom:0.5rem;">Green = Higher equity value. Red = Lower equity value.</div>', unsafe_allow_html=True)
    try:
        sens_df = sensitivity_analysis(dcf_result, wacc_data)
        st.plotly_chart(sensitivity_heatmap(sens_df), use_container_width=True, config={'displayModeBar': False})
        with st.expander("View Sensitivity Table"):
            st.dataframe(sens_df, use_container_width=True)
    except Exception as e:
        st.warning(f"Sensitivity analysis could not be computed: {e}")


def render_peers(peer_df: pd.DataFrame, info: dict):
    st.markdown('<div class="er-section-header">Comparable Company Analysis</div>', unsafe_allow_html=True)

    if peer_df is None or peer_df.empty:
        st.warning("No peer data available. Peer comparison requires valid ticker data.")
        return

    pe_vals = peer_df['P/E (x)'].dropna()
    ev_vals = peer_df['EV/EBITDA (x)'].dropna()
    pb_vals = peer_df['P/B (x)'].dropna()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Peer Median P/E", f"{pe_vals.median():.1f}x" if len(pe_vals) > 0 else "N/A")
    with c2:
        st.metric("Peer Median EV/EBITDA", f"{ev_vals.median():.1f}x" if len(ev_vals) > 0 else "N/A")
    with c3:
        st.metric("Peer Median P/B", f"{pb_vals.median():.2f}x" if len(pb_vals) > 0 else "N/A")
    with c4:
        co_pe = info.get('trailingPE')
        peer_pe = pe_vals.median() if len(pe_vals) > 0 else None
        if co_pe and peer_pe and peer_pe > 0:
            prem = (co_pe - peer_pe) / peer_pe * 100
            st.metric("P/E Premium to Peers", f"{prem:+.1f}%", delta=f"{prem:+.1f}%")
        else:
            st.metric("P/E Premium to Peers", "N/A")

    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(peer_multiples_chart(peer_df), use_container_width=True, config={'displayModeBar': False})

    st.markdown('<div class="er-section-header">Peer Multiples Table</div>', unsafe_allow_html=True)
    display_df = peer_df.copy()
    for col in ['P/E (x)', 'P/B (x)', 'EV/EBITDA (x)', 'EV/Revenue (x)']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}x" if pd.notna(x) else 'N/A')
    if 'Mkt Cap (Cr)' in display_df.columns:
        display_df['Mkt Cap (Cr)'] = display_df['Mkt Cap (Cr)'].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else 'N/A')
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    st.markdown("""
    <div class="er-disclaimer">
    ⚠ Comparable company analysis is based on TTM multiples sourced from Yahoo Finance.
    Peer group is auto-selected based on sector/industry. Multiples are point-in-time.
    </div>
    """, unsafe_allow_html=True)


def render_ai_research(info: dict, metrics: dict, ratios: dict):
    st.markdown('<div class="er-ai-label">AI-ASSISTED ANALYSIS — ANTHROPIC CLAUDE</div>', unsafe_allow_html=True)
    st.markdown('<div class="er-section-header">AI Research Engine</div>', unsafe_allow_html=True)

    client = get_client()
    if client is None:
        st.warning("**AI Engine not active.** Enter your Anthropic API key in the sidebar.\n\nGet your key at: https://console.anthropic.com")
        return

    context = build_context(info, metrics, ratios)
    analysis_options = {
        'Business Model & Competitive Position': 'business_model',
        'Investment Thesis (Bull & Bear)': 'investment_thesis',
        'Key Risk Factors': 'risks',
        'Analyst Recommendation': 'recommendation',
    }

    col_l, col_r = st.columns([1, 3])
    with col_l:
        selected_analysis = st.radio("Select Analysis", list(analysis_options.keys()), label_visibility="collapsed")

    analysis_key = analysis_options[selected_analysis]

    with col_r:
        cache_key = f"ai_{analysis_key}_{info.get('symbol', '')}"
        if cache_key not in st.session_state['ai_sections']:
            if st.button(f"Generate: {selected_analysis}", key=f"gen_{analysis_key}"):
                with st.spinner("Generating AI analysis..."):
                    result = run_ai_analysis(context, analysis_key, client)
                    st.session_state['ai_sections'][cache_key] = result

        if cache_key in st.session_state['ai_sections']:
            result_text = st.session_state['ai_sections'][cache_key]
            st.markdown(f"""
            <div class="er-card">
                <div class="er-ai-label" style="margin-bottom:0.8rem;">AI OUTPUT — {selected_analysis.upper()}</div>
                <div style="font-size:0.86rem; color:#c8d3e6; line-height:1.75; white-space:pre-wrap;">{result_text}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:#4a5568; font-size:0.82rem; padding:1rem 0;">Click Generate to run: <strong>{selected_analysis}</strong></div>', unsafe_allow_html=True)

    st.markdown('<div class="er-disclaimer">⚠ AI-generated analysis is produced by Anthropic Claude based on available data only. Not investment advice.</div>', unsafe_allow_html=True)


def render_memo(info: dict, metrics: dict, ratios: dict, dcf_result: dict, peer_df: pd.DataFrame):
    st.markdown('<div class="er-ai-label">AI-ASSISTED ANALYSIS — ANTHROPIC CLAUDE</div>', unsafe_allow_html=True)
    st.markdown('<div class="er-section-header">Investment Memo Generator</div>', unsafe_allow_html=True)

    client = get_client()
    if client is None:
        st.warning("AI Engine not active. Enter your Anthropic API key in the sidebar.")
        return

    rec_options = ['BUY', 'ADD', 'HOLD', 'REDUCE', 'SELL']
    rec = st.selectbox("Select Rating", rec_options, index=2, key='rec_select')
    st.session_state['recommendation'] = rec

    if st.button("Generate Investment Memo", key='gen_memo'):
        with st.spinner("Generating institutional investment memo..."):
            memo = generate_investment_memo(info, metrics, ratios, dcf_result or {}, peer_df, client)
            st.session_state['memo_text'] = memo

    if st.session_state.get('memo_text'):
        memo_text = st.session_state['memo_text']
        rec_badge = {
            'BUY': '<span class="er-badge-buy">BUY</span>',
            'ADD': '<span class="er-badge-buy">ADD</span>',
            'HOLD': '<span class="er-badge-hold">HOLD</span>',
            'REDUCE': '<span class="er-badge-sell">REDUCE</span>',
            'SELL': '<span class="er-badge-sell">SELL</span>',
        }.get(rec, '')
        st.markdown(f"""
        <div class="er-card">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
                <div class="er-ai-label">INVESTMENT MEMO — AI ASSISTED</div>
                {rec_badge}
            </div>
            <div style="font-size:0.86rem; color:#c8d3e6; line-height:1.8; white-space:pre-wrap;">{memo_text}</div>
        </div>
        """, unsafe_allow_html=True)


def render_pdf_export(info: dict, metrics: dict, ratios: dict, dcf_result: dict, peer_df: pd.DataFrame):
    st.markdown('<div class="er-section-header">PDF Report Export</div>', unsafe_allow_html=True)

    company_name = info.get('longName', info.get('shortName', 'Company'))
    ticker = info.get('symbol', 'N/A')
    rec = st.session_state.get('recommendation', 'HOLD')
    memo_text = st.session_state.get('memo_text', '')

    st.markdown(f"""
    <div class="er-card">
        <div class="er-card-title">Report Preview</div>
        <div style="font-size:1rem; font-weight:600; color:#f0f4ff; margin-bottom:0.5rem;">
            {company_name} — Equity Research Report
        </div>
        <div style="font-size:0.8rem; color:#8b9cb8; line-height:1.8;">
            📄 Company Overview & Key Metrics<br>
            📊 Historical Financial Analysis<br>
            🔢 DCF Valuation Model (FCFF Approach)<br>
            🔍 Comparable Company Analysis<br>
            {"📝 AI Investment Memo<br>" if memo_text else "📝 Investment Memo (Generate in Memo tab first)<br>"}
            ⚠ Professional Disclaimers
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        rec_select = st.selectbox("Rating for Report", ['BUY', 'ADD', 'HOLD', 'REDUCE', 'SELL'],
                                   index=['BUY', 'ADD', 'HOLD', 'REDUCE', 'SELL'].index(rec), key='pdf_rec')

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Generate PDF Report", key='gen_pdf'):
        with st.spinner("Generating institutional PDF report..."):
            try:
                pdf_bytes = generate_pdf_report(
                    info=info, metrics=metrics, ratios=ratios,
                    dcf_result=dcf_result or {},
                    peer_df=peer_df if peer_df is not None else pd.DataFrame(),
                    memo_text=memo_text, recommendation=rec_select,
                )
                date_str = datetime.datetime.now().strftime("%Y%m%d")
                filename = f"EquityResearch_{ticker}_{date_str}.pdf"
                st.download_button(
                    label="⬇ Download PDF Report", data=pdf_bytes,
                    file_name=filename, mime="application/pdf", key='download_pdf'
                )
                st.success(f"✓ Report generated: {filename}")
            except Exception as e:
                st.error(f"PDF generation failed: {str(e)}")
                st.code(traceback.format_exc())


def run_analysis(ticker_input: str, exchange_hint: str, rev_growth: float,
                 terminal_growth: float, forecast_years: int):
    if 'quick_pick' in st.session_state:
        ticker_input = st.session_state.pop('quick_pick')

    if not ticker_input:
        return

    if exchange_hint == 'NSE':
        ticker_symbol = ticker_input.upper().replace('.NS', '') + '.NS'
    elif exchange_hint == 'BSE':
        ticker_symbol = ticker_input.upper().replace('.BO', '') + '.BO'
    else:
        ticker_symbol, _ = resolve_ticker(ticker_input)

    settings_key = f"{ticker_symbol}_{rev_growth}_{terminal_growth}_{forecast_years}"
    if (st.session_state.get('last_ticker') == settings_key and st.session_state.get('analysis_done')):
        return

    progress_container = st.empty()
    with progress_container.container():
        st.markdown(f'<div style="color:#c9a84c; font-size:0.85rem; margin-bottom:0.5rem;">Fetching data for <strong>{ticker_symbol}</strong>...</div>', unsafe_allow_html=True)
        prog = st.progress(0)

        prog.progress(10, text="Fetching market data...")
        data = fetch_company_data(ticker_symbol)

        if data['errors']:
            progress_container.empty()
            for err in data['errors']:
                st.error(f"Data Error: {err}")
            return

        prog.progress(30, text="Processing financial statements...")
        metrics = extract_financials(data)
        if metrics.get('errors'):
            for w in metrics['errors']:
                st.warning(f"Financial Data: {w}")

        prog.progress(50, text="Calculating financial ratios...")
        ratios = calculate_ratios(metrics, data['info'])

        prog.progress(65, text="Building DCF model...")
        wacc_data = estimate_wacc(data['info'], metrics)
        dcf_result = project_fcff(
            metrics, wacc_data,
            revenue_growth_phase1=rev_growth,
            terminal_growth=terminal_growth,
            forecast_years=forecast_years,
        )

        prog.progress(80, text="Fetching peer companies...")
        sector = data['info'].get('sector', '')
        industry = data['info'].get('industry', '')
        peer_tickers = get_peer_tickers(data['info'], sector, industry)
        peer_tickers = [p for p in peer_tickers if not p.startswith(ticker_input.upper().split('.')[0])]
        peer_df = fetch_peer_data(peer_tickers, data['info'])

        prog.progress(100, text="Analysis complete.")
        time.sleep(0.3)

    progress_container.empty()

    st.session_state['data'] = data
    st.session_state['metrics'] = metrics
    st.session_state['ratios'] = ratios
    st.session_state['wacc_data'] = wacc_data
    st.session_state['dcf_result'] = dcf_result
    st.session_state['peer_df'] = peer_df
    st.session_state['ticker_symbol'] = ticker_symbol
    st.session_state['company_name'] = data['info'].get('longName', ticker_symbol)
    st.session_state['analysis_done'] = True
    st.session_state['last_ticker'] = settings_key
    st.session_state['ai_sections'] = {}
    st.session_state['memo_text'] = ''


def main():
    inject_css()
    init_state()

    ticker_input, exchange_hint, analyze_btn, rev_growth, terminal_growth, forecast_years = render_sidebar()

    st.markdown("""
    <div style="display:flex; align-items:baseline; gap:0.75rem; padding: 0.5rem 0 0.5rem 0;">
        <span style="font-size:1.2rem; font-weight:700; color:#c9a84c; letter-spacing:-0.02em;">EQUITY RESEARCH</span>
        <span style="font-size:0.75rem; color:#4a5568; letter-spacing:0.12em; text-transform:uppercase;">AI-Assisted Platform</span>
    </div>
    <div style="height:1px; background: linear-gradient(90deg, #c9a84c33 0%, #1e2d4a 60%); margin-bottom:1.5rem;"></div>
    """, unsafe_allow_html=True)

    if 'quick_pick' in st.session_state:
        ticker_input = st.session_state['quick_pick']
        analyze_btn = True

    if analyze_btn or 'quick_pick' in st.session_state:
        run_analysis(ticker_input, exchange_hint, rev_growth, terminal_growth, forecast_years)

    if not st.session_state.get('analysis_done'):
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;
                    padding: 5rem 2rem; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">📊</div>
            <div style="font-size:1.4rem; font-weight:700; color:#f0f4ff; margin-bottom:0.5rem;">
                Aryan's AI Equity Research Platform
            </div>
            <div style="font-size:0.9rem; color:#8b9cb8; max-width:500px; line-height:1.7;">
                Enter a ticker symbol in the sidebar and click Analyse to generate
                a complete institutional-grade equity research report.
            </div>
            <div style="margin-top:2rem; font-size:0.8rem; color:#4a5568;">
                Supports NSE · BSE · US Tickers<br>
                Examples: TRENT · POLYCAB · DIXON · ICICIBANK · INFY
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    data = st.session_state['data']
    metrics = st.session_state['metrics']
    ratios = st.session_state['ratios']
    wacc_data = st.session_state['wacc_data']
    dcf_result = st.session_state['dcf_result']
    peer_df = st.session_state['peer_df']
    info = data['info']

    if data.get('warnings'):
        with st.expander("⚠ Data Warnings", expanded=False):
            for w in data['warnings']:
                st.warning(w)

    render_platform_header(info)

    tabs = st.tabs([
        "📋 Overview", "📈 Financials", "🔢 DCF Valuation",
        "🔍 Peers", "🤖 AI Research", "📝 Inv. Memo", "📥 PDF Export",
    ])

    with tabs[0]:
        render_overview(info, data.get('history'))
    with tabs[1]:
        render_financials(metrics, ratios, info)
    with tabs[2]:
        render_dcf(dcf_result, wacc_data, info, metrics)
    with tabs[3]:
        render_peers(peer_df, info)
    with tabs[4]:
        render_ai_research(info, metrics, ratios)
    with tabs[5]:
        render_memo(info, metrics, ratios, dcf_result, peer_df)
    with tabs[6]:
        render_pdf_export(info, metrics, ratios, dcf_result, peer_df)


if __name__ == "__main__":
    main()
