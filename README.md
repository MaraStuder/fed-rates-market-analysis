# Federal Funds Rate & S&P 500 Analysis

A Python data pipeline exploring US monetary policy and equity 
market performance using real economic data from the FRED API.

**Finding:** The correlation between rate changes and S&P 500 
returns turned strongly negative (−0.8) during the 2022–2023 
rate hike cycle, consistent with monetary policy theory, but 
reversed in 2024 as markets rallied despite elevated rates, 
suggesting the relationship shifts with broader market conditions.

---

## Pipeline

```
FRED API → build_database.py → fed_rates.db → rate_market_analyzer.py
```

Extract (fredapi) → Transform (pandas) → Load (DuckDB) → Analyse (Python class)

---

## Data

| Series | Description | Coverage |
|---|---|---|
| `FEDFUNDS` | Federal Funds Effective Rate | 2000–2024 |
| `SP500` | S&P 500 Index | 2015–2024 |

---

## Getting Started

The database is included — no API key needed to run the analysis.

```bash
git clone https://github.com/MaraStuder/fed-rates-market-analysis.git
cd fed-rates-market-analysis
uv sync
uv run python src/rate_market_analyzer.py
```

To rebuild the database yourself, get a free API key at 
[fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html), 
copy `.env.example` to `.env`, add your key, then run:

```bash
uv run python data/build_database.py
```

---

## Usage

```python
from src.rate_market_analyzer import RateMarketAnalyzer

analyzer = RateMarketAnalyzer()
analyzer.summary_statistics(start="2015-01-01")
analyzer.plot_both(start="2015-01-01")
analyzer.plot_rolling_correlation(window=12)
```

---

## Stack

Python • Pandas • DuckDB • Matplotlib • fredapi • uv