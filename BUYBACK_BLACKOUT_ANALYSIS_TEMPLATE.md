# Buyback Blackout Period Analysis Template

## Overview

This template analyzes whether a stock underperforms during buyback blackout periods (when companies are restricted from repurchasing shares) compared to a benchmark index.

**Hypothesis**: When a major buyer (the company itself) steps away from the market during blackout periods, the stock should underperform. When buybacks resume after earnings, the stock should recover.

---

## Quick Start

```bash
cd "c:\Users\Iccanui\Documents\Github\BP\Stock buybacks"
pip install yfinance pandas numpy scipy matplotlib
python aapl_blackout_analysis.py
```

---

## How to Adapt for Other Stocks

### Step 1: Change the Stock Ticker

In `aapl_blackout_analysis.py`, update the `load_data()` function:

```python
def load_data():
    # Change "AAPL" to your target stock
    stock = yf.download("YOUR_TICKER", start="2012-01-01", end="2026-01-17", progress=False)
    spy = yf.download("SPY", start="2012-01-01", end="2026-01-17", progress=False)
```

**Alternative benchmarks:**
- `SPY` - S&P 500 (large cap US)
- `QQQ` - Nasdaq 100 (tech-heavy)
- `IWM` - Russell 2000 (small cap)
- `XLK` - Technology Select Sector
- `XLF` - Financial Select Sector

### Step 2: Update Earnings Dates

Replace `APPLE_EARNINGS_DATES` with your target company's earnings dates:

```python
EARNINGS_DATES = [
    "2026-01-XX",  # Upcoming
    "2025-10-XX",  # Q3
    "2025-07-XX",  # Q2
    # ... add all historical dates
]
```

**Where to find earnings dates:**
- Yahoo Finance: `https://finance.yahoo.com/quote/TICKER/history`
- Earnings Whispers: `https://www.earningswhispers.com/stocks/TICKER`
- SEC EDGAR: Search for 8-K filings

### Step 3: Adjust Blackout Window (Optional)

Default settings work for most US public companies:

```python
BLACKOUT_DAYS_BEFORE = 35  # 5 weeks before earnings (standard)
BLACKOUT_DAYS_AFTER = 2    # 2 trading days after earnings
POST_BLACKOUT_DAYS = 10    # Recovery analysis window
```

**Company-specific adjustments:**
- Some companies have longer blackouts (check proxy statements)
- Banks often have extended blackouts around stress tests
- Retail companies may have blackouts around holiday sales data

---

## Results from Apple (AAPL) Analysis

### Summary (2012-2026, 56 blackout periods)

| Metric | Value |
|--------|-------|
| Average AAPL Excess Return | **+0.68%** |
| Underperformance Rate | 42.9% |
| T-test p-value | 0.8355 |
| **Conclusion** | **Thesis NOT supported** |

### Key Findings

1. **Overall**: No statistically significant blackout effect
2. **By Quarter**: Q3 (Apr-Jun) shows significant **outperformance** (+3.08%, p=0.034)
3. **By Quarter**: Q1 (Oct-Dec) shows most underperformance (-1.95%) but not significant
4. **By Era**: 2012-2013 showed underperformance, 2017-2020 showed strong outperformance

### Monthly Breakdown

| Month | Count | Excess Return | P-value | Significant? |
|-------|-------|---------------|---------|--------------|
| January | 11 | -2.02% | 0.507 | No |
| February | 3 | -1.68% | 0.825 | No |
| April | 9 | -0.40% | 0.878 | No |
| May | 5 | +2.08% | 0.515 | No |
| **July** | 11 | **+3.46%** | **0.032** | **Yes** |
| August | 3 | +1.69% | 0.704 | No |
| October | 11 | +0.47% | 0.789 | No |
| November | 3 | +3.35% | 0.396 | No |

### Yearly Breakdown

| Year | Excess Return | Underperf% | Notes |
|------|---------------|------------|-------|
| 2012 | -4.14% | 66.7% | Post-Steve Jobs uncertainty |
| 2013 | -7.91% | 75.0% | Peak iPhone concerns |
| 2014 | +1.27% | 25.0% | iPhone 6 cycle begins |
| 2015 | +1.38% | 50.0% | Apple Watch launch |
| 2016 | -3.01% | 50.0% | iPhone sales plateau |
| 2017 | +6.15% | 0.0% | Services narrative begins |
| 2018 | +0.62% | 50.0% | Trade war concerns |
| 2019 | +5.67% | 25.0% | Strong momentum |
| 2020 | +6.36% | 25.0% | COVID beneficiary |
| 2021 | +1.21% | 25.0% | Supply chain issues |
| 2022 | +2.10% | 50.0% | Rate hike volatility |
| 2023 | +3.10% | 25.0% | AI narrative boost |
| 2024 | +1.21% | 50.0% | Mixed results |
| 2025 | -4.12% | 75.0% | Recent weakness |

