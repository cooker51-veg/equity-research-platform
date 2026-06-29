"""
AI Research Engine
Uses Anthropic Claude API for qualitative research assistance.
Strict instruction: Never fabricate financial data or events.
All AI output is clearly labeled as AI-assisted analysis.
"""

import anthropic
import json
from typing import Dict, Any, Optional
import os


def get_client() -> Optional[anthropic.Anthropic]:
    """Initialize Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


def build_context(info: Dict, metrics: Dict, ratios: Dict) -> str:
    """Build a structured financial context string for the AI prompt."""
    
    def fmt(val, suffix='', prefix='', decimals=1, divisor=1):
        if val is None:
            return 'N/A'
        try:
            return f"{prefix}{val/divisor:,.{decimals}f}{suffix}"
        except Exception:
            return 'N/A'

    rev = metrics.get('revenue', [])
    latest_rev = rev[-1] if rev else None
    years = metrics.get('years', [])

    context = f"""
COMPANY: {info.get('longName', 'N/A')} ({info.get('symbol', 'N/A')})
SECTOR: {info.get('sector', 'N/A')} | INDUSTRY: {info.get('industry', 'N/A')}
EXCHANGE: {info.get('exchange', 'N/A')} | COUNTRY: {info.get('country', 'N/A')}

MARKET DATA:
- Current Price: {fmt(info.get('currentPrice') or info.get('regularMarketPrice'), prefix='₹')}
- Market Cap: {fmt(info.get('marketCap'), prefix='₹', divisor=1e7, suffix=' Cr')}
- Enterprise Value: {fmt(info.get('enterpriseValue'), prefix='₹', divisor=1e7, suffix=' Cr')}
- 52W High: {fmt(info.get('fiftyTwoWeekHigh'), prefix='₹')}
- 52W Low: {fmt(info.get('fiftyTwoWeekLow'), prefix='₹')}
- Beta: {fmt(info.get('beta'), decimals=2)}

FINANCIAL PERFORMANCE (most recent year):
- Revenue: {fmt(latest_rev, prefix='₹', divisor=1e7, suffix=' Cr')}
- Revenue CAGR: {fmt(ratios.get('revenue_cagr'), suffix='%', decimals=1)}
- EBITDA Margin: {fmt(ratios.get('latest_ebitda_margin'), suffix='%', decimals=1)}
- EBIT Margin: {fmt(ratios.get('latest_ebit_margin'), suffix='%', decimals=1)}
- Net Margin: {fmt(ratios.get('latest_net_margin'), suffix='%', decimals=1)}
- ROE: {fmt(ratios.get('latest_roe'), suffix='%', decimals=1)}
- ROCE: {fmt(ratios.get('latest_roce'), suffix='%', decimals=1)}
- D/E Ratio: {fmt(ratios.get('latest_de'), decimals=2)}

VALUATION MULTIPLES:
- P/E: {fmt(info.get('trailingPE'), suffix='x', decimals=1)}
- P/B: {fmt(info.get('priceToBook'), suffix='x', decimals=2)}
- EV/EBITDA: {fmt(info.get('enterpriseToEbitda'), suffix='x', decimals=1)}
- EV/Revenue: {fmt(info.get('enterpriseToRevenue'), suffix='x', decimals=2)}

COMPANY DESCRIPTION: {(info.get('longBusinessSummary') or '')[:1000]}
"""
    return context.strip()


def run_ai_analysis(context: str, analysis_type: str, client: anthropic.Anthropic) -> str:
    """
    Run a specific AI analysis module.
    Returns structured text output.
    """
    
    prompts = {
        'business_model': f"""
You are a senior equity research analyst. Based on the following company data, provide a concise, professional analysis of the business model.

{context}

Structure your response as:
1. CORE BUSINESS MODEL (2-3 sentences describing how the company makes money)
2. REVENUE STREAMS (bullet points of key revenue sources)
3. COMPETITIVE ADVANTAGES (2-3 concrete moats or advantages)
4. INDUSTRY STRUCTURE (1-2 sentences on industry dynamics)

Be specific, factual, and professional. Do NOT fabricate specific numbers or events not present in the data.
If information is uncertain, say "Based on available data..." or "Industry context suggests..."
Maximum 300 words.
""",

        'investment_thesis': f"""
You are a senior equity research analyst at a top-tier institution. Based on the following company data, generate a structured investment thesis.

{context}

Structure your response as:
INVESTMENT THESIS
1-2 sentence summary thesis statement.

BULL CASE (3 specific catalysts or positive drivers):
• Point 1
• Point 2  
• Point 3

BEAR CASE (3 specific risks or headwinds):
• Point 1
• Point 2
• Point 3

KEY CATALYSTS TO WATCH:
• Near-term (0-6 months)
• Medium-term (6-18 months)

