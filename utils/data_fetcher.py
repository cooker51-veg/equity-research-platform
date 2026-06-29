"""
Data Fetching & Validation Layer
Handles all yfinance calls with robust error handling and data validation.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')


# NSE/BSE ticker suffix mapping
EXCHANGE_SUFFIXES = {
    'NSE': '.NS',
    'BSE': '.BO',
}

# Known Indian tickers for auto-detection
KNOWN_NSE_TICKERS = {
    'TRENT', 'POLYCAB', 'DIXON', 'ICICIBANK', 'INDIGO', 'RELIANCE',
    'TCS', 'INFY', 'HDFCBANK', 'WIPRO', 'LT', 'BAJFINANCE',
    'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'ASIANPAINT',
    'MARUTI', 'TITAN', 'SUNPHARMA', 'ULTRACEMCO', 'NESTLEIND',
    'TATAMOTORS', 'TATASTEEL', 'JSWSTEEL', 'POWERGRID', 'NTPC',
    'ONGC', 'COALINDIA', 'TECHM', 'HCLTECH', 'AXISBANK',
    'KOTAKBANK', 'ADANIENT', 'ADANIPORTS', 'BAJAJ-AUTO', 'HEROMOTOCO',
    'DRREDDY', 'CIPLA', 'DIVISLAB', 'BPCL', 'GRASIM'
}


def resolve_ticker(user_input: str) -> Tuple[str, str]:
    """
    Resolve user input to a valid yfinance ticker.
    Returns (ticker_symbol, exchange_label)
    """
    ticker = user_input.strip().upper()

    # Already has exchange suffix
    if ticker.endswith('.NS'):
        return ticker, 'NSE'
    if ticker.endswith('.BO'):
        return ticker, 'BSE'

    # Known NSE ticker
    if ticker in KNOWN_NSE_TICKERS:
        return f"{ticker}.NS", 'NSE'

    # Try NSE first, then BSE, then direct
    candidates = [
        (f"{ticker}.NS", 'NSE'),
        (f"{ticker}.BO", 'BSE'),
        (ticker, 'US/Other'),
    ]

    for symbol, exchange in candidates:
        try:
            t = yf.Ticker(symbol)
            info = t.info
            if info and info.get('regularMarketPrice') is not None:
                return symbol, exchange
            if info and info.get('currentPrice') is not None:
                return symbol, exchange
            # Check if we get meaningful data
            if info and info.get('longName'):
                return symbol, exchange
        except Exception:
            continue

    # Return best guess
    return f"{ticker}.NS", 'NSE'


def safe_get(info: dict, *keys, default=None):
    """Safely extract value from info dict, trying multiple keys."""
    for key in keys:
        val = info.get(key)
        if val is not None and val != 'N/A' and val != '':
            try:
                if isinstance(val, (int, float)) and not np.isnan(val):
                    return val
                if isinstance(val, str):
                    return val
            except (TypeError, ValueError):
                continue
    return default


def fetch_company_data(ticker_symbol: str) -> Dict[str, Any]:
    """
    Fetch comprehensive company data from yfinance.
    Returns structured dict with validation flags.
    """
    result = {
        'ticker': ticker_symbol,
        'info': {},
        'financials': None,
        'balance_sheet': None,
        'cashflow': None,
        'history': None,
        'quarterly_financials': None,
        'quarterly_balance_sheet': None,
        'errors': [],
        'warnings': []
    }

    try:
        ticker = yf.Ticker(ticker_symbol)

        # Basic info
        try:
            info = ticker.info
            if not info or not info.get('longName'):
                result['errors'].append("Company information not available for this ticker.")
            else:
                result['info'] = info
        except Exception as e:
            result['errors'].append(f"Failed to fetch company info: {str(e)}")

        # Annual financials
        try:
            fin = ticker.financials
            if fin is not None and not fin.empty:
                result['financials'] = fin
            else:
                result['warnings'].append("Annual income statement data not available.")
        except Exception as e:
            result['warnings'].append(f"Income statement unavailable: {str(e)}")

        # Balance sheet
        try:
            bs = ticker.balance_sheet
            if bs is not None and not bs.empty:
                result['balance_sheet'] = bs
            else:
                result['warnings'].append("Balance sheet data not available.")
        except Exception as e:
            result['warnings'].append(f"Balance sheet unavailable: {str(e)}")

        # Cash flow
        try:
            cf = ticker.cashflow
            if cf is not None and not cf.empty:
                result['cashflow'] = cf
            else:
                result['warnings'].append("Cash flow statement not available.")
        except Exception as e:
            result['warnings'].append(f"Cash flow unavailable: {str(e)}")

        # Price history
        try:
            hist = ticker.history(period="2y")
            if hist is not None and not hist.empty:
                result['history'] = hist
            else:
                result['warnings'].append("Price history not available.")
        except Exception as e:
            result['warnings'].append(f"Price history unavailable: {str(e)}")

        # Quarterly data
        try:
            qf = ticker.quarterly_financials
            if qf is not None and not qf.empty:
                result['quarterly_financials'] = qf
        except Exception:
            pass

        try:
            qbs = ticker.quarterly_balance_sheet
            if qbs is not None and not qbs.empty:
                result['quarterly_balance_sheet'] = qbs
        except Exception:
            pass

    except Exception as e:
        result['errors'].append(f"Critical data fetch error: {str(e)}")

    return result


def extract_financials(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and calculate all financial metrics from raw data.
    All calculations follow CFA/FMVA standards.
    """
    metrics = {
        'revenue': [],
        'ebitda': [],
        'ebit': [],
        'net_income': [],
        'total_assets': [],
        'total_equity': [],
        'total_debt': [],
        'cash': [],
        'capex': [],
        'operating_cf': [],
        'free_cash_flow': [],
        'depreciation': [],
        'interest_expense': [],
        'tax_expense': [],
        'years': [],
        'errors': []
    }

    info = data.get('info', {})
    fin = data.get('financials')
    bs = data.get('balance_sheet')
    cf = data.get('cashflow')

    if fin is None or fin.empty:
        metrics['errors'].append("No income statement data available")
        return metrics

    # Normalize index to lowercase
    def normalize_index(df):
        if df is None or df.empty:
            return df
        df.index = [str(i).strip() for i in df.index]
        return df

    fin = normalize_index(fin)
    bs = normalize_index(bs) if bs is not None else None
    cf = normalize_index(cf) if cf is not None else None

    # Get years (columns) - most recent first
    years = list(fin.columns)
    years.sort(reverse=True)

    def get_row(df, *row_names, default=0):
        if df is None or df.empty:
            return None
        for name in row_names:
            for idx in df.index:
                if name.lower() in idx.lower():
                    try:
                        vals = df.loc[idx]
                        return vals
                    except Exception:
                        continue
        return None

    def safe_val(series, year, default=0):
        if series is None:
            return default
        try:
            val = series[year]
            if pd.isna(val) or val is None:
                return default
            return float(val)
        except Exception:
            return default

    # Revenue
    rev_row = get_row(fin, 'Total Revenue', 'Revenue', 'Net Revenue')
    # EBIT (Operating Income)
    ebit_row = get_row(fin, 'Operating Income', 'EBIT', 'Ebit')
    # Net Income
    ni_row = get_row(fin, 'Net Income', 'Net Income Common Stockholders')
    # Depreciation & Amortization
    da_row = get_row(cf, 'Depreciation', 'Depreciation And Amortization', 'Depreciation Amortization Depletion')
    if da_row is None:
        da_row = get_row(fin, 'Reconciled Depreciation', 'Depreciation')
    # Interest Expense
    int_row = get_row(fin, 'Interest Expense', 'Net Interest Income')
    # Tax Expense
    tax_row = get_row(fin, 'Tax Provision', 'Income Tax Expense')
    # Operating CF
    ocf_row = get_row(cf, 'Operating Cash Flow', 'Cash From Operations', 'Net Cash Provided By Operating Activities')
    # Capex
    capex_row = get_row(cf, 'Capital Expenditure', 'Capital Expenditures', 'Purchase Of Ppe')
    # Total Assets
    assets_row = get_row(bs, 'Total Assets') if bs is not None else None
    # Total Equity
    equity_row = get_row(bs, 'Stockholders Equity', 'Total Stockholder Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity') if bs is not None else None
    # Total Debt
    debt_row = get_row(bs, 'Total Debt', 'Long Term Debt', 'Long Term Debt And Capital Lease Obligation') if bs is not None else None
    # Cash
    cash_row = get_row(bs, 'Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Cash And Short Term Investments') if bs is not None else None

    for year in years:
        rev = safe_val(rev_row, year)
        ebit = safe_val(ebit_row, year)
        da = safe_val(da_row, year)
        ni = safe_val(ni_row, year)
        int_exp = abs(safe_val(int_row, year)) if int_row is not None else 0
        tax = safe_val(tax_row, year)
        ocf = safe_val(ocf_row, year)
        capex = abs(safe_val(capex_row, year)) if capex_row is not None else 0
        assets = safe_val(assets_row, year) if assets_row is not None else 0
        equity = safe_val(equity_row, year) if equity_row is not None else 0
        debt = safe_val(debt_row, year) if debt_row is not None else 0
        cash = safe_val(cash_row, year) if cash_row is not None else 0

        ebitda = ebit + da
        fcf = ocf - capex

        metrics['years'].append(str(year.year) if hasattr(year, 'year') else str(year)[:4])
        metrics['revenue'].append(rev)
        metrics['ebitda'].append(ebitda)
        metrics['ebit'].append(ebit)
        metrics['net_income'].append(ni)
        metrics['total_assets'].append(assets)
        metrics['total_equity'].append(equity)
        metrics['total_debt'].append(debt)
        metrics['cash'].append(cash)
        metrics['capex'].append(capex)
        metrics['operating_cf'].append(ocf)
        metrics['free_cash_flow'].append(fcf)
        metrics['depreciation'].append(da)
        metrics['interest_expense'].append(int_exp)
        metrics['tax_expense'].append(tax)

    # Reverse to chronological order
    for key in metrics:
        if key not in ['errors'] and isinstance(metrics[key], list):
            metrics[key] = list(reversed(metrics[key]))

    return metrics


