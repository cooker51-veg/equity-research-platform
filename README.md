# AI-Assisted Equity Research Platform

A production-ready institutional equity research platform combining financial modelling, DCF valuation, comparable company analysis, and AI-assisted research generation.

Built as a flagship finance portfolio project for MSc Finance admissions, equity research, investment banking, and private equity recruiting.

---

## Platform Overview

This platform replicates the core workflow of a professional equity research workstation:

| Module | Description |
|---|---|
| Company Overview | Live price, market data, 52W range, multiples, business description |
| Financial Analysis | Revenue/EBITDA trends, margin analysis, return ratios, FCF generation |
| DCF Valuation | 3-stage FCFF model, WACC (CAPM), terminal value, sensitivity matrix |
| Peer Comparables | Auto-identified sector peers, EV/EBITDA, P/E, P/B, EV/Revenue |
| AI Research Engine | Business model, investment thesis, risk analysis (Claude AI) |
| Investment Memo | Full institutional-grade research memo generation |
| PDF Export | One-click professionally formatted PDF report |

---

## Technology Stack

- **Frontend/App**: Streamlit
- **Data**: yfinance (Yahoo Finance — NSE, BSE, US markets)
- **Charts**: Plotly (interactive, institutional dark theme)
- **AI Engine**: Anthropic Claude (claude-sonnet-4-6)
- **PDF**: ReportLab
- **Finance**: pandas, numpy, scipy

---

## Installation & Local Setup

### Prerequisites

- Python 3.9 or higher
- pip

### Step 1: Clone or download the project

```bash
git clone <your-repo-url>
cd equity_research
```

### Step 2: Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set up your Anthropic API key

```bash
# Option A: Environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Option B: Create a .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

Or enter the key directly in the sidebar when the app is running.

### Step 5: Run the application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Deployment

### Option A: Streamlit Community Cloud (Free, Recommended)

1. Push this project to a GitHub repository
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select your repository, branch, and `app.py` as the entry point
5. Add your `ANTHROPIC_API_KEY` in **Settings → Secrets**:

```toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

6. Click Deploy — your app gets a public URL immediately

### Option B: Heroku

```bash
# Add Procfile
echo "web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

heroku create your-app-name
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
git push heroku main
```

### Option C: Railway / Render

Both platforms support Python apps with `requirements.txt`. Set the start command to:

```
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

Add `ANTHROPIC_API_KEY` as an environment variable in the platform dashboard.

---

## Project Structure

```
equity_research/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── assets/
│   └── styles.css            # CSS reference
├── utils/
│   ├── __init__.py
│   └── data_fetcher.py       # yfinance data layer & validation
└── modules/
    ├── __init__.py
    ├── dcf_engine.py          # DCF/WACC valuation engine
    ├── ai_research.py         # Anthropic Claude AI research module
    ├── charts.py              # Plotly chart library
    └── pdf_generator.py       # ReportLab PDF generation
```

---

## Supported Tickers

### Indian Markets (NSE/BSE)
Enter the base ticker — the platform auto-appends `.NS` or `.BO`:

```
TRENT, POLYCAB, DIXON, ICICIBANK, INDIGO, RELIANCE, TCS, INFY,
HDFCBANK, WIPRO, LT, BAJFINANCE, HINDUNILVR, ITC, SBIN, BHARTIARTL,
ASIANPAINT, MARUTI, TITAN, SUNPHARMA, TATAMOTORS, TATASTEEL, JSWSTEEL
```

### US Markets
Enter the standard ticker directly:
```
AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, JPM, GS
```

---

## DCF Methodology

The DCF model follows **CFA/FMVA FCFF (Free Cash Flow to Firm)** methodology:

### FCFF Formula
```
FCFF = NOPAT + D&A - Capex - ΔWorking Capital
NOPAT = EBIT × (1 - Tax Rate)
```

### 3-Stage Model
- **Stage 1**: High-growth phase (user-defined, default 15%, Years 1-5)
- **Stage 2**: Transition/fade phase (Years 6-8, linear interpolation to TGR)
- **Stage 3**: Terminal value via Gordon Growth Model

### Terminal Value
```
TV = FCFFn+1 / (WACC - g)
```

### WACC (CAPM)
```
Ke = Rf + β × ERP   (Risk-free: India 10Y G-Sec ~7.2%, ERP: 6.0%)
WACC = (E/V) × Ke + (D/V) × Kd × (1 - t)
```

---

## Financial Ratios — Definitions

All ratios follow standard CFA Institute definitions:

| Ratio | Formula |
|---|---|
| EBITDA Margin | EBITDA / Revenue |
| EBIT Margin | EBIT / Revenue |
| Net Margin | Net Income / Revenue |
| ROE | Net Income / Total Equity |
| ROCE | EBIT / Capital Employed |
| ROA | EBIT / Total Assets |
| D/E Ratio | Total Debt / Total Equity |
| Interest Coverage | EBIT / Interest Expense |
| FCF | Operating CF - Capex |
| Revenue CAGR | (End/Start)^(1/n) - 1 |

---

## CV / Portfolio Guidance

When presenting this project to recruiters or admissions committees:

### What to highlight
- **Financial modelling**: 3-stage DCF with WACC estimation, sensitivity tables
- **Data engineering**: Live market data pipeline with validation and error handling
- **AI integration**: Responsible LLM integration with clear labelling and guardrails
- **Full-stack deployment**: Production-ready Python application, publicly deployed

### Suggested CV entry
> **AI-Assisted Equity Research Platform** | Python, Streamlit, Anthropic Claude API
> Built a production-grade equity research tool featuring 3-stage DCF valuation (FCFF methodology),
> comparable company analysis, AI-assisted research generation, and one-click PDF report export.
> Supports NSE/BSE/US tickers with live market data. Deployed at [your-url].

### Interview talking points
- Explain the FCFF vs FCFE distinction and why FCFF was chosen
- Walk through the WACC calculation (CAPM, cost of debt, capital structure)
- Discuss terminal value sensitivity and why TV dominates DCF outputs
- Explain peer group selection methodology
- Discuss AI guardrails — why the system is instructed not to fabricate data

---

## Data Sources & Limitations

- **Market data**: Yahoo Finance via yfinance library
- **Update frequency**: Real-time prices, quarterly/annual financials as filed
- **AI analysis**: Anthropic Claude, based on provided data only
- **Limitations**: yfinance may have gaps for some Indian mid-caps; forward estimates not available for all stocks

---

## Disclaimer

This platform is built for **educational and portfolio demonstration purposes only**.

It does not constitute investment advice, a solicitation, or a recommendation to buy or sell any security.

AI-generated analysis sections are clearly labelled and should not be relied upon for investment decisions.

Always conduct independent research and consult a registered financial advisor.

---

## License

MIT License — free to use, modify, and distribute for educational purposes.

---

*Built with Python · Streamlit · Anthropic Claude · yfinance · Plotly · ReportLab*
