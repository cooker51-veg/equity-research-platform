"""
DCF Valuation Engine
Follows CFA/FMVA methodology for free cash flow to firm (FCFF) valuation.
All formulas are standard corporate finance practice.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
import warnings
warnings.filterwarnings('ignore')


def estimate_wacc(info: Dict, metrics: Dict, rf_rate: float = 0.072) -> Dict[str, float]:
    """
    Estimate WACC using CAPM for cost of equity.
    
    WACC = (E/V) * Ke + (D/V) * Kd * (1 - t)
    Ke = Rf + Beta * (Rm - Rf)  [CAPM]
    
    For Indian markets:
    - Rf: 10Y G-Sec yield (~7.2%)
    - ERP: India Equity Risk Premium (~5.5-6.5%)
    - Default spread added if leverage is high
    """
    # Market parameters (India defaults)
    equity_risk_premium = 0.060  # 6.0% for India
    
    # Beta
    beta = info.get('beta')
    if beta is None or beta <= 0 or beta > 5:
        beta = 1.0  # Market beta as fallback
    beta = max(0.5, min(beta, 2.5))  # Bound between 0.5 and 2.5

    # Cost of Equity (CAPM)
    ke = rf_rate + beta * equity_risk_premium

    # Debt & Equity weights
    market_cap = info.get('marketCap', 0) or 0
    total_debt = metrics.get('total_debt', [0])
    latest_debt = total_debt[-1] if total_debt else 0
    latest_cash = (metrics.get('cash', [0]) or [0])[-1]
    net_debt = max(0, latest_debt - latest_cash)

    total_capital = market_cap + net_debt
    if total_capital <= 0:
        total_capital = market_cap if market_cap > 0 else 1

    weight_equity = market_cap / total_capital
    weight_debt = net_debt / total_capital

    # Cost of Debt
    int_exp_list = metrics.get('interest_expense', [0])
    avg_debt = np.mean(metrics.get('total_debt', [1])) if metrics.get('total_debt') else latest_debt
    
    if int_exp_list and avg_debt and avg_debt > 0:
        kd_raw = np.mean([i for i in int_exp_list if i and i > 0]) / max(avg_debt, 1)
        kd = max(0.04, min(kd_raw, 0.18))  # Bound 4-18%
    else:
        kd = 0.09  # Default 9% for India

    # Effective tax rate
    ebit_list = metrics.get('ebit', [])
    tax_list = metrics.get('tax_expense', [])
    
    if ebit_list and tax_list:
        valid_tax_rates = []
        for e, t in zip(ebit_list, tax_list):
            if e and e > 0 and t and t > 0:
                valid_tax_rates.append(t / e)
        tax_rate = np.median(valid_tax_rates) if valid_tax_rates else 0.25
    else:
        tax_rate = 0.25  # India statutory ~25%
    
    tax_rate = max(0.15, min(tax_rate, 0.40))

    # WACC
    wacc = (weight_equity * ke) + (weight_debt * kd * (1 - tax_rate))
    wacc = max(0.08, min(wacc, 0.25))  # Sanity bounds 8-25%

    return {
        'rf_rate': rf_rate,
        'beta': beta,
        'erp': equity_risk_premium,
        'ke': ke,
        'kd': kd,
        'tax_rate': tax_rate,
        'weight_equity': weight_equity,
        'weight_debt': weight_debt,
        'wacc': wacc,
        'net_debt': net_debt,
        'market_cap': market_cap,
    }


def project_fcff(
    metrics: Dict,
    wacc_data: Dict,
    revenue_growth_phase1: float = 0.15,
    revenue_growth_phase2: float = 0.10,
    terminal_growth: float = 0.05,
    ebitda_margin_target: float = None,
    capex_pct_revenue: float = None,
    wc_pct_revenue: float = 0.05,
    forecast_years: int = 5,
    phase2_years: int = 3,
) -> Dict[str, Any]:
    """
    3-Stage DCF Model:
    Stage 1: High growth (years 1-5)
    Stage 2: Transition growth (years 6-8)
    Stage 3: Terminal value (Gordon Growth Model)
    
    FCFF = EBIT * (1-t) + D&A - Capex - Change in Working Capital
    Terminal Value = FCFFn+1 / (WACC - g)
    """
    rev = metrics.get('revenue', [])
    ebitda = metrics.get('ebitda', [])
    ebit = metrics.get('ebit', [])
    da = metrics.get('depreciation', [])
    capex_hist = metrics.get('capex', [])
    ocf = metrics.get('operating_cf', [])

    if not rev or not any(r > 0 for r in rev if r):
        return {'error': 'Insufficient revenue data for DCF projection'}

    # Base values (use most recent non-zero)
    def get_latest(lst):
        for v in reversed(lst):
            if v and abs(v) > 0:
                return v
        return 0

    base_revenue = get_latest(rev)
    base_ebitda = get_latest(ebitda)
    base_da = get_latest(da)

    tax_rate = wacc_data.get('tax_rate', 0.25)
    wacc = wacc_data.get('wacc', 0.12)

    # Derive margin targets from historical average if not provided
    valid_ebitda_margins = []
    for r, e in zip(rev, ebitda):
        if r and r > 0 and e is not None:
            valid_ebitda_margins.append(e / r)

    if ebitda_margin_target is None:
        if valid_ebitda_margins:
            # Use average of last 3 years, slight improvement assumption
            ebitda_margin_target = np.mean(valid_ebitda_margins[-3:]) * 1.02
        else:
            ebitda_margin_target = 0.15

    ebitda_margin_target = max(0.05, min(ebitda_margin_target, 0.55))

    # Capex as % of revenue
    valid_capex_pcts = []
    for r, c in zip(rev, capex_hist):
        if r and r > 0 and c and c > 0:
            valid_capex_pcts.append(c / r)

    if capex_pct_revenue is None:
        capex_pct_revenue = np.mean(valid_capex_pcts) if valid_capex_pcts else 0.05
    capex_pct_revenue = max(0.02, min(capex_pct_revenue, 0.25))

    # D&A as % of revenue
    da_pct = (base_da / base_revenue) if base_revenue > 0 else 0.04
    da_pct = max(0.01, min(da_pct, 0.15))

    # Projection
    years = []
    revenues = []
    ebitdas = []
    ebits = []
    nopats = []  # EBIT * (1-t)
    das = []
    capexs = []
    delta_wcs = []
    fcffs = []

    current_revenue = base_revenue
    prev_revenue = rev[-2] if len(rev) >= 2 else base_revenue * 0.85

    total_years = forecast_years + phase2_years

    for i in range(1, total_years + 1):
        if i <= forecast_years:
            g = revenue_growth_phase1
        else:
            # Linear interpolation from phase1 to terminal in phase2
            steps = phase2_years
            step = i - forecast_years
            g = revenue_growth_phase1 + (terminal_growth - revenue_growth_phase1) * (step / steps)

        # Revenue
        projected_revenue = current_revenue * (1 + g)
        # EBITDA
        projected_ebitda = projected_revenue * ebitda_margin_target
        # D&A
        projected_da = projected_revenue * da_pct
        # EBIT
        projected_ebit = projected_ebitda - projected_da
        # NOPAT
        projected_nopat = projected_ebit * (1 - tax_rate)
        # Capex
        projected_capex = projected_revenue * capex_pct_revenue
        # Change in Working Capital
        projected_delta_wc = (projected_revenue - current_revenue) * wc_pct_revenue

        # FCFF = NOPAT + D&A - Capex - Delta WC
        projected_fcff = projected_nopat + projected_da - projected_capex - projected_delta_wc

        years.append(f"Y{i}E")
        revenues.append(projected_revenue)
        ebitdas.append(projected_ebitda)
        ebits.append(projected_ebit)
        nopats.append(projected_nopat)
        das.append(projected_da)
        capexs.append(projected_capex)
        delta_wcs.append(projected_delta_wc)
        fcffs.append(projected_fcff)

        prev_revenue = current_revenue
        current_revenue = projected_revenue

    # Terminal Value (Gordon Growth Model)
    terminal_fcff = fcffs[-1] * (1 + terminal_growth)
    if wacc <= terminal_growth:
        wacc = terminal_growth + 0.03  # Safety guard
    terminal_value = terminal_fcff / (wacc - terminal_growth)

    # Discount factors
    discount_factors = [(1 / (1 + wacc) ** i) for i in range(1, total_years + 1)]

    # PV of FCFFs
    pv_fcffs = [f * d for f, d in zip(fcffs, discount_factors)]

    # PV of Terminal Value (discount at end of projection period)
    pv_terminal = terminal_value * discount_factors[-1]

    # Enterprise Value
    enterprise_value = sum(pv_fcffs) + pv_terminal

    # Equity Value
    net_debt = wacc_data.get('net_debt', 0)
    equity_value = enterprise_value - net_debt

    # Intrinsic value per share
    shares = None
    for key in ['sharesOutstanding', 'impliedSharesOutstanding', 'floatShares']:
        if key in wacc_data:
            shares = wacc_data[key]
            break

    return {
        'years': years,
        'revenues': revenues,
        'ebitdas': ebitdas,
        'ebits': ebits,
        'nopats': nopats,
        'das': das,
        'capexs': capexs,
        'delta_wcs': delta_wcs,
        'fcffs': fcffs,
        'pv_fcffs': pv_fcffs,
        'discount_factors': discount_factors,
        'terminal_value': terminal_value,
        'pv_terminal': pv_terminal,
        'enterprise_value': enterprise_value,
        'net_debt': net_debt,
        'equity_value': equity_value,
        'sum_pv_fcffs': sum(pv_fcffs),
        'ebitda_margin_target': ebitda_margin_target,
        'capex_pct_revenue': capex_pct_revenue,
        'da_pct': da_pct,
        'wc_pct_revenue': wc_pct_revenue,
        'terminal_growth': terminal_growth,
        'wacc': wacc,
        'tax_rate': tax_rate,
        'base_revenue': base_revenue,
        'revenue_growth_phase1': revenue_growth_phase1,
        'revenue_growth_phase2': terminal_growth,
        'forecast_years': forecast_years,
        'phase2_years': phase2_years,
    }


def sensitivity_analysis(
    dcf_result: Dict,
    wacc_data: Dict,
    wacc_range: List[float] = None,
    tgr_range: List[float] = None,
) -> pd.DataFrame:
    """
    2D Sensitivity Table: WACC vs Terminal Growth Rate
    Returns matrix of implied equity values per share (or EV if no share count).
    """
    if wacc_range is None:
        base_wacc = dcf_result.get('wacc', 0.12)
        wacc_range = [base_wacc - 0.02, base_wacc - 0.01, base_wacc,
                      base_wacc + 0.01, base_wacc + 0.02]

    if tgr_range is None:
        base_tgr = dcf_result.get('terminal_growth', 0.05)
        tgr_range = [base_tgr - 0.01, base_tgr - 0.005, base_tgr,
                     base_tgr + 0.005, base_tgr + 0.01]

    net_debt = dcf_result.get('net_debt', 0)
    terminal_fcff = dcf_result['fcffs'][-1] * (1 + dcf_result['terminal_growth'])
    pv_explicit = dcf_result.get('sum_pv_fcffs', 0)
    n = len(dcf_result['fcffs'])

    matrix = []
    for tgr in tgr_range:
        row = []
        for w in wacc_range:
            if w <= tgr:
                row.append(None)
                continue
            tv = terminal_fcff / (w - tgr)
            pv_tv = tv / ((1 + w) ** n)

            # Re-compute explicit PV with new WACC
            new_pv_explicit = sum(
                f / ((1 + w) ** (i + 1))
                for i, f in enumerate(dcf_result['fcffs'])
            )

            ev = new_pv_explicit + pv_tv
            eq_val = ev - net_debt
            row.append(round(eq_val / 1e7, 0))  # In Crores

        matrix.append(row)

    wacc_labels = [f"{w*100:.1f}%" for w in wacc_range]
    tgr_labels = [f"{t*100:.1f}%" for t in tgr_range]

    df = pd.DataFrame(matrix, index=tgr_labels, columns=wacc_labels)
    df.index.name = 'TGR \\ WACC'
    return df


def valuation_bridge(dcf_result: Dict) -> Dict:
    """
    Build components for waterfall valuation bridge chart.
    EV → (-) Net Debt → Equity Value
    """
    return {
        'pv_fcffs': dcf_result.get('sum_pv_fcffs', 0),
        'pv_terminal': dcf_result.get('pv_terminal', 0),
        'enterprise_value': dcf_result.get('enterprise_value', 0),
        'net_debt': dcf_result.get('net_debt', 0),
        'equity_value': dcf_result.get('equity_value', 0),
    }