def calculate_ratios(metrics: Dict, info: Dict) -> Dict[str, Any]:
    """
    Calculate all financial ratios using standard CFA definitions.
    """
    ratios = {}

    rev = metrics.get('revenue', [])
    ebitda = metrics.get('ebitda', [])
    ebit = metrics.get('ebit', [])
    ni = metrics.get('net_income', [])
    assets = metrics.get('total_assets', [])
    equity = metrics.get('total_equity', [])
    debt = metrics.get('total_debt', [])
    cash = metrics.get('cash', [])
    fcf = metrics.get('free_cash_flow', [])
    int_exp = metrics.get('interest_expense', [])

    def safe_ratio(num, den, pct=False):
        try:
            if den and den != 0 and num is not None:
                r = num / den
                return r * 100 if pct else r
        except Exception:
            pass
        return None

    def cagr(values, years):
        """CAGR = (End/Start)^(1/n) - 1"""
        try:
            non_zero = [(v, i) for i, v in enumerate(values) if v and v > 0]
            if len(non_zero) >= 2:
                start_val = non_zero[0][0]
                end_val = non_zero[-1][0]
                n = len(values) - 1
                if n > 0 and start_val > 0:
                    return ((end_val / start_val) ** (1 / n) - 1) * 100
        except Exception:
            pass
        return None

    n_years = len(rev)

    # Profitability
    if rev and ebitda:
        ratios['ebitda_margin'] = [safe_ratio(e, r, pct=True) for e, r in zip(ebitda, rev)]
    if rev and ebit:
        ratios['ebit_margin'] = [safe_ratio(e, r, pct=True) for e, r in zip(ebit, rev)]
    if rev and ni:
        ratios['net_margin'] = [safe_ratio(n, r, pct=True) for n, r in zip(ni, rev)]

    # Returns
    if ni and equity:
        ratios['roe'] = [safe_ratio(n, e, pct=True) for n, e in zip(ni, equity)]
    if ebit and assets:
        ratios['roa'] = [safe_ratio(e, a, pct=True) for e, a in zip(ebit, assets)]
    # ROCE = EBIT / (Total Assets - Current Liabilities) — approximate with (Assets - Cash - Debt) if needed
    if ebit and assets and debt:
        capital_employed = [a - d for a, d in zip(assets, debt)]
        ratios['roce'] = [safe_ratio(e, c, pct=True) for e, c in zip(ebit, capital_employed)]

    # Leverage
    if debt and equity:
        ratios['debt_equity'] = [safe_ratio(d, e) for d, e in zip(debt, equity)]
    if ebit and int_exp:
        ratios['interest_coverage'] = [safe_ratio(e, i) for e, i in zip(ebit, int_exp) if i and i > 0]

    # CAGR
    ratios['revenue_cagr'] = cagr(rev, n_years)
    ratios['ebitda_cagr'] = cagr(ebitda, n_years)
    ratios['fcf_cagr'] = cagr([f for f in fcf if f and f > 0], n_years)

    # Latest values
    def latest(lst):
        if lst:
            for v in reversed(lst):
                if v is not None:
                    return v
        return None

    ratios['latest_ebitda_margin'] = latest(ratios.get('ebitda_margin', []))
    ratios['latest_ebit_margin'] = latest(ratios.get('ebit_margin', []))
    ratios['latest_net_margin'] = latest(ratios.get('net_margin', []))
    ratios['latest_roe'] = latest(ratios.get('roe', []))
    ratios['latest_roa'] = latest(ratios.get('roa', []))
    ratios['latest_roce'] = latest(ratios.get('roce', []))
    ratios['latest_de'] = latest(ratios.get('debt_equity', []))

    # Net Debt
    if debt and cash and len(debt) == len(cash):
        net_debt = [d - c for d, c in zip(debt, cash)]
        ratios['net_debt'] = net_debt
        ratios['latest_net_debt'] = latest(net_debt)

    return ratios