---

## Output Files Generated

| File | Description |
|------|-------------|
| `aapl_blackout_results.csv` | Period-by-period blackout performance |
| `aapl_post_blackout_results.csv` | Post-earnings recovery data |
| `aapl_daily_analysis.csv` | Daily returns classified by blackout status |
| `aapl_monthly_analysis.csv` | Statistics grouped by earnings month |
| `aapl_quarterly_analysis.csv` | Statistics grouped by fiscal quarter |
| `aapl_yearly_analysis.csv` | Statistics grouped by year |
| `aapl_blackout_analysis.png` | Visualization charts |

---

## Statistical Tests Explained

### T-test (parametric)
- Tests if mean excess return is significantly different from zero
- Assumes normal distribution
- **p < 0.05**: Statistically significant
- **p < 0.10**: Marginally significant

### Mann-Whitney U (non-parametric)
- Tests if blackout vs non-blackout distributions differ
- No normality assumption
- More robust to outliers

### One-sample T-test (per month/quarter)
- Tests if that period's excess return is significantly different from zero
- Used in monthly/quarterly breakdowns

---

## Interpretation Guide

| Excess Return | Interpretation |
|---------------|----------------|
| < -1.0% | Strong support for blackout thesis |
| -0.5% to -1.0% | Moderate support |
| -0.5% to +0.5% | No clear effect |
| > +0.5% | Thesis NOT supported |

| P-value | Interpretation |
|---------|----------------|
| < 0.01 | Highly significant |
| < 0.05 | Significant |
| < 0.10 | Marginally significant |
| > 0.10 | Not significant |

---

## Confounding Variables to Consider

1. **Earnings surprise**: Good/bad results dominate any buyback effect
2. **Guidance**: Forward guidance often moves stock more than results
3. **Macro events**: FOMC meetings, geopolitical events during blackout
4. **Sector rotation**: Industry-wide moves unrelated to buybacks
5. **Seasonality**: January effect, summer doldrums, etc.
6. **10b5-1 plans**: ~60% of buybacks may continue via pre-programmed plans

---

## Companies with Large Buyback Programs

Good candidates for this analysis:

| Company | Ticker | Annual Buybacks (approx) |
|---------|--------|-------------------------|
| Apple | AAPL | $80-100B |
| Alphabet | GOOGL | $60-70B |
| Meta | META | $40-50B |
| Microsoft | MSFT | $30-40B |
| Nvidia | NVDA | $20-25B |
| Berkshire | BRK.B | $20-30B |
| JP Morgan | JPM | $15-20B |
| Bank of America | BAC | $15-20B |
| Visa | V | $15B |
| Home Depot | HD | $10-15B |

---

## Potential Trading Strategies (If Effect Found)

**If blackout underperformance confirmed:**
1. Short stock / buy puts 5 weeks before earnings
2. Cover / close 2 days after earnings
3. Go long after blackout ends for recovery

**Risk management:**
- Max position size: 2-5% of portfolio
- Stop loss: 10-15% adverse move
- Avoid earnings week (unpredictable)

**Important**: Apple data does NOT support this strategy. Test thoroughly on paper before risking capital.

---

## Code Architecture

```
aapl_blackout_analysis.py
├── Configuration
│   ├── EARNINGS_DATES (list)
│   └── BLACKOUT_DAYS_BEFORE/AFTER (int)
├── Data Loading
│   └── load_data() -> downloads price data
├── Window Generation
│   ├── get_blackout_window() -> single window
│   └── generate_blackout_windows() -> all windows
├── Analysis Functions
│   ├── calculate_period_return() -> returns for date range
│   ├── analyze_blackout_periods() -> main blackout analysis
│   ├── analyze_post_blackout() -> recovery analysis
│   ├── analyze_daily_returns() -> day-by-day classification
│   ├── analyze_by_month() -> monthly breakdown
│   ├── analyze_by_quarter() -> quarterly breakdown
│   └── analyze_by_year() -> yearly breakdown
├── Statistical Tests
│   └── run_statistical_tests() -> t-test, Mann-Whitney
├── Reporting
│   ├── print_summary() -> console output
│   ├── print_detailed_tables() -> period tables
│   ├── print_monthly_analysis() -> breakdowns
│   └── create_visualizations() -> charts
└── Main
    └── main() -> orchestrates everything
```

---

## Dependencies

```
yfinance>=0.2.0
pandas>=1.5.0
numpy>=1.20.0
scipy>=1.9.0
matplotlib>=3.5.0
```

---

## License

Free to use for personal research. Not financial advice.

---

## Last Updated

January 2026 - Analysis includes data through January 15, 2026
