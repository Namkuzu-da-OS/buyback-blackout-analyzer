# Buyback Blackout Period Analyzer

A quantitative analysis tool for identifying trading opportunities during corporate buyback blackout periods.

## The Edge

Major corporations with massive buyback programs (~$20-100B annually) must pause repurchases during "blackout periods" - typically 5 weeks before earnings through 2 days after. When these consistent buyers step away, supply/demand dynamics shift.

**Key Insight from Apple Analysis:**
- The weakness is **front-loaded** (early blackout: -1.99% excess)
- Late blackout shows **strength** (+1.79% excess, 77% win rate)
- Post-earnings recovery is strong (+1.95% at 15 days, 77% win rate)
- **This creates a predictable buying opportunity in late blackout**

## Project Structure

```
Stock buybacks/
├── buyback_analyzer.py      # Main generic analyzer (run this)
├── apple/                   # Apple-specific analysis & results
│   ├── AAPL_BLACKOUT_REPORT.md
│   ├── aapl_blackout_data.json
│   ├── aapl_blackout_analysis.py
│   ├── aapl_january_deep_dive.py
│   └── [CSV and PNG results]
└── README.md
```

## Quick Start

```bash
# Analyze Apple
python buyback_analyzer.py --ticker AAPL

# Analyze Google vs QQQ benchmark
python buyback_analyzer.py --ticker GOOGL --benchmark QQQ

# Analyze Meta from 2018
python buyback_analyzer.py --ticker META --start-date 2018-01-01

# List available stocks
python buyback_analyzer.py --list-stocks
```

## Stocks in Database

| Ticker | Annual Buyback | Earnings Dates | Notes |
|--------|----------------|----------------|-------|
| AAPL | ~$90B | 56 | Largest buyback program |
| GOOGL | ~$62B | 44 | Aggressive since 2022 |
| META | ~$40B | 44 | Ramped up 2023-2024 |
| MSFT | ~$35B | 44 | Consistent buyer |
| NVDA | ~$25B | 36 | Growing program |
| AMZN | ~$10B | 40 | Newer program (2022) |

## Output Files

For each analyzed stock, the tool generates:
- `{ticker}_blackout_results.csv` - All blackout period returns
- `{ticker}_monthly_analysis.csv` - Performance by earnings month
- `{ticker}_yearly_analysis.csv` - Performance by year
- `{ticker}_post_blackout.csv` - Recovery period analysis
- `{ticker}_summary.json` - Summary statistics & current setup
- `{ticker}_blackout_analysis.png` - Visualization charts

## The Strategy

Based on Apple's January analysis pattern:

| Phase | Timing | Expected Excess | Action |
|-------|--------|-----------------|--------|
| Early Blackout | Days 1-14 | -2% to -3% | AVOID or SHORT |
| Mid Blackout | Days 15-28 | -1% | TRANSITION |
| Late Blackout | Days 29-35 | +1.5% to +2% | BUY |
| Post-Earnings | Days 36-50 | +2% (15-day) | HOLD |

**Optimal Trade:**
- Entry: Late blackout (1 week before earnings)
- Exit: 15 days post-earnings
- Expected excess return: ~3-4%
- Historical win rate: ~77%

## Requirements

```
pip install yfinance pandas numpy scipy matplotlib
```

## Adding New Stocks

Edit `EARNINGS_DATABASE` in `buyback_analyzer.py` to add earnings dates:

```python
EARNINGS_DATABASE['TICKER'] = [
    '2026-01-29',  # Most recent first
    '2025-10-30',
    # ... historical dates
]
```

## Disclaimer

This analysis is for informational and educational purposes only. Past performance does not guarantee future results. Always conduct your own research before making investment decisions.