Be specific and analytical. Ground all points in the provided data.
Do NOT invent company events, deals, or specific forward numbers.
If uncertain, qualify with "could", "may", "if management executes".
Maximum 350 words.
""",

        'risks': f"""
You are a risk analyst covering this company. Identify and explain the key investment risks.

{context}

Provide exactly 6 risks, formatted as:
RISK 1 — [RISK NAME] | Severity: High/Medium/Low
[1-2 sentence explanation of the risk and its potential impact]

RISK 2 — [RISK NAME] | Severity: High/Medium/Low
...

Cover a mix of: business risk, financial risk, regulatory risk, competitive risk, macro risk, and execution risk.
Be specific to this company's sector and profile.
Do NOT fabricate specific events or regulatory changes not in the data.
""",

        'recommendation': f"""
You are writing the concluding section of an institutional equity research report.

{context}

Write a professional investment recommendation containing:

RECOMMENDATION: [BUY / ADD / HOLD / REDUCE / SELL]
(Base this on valuation multiples relative to growth, margin quality, and risk profile)

INVESTMENT CONCLUSION (2-3 professional sentences summarizing the key investment case)

VALUATION BASIS (1-2 sentences explaining the valuation methodology basis)

KEY MONITORABLES (3 bullet points — what to watch that could change the thesis):
• 
• 
•

RISKS TO TARGET (1-2 sentences on what could impair the thesis)

Write in the style of Goldman Sachs or Morgan Stanley equity research.
Be direct, analytical, and qualified appropriately.
Do NOT invent specific price targets or EPS numbers unless they exist in the data.
"""
    }

    prompt = prompts.get(analysis_type, '')
    if not prompt:
        return "Analysis type not found."

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"AI analysis unavailable: {str(e)}\n\nNote: Ensure ANTHROPIC_API_KEY is set in your environment."


def generate_investment_memo(
    info: Dict,
    metrics: Dict,
    ratios: Dict,
    dcf_result: Dict,
    peer_df,
    client: anthropic.Anthropic
) -> str:
    """
    Generate a complete investment memo using AI.
    Structured like institutional equity research.
    """
    
    def fmt(val, suffix='', prefix='', decimals=1, divisor=1):
        if val is None:
            return 'N/A'
        try:
            return f"{prefix}{val/divisor:,.{decimals}f}{suffix}"
        except Exception:
            return 'N/A'

    rev = metrics.get('revenue', [])
    years = metrics.get('years', [])
    latest_rev = rev[-1] if rev else 0

    ev = dcf_result.get('enterprise_value', 0)
    equity_val = dcf_result.get('equity_value', 0)

    peer_summary = ""
    if peer_df is not None and not peer_df.empty:
        peer_summary = peer_df.to_string(index=False)

    context = build_context(info, metrics, ratios)

    memo_prompt = f"""
You are a Managing Director of Equity Research at a bulge bracket investment bank.
Write a complete, institutional-quality investment research memo for this company.

COMPANY DATA:
{context}

DCF VALUATION OUTPUT:
- DCF Enterprise Value: {fmt(ev, prefix='₹', divisor=1e7, suffix=' Cr')}
- DCF Equity Value: {fmt(equity_val, prefix='₹', divisor=1e7, suffix=' Cr')}
- WACC Used: {fmt(dcf_result.get('wacc', 0)*100, suffix='%', decimals=1)}
- Terminal Growth: {fmt(dcf_result.get('terminal_growth', 0)*100, suffix='%', decimals=1)}
- Forecast Revenue Growth (Stage 1): {fmt(dcf_result.get('revenue_growth_phase1', 0)*100, suffix='%', decimals=1)}

PEER COMPARABLES:
{peer_summary}

Write the memo with these sections:
---
EQUITY RESEARCH | [COMPANY NAME] | [SECTOR]
RECOMMENDATION: [BUY/ADD/HOLD/REDUCE/SELL] | RATING INITIATION

EXECUTIVE SUMMARY
[2-3 sentence thesis]

BUSINESS OVERVIEW
[2-3 paragraphs covering business model, revenue streams, competitive positioning]

FINANCIAL ANALYSIS
[2 paragraphs covering revenue trajectory, margin profile, return ratios, balance sheet strength]

VALUATION
[2 paragraphs covering DCF methodology, peer multiples, implied upside/downside]

INVESTMENT THESIS
[Bull case and bear case with 3 points each]

KEY RISKS
[4-5 specific risks]

CATALYSTS
[3-4 near and medium term catalysts]

INVESTMENT CONCLUSION
[1 paragraph - direct, professional closing statement]
---

IMPORTANT RULES:
- Write like Goldman Sachs or Morgan Stanley research
- Ground all statements in the provided data
- Do NOT fabricate specific earnings events, deals, or announcements
- Qualify uncertain statements appropriately
- Be analytical and specific, not generic
- Total length: 600-800 words
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": memo_prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Investment memo generation failed: {str(e)}"