def get_peer_tickers(info: Dict, sector: str, industry: str) -> list:
    """
    Return a list of peer tickers based on sector/industry.
    Uses curated peer groups for common sectors.
    """
    # Curated Indian peer groups
    PEER_MAP = {
        'Technology': ['TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS'],
        'Consumer Electronics': ['DIXON.NS', 'AMBER.NS', 'VGUARD.NS'],
        'Electrical Equipment': ['POLYCAB.NS', 'HAVELLS.NS', 'VGUARD.NS', 'KEI.NS'],
        'Retail': ['TRENT.NS', 'DMART.NS', 'ABFRL.NS', 'SHOPERSTOP.NS'],
        'Airlines': ['INDIGO.NS', 'SPICEJET.NS'],
        'Banking': ['ICICIBANK.NS', 'HDFCBANK.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'SBIN.NS'],
        'Finance': ['BAJFINANCE.NS', 'BAJAJFINSV.NS', 'CHOLAFIN.NS', 'MUTHOOTFIN.NS'],
        'Pharmaceuticals': ['SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS'],
        'Automobile': ['MARUTI.NS', 'TATAMOTORS.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS', 'M&M.NS'],
        'Steel': ['TATASTEEL.NS', 'JSWSTEEL.NS', 'SAIL.NS', 'NMDC.NS'],
        'Oil & Gas': ['RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'IOC.NS'],
        'FMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'MARICO.NS', 'DABUR.NS'],
        'Cement': ['ULTRACEMCO.NS', 'AMBUJACEM.NS', 'SHREECEM.NS', 'ACC.NS'],
        'Paints': ['ASIANPAINT.NS', 'BERGEPAINT.NS', 'KANSAINER.NS'],
        'Diversified': ['RELIANCE.NS', 'ITC.NS', 'LT.NS'],
    }

    # Try to match
    for key, peers in PEER_MAP.items():
        if key.lower() in (industry or '').lower() or key.lower() in (sector or '').lower():
            return peers[:5]

    # Generic fallback - Nifty 50 large caps
    return ['TCS.NS', 'INFY.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS']


def fetch_peer_data(peer_tickers: list, info: Dict) -> pd.DataFrame:
    """
    Fetch valuation multiples for peer companies.
    Returns DataFrame with P/E, EV/EBITDA, P/B, EV/Revenue.
    """
    rows = []
    for ticker in peer_tickers:
        try:
            t = yf.Ticker(ticker)
            i = t.info
            if not i or not i.get('longName'):
                continue

            name = i.get('shortName', ticker.replace('.NS', '').replace('.BO', ''))
            pe = i.get('trailingPE') or i.get('forwardPE')
            pb = i.get('priceToBook')
            ev_ebitda = i.get('enterpriseToEbitda')
            ev_revenue = i.get('enterpriseToRevenue')
            market_cap = i.get('marketCap', 0)
            price = i.get('currentPrice') or i.get('regularMarketPrice')

            rows.append({
                'Company': name,
                'Ticker': ticker.replace('.NS', '').replace('.BO', ''),
                'P/E (x)': round(pe, 1) if pe and pe > 0 else None,
                'P/B (x)': round(pb, 2) if pb and pb > 0 else None,
                'EV/EBITDA (x)': round(ev_ebitda, 1) if ev_ebitda and ev_ebitda > 0 else None,
                'EV/Revenue (x)': round(ev_revenue, 2) if ev_revenue and ev_revenue > 0 else None,
                'Mkt Cap (Cr)': round(market_cap / 1e7, 0) if market_cap else None,
            })
        except Exception:
            continue

    return pd.DataFrame(rows) if rows else pd.DataFrame()
