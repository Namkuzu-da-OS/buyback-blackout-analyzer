# Buyback Blackout Trading System - Project Plan

## Overview

A multi-component trading system that identifies high-conviction entry points during corporate buyback blackout periods. The core thesis: when companies with massive buyback programs ($25B+/year) pause repurchases during blackout periods, supply/demand dynamics create predictable price patterns - specifically weakness early in blackout and strength late in blackout, creating buying opportunities.

## The Strategy

**Entry Signal Confluence:**
- Stock is in **late blackout period** (1 week before earnings)
- Price at **technical support** (200 SMA, 50 SMA)
- **RSI oversold** (< 30)
- Company has **material buyback program** (large enough to move the needle)
- Historical win rate supports the trade

**The Edge (from Apple analysis):**
| Phase | Timing | Expected Excess Return | Action |
|-------|--------|------------------------|--------|
| Early Blackout | Days 1-14 | -2% to -3% | AVOID |
| Mid Blackout | Days 15-28 | -1% | TRANSITION |
| Late Blackout | Days 29-35 | +1.5% to +2% | BUY |
| Post-Earnings | Days 36-50 | +2% (15-day) | HOLD |

**Optimal Trade:**
- Entry: Late blackout (1 week before earnings)
- Exit: 15 days post-earnings
- Expected excess return: ~3-4%
- Historical win rate: ~77%

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Trading Signal Dashboard                      │
│         (Web UI - FastAPI + lightweight HTML/JS)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │     Buyback      │  │     Buyback      │  │   Earnings    │ │
│  │    Blackout      │  │    Research      │  │   Calendar    │ │
│  │    Service       │  │     Agent        │  │   (existing)  │ │
│  │                  │  │                  │  │               │ │
│  │ - Current status │  │ - Finds buyback  │  │ - Upcoming    │ │
│  │ - Historical     │  │   programs       │  │   earnings    │ │
│  │   analysis       │  │ - Tracks changes │  │   dates       │ │
│  │ - Signals        │  │ - Updates weekly │  │               │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 ▼                               │
│                    ┌─────────────────────┐                      │
│                    │  Signal Aggregator  │                      │
│                    │                     │                      │
│                    │  Combines:          │                      │
│                    │  - Blackout phase   │                      │
│                    │  - Technical levels │                      │
│                    │  - RSI              │                      │
│                    │  - Buyback size     │                      │
│                    │  → Conviction score │                      │
│                    └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Buyback Blackout Service (API)

**Purpose:** Provide blackout period status and signals via API

**Endpoints:**
- `GET /blackout/status` - All tracked stocks' current blackout phase
- `GET /blackout/status/{ticker}` - Detailed status for one stock
- `GET /blackout/signals` - Stocks currently in buy zone (late blackout)
- `GET /blackout/calendar` - Upcoming blackout windows
- `GET /blackout/analyze/{ticker}` - Run full historical analysis

**Output per stock:**
```json
{
  "ticker": "AAPL",
  "blackout_phase": "late",
  "days_to_earnings": 5,
  "blackout_day": 30,
  "historical_win_rate": 0.77,
  "avg_excess_return": 1.79,
  "price": 185.50,
  "sma_200": 182.30,
  "sma_50": 188.40,
  "rsi_14": 28,
  "buyback_annual": "90B",
  "signal": "BUY_ZONE",
  "conviction": "HIGH"
}
```

**Tech Stack:** FastAPI + Python

**Data Refresh:** Daily (but blackout phases move weekly, so not urgent)

---

### 2. Buyback Research Agent

**Purpose:** Continuously maintain the universe of stocks with material buyback programs

**Runs:** Weekly (scheduled) + on-demand

**Data Sources:**
- SEC EDGAR (10-Q, 10-K filings)
- Financial news (buyback announcements)
- Company press releases
- Earnings call transcripts

**Outputs:**
- `buyback_universe.json` - Current list of material buyback programs
- Change log - Who increased/decreased programs
- Alerts - Significant changes

**Data tracked per company:**
```json
{
  "AAPL": {
    "company_name": "Apple Inc.",
    "authorization_total": "110B",
    "annual_run_rate": "90B",
    "remaining_pct": 45,
    "program_start": 2012,
    "last_increase": "2025-10-30",
    "last_updated": "2026-01-15",
    "data_source": "Q4 2025 10-K filing",
    "recent_news": "Board authorized additional $10B",
    "confidence": "high",
    "notes": "Largest corporate buyback program in history"
  }
}
```

**Thresholds for inclusion:**
- Minimum annual buyback: $10B+ (TBD - need to validate with backtesting)
- Or: Buyback > X% of market cap
- Or: Buyback > X% of average daily volume

---

### 3. Earnings Calendar Integration

**Purpose:** Provide upcoming earnings dates to the system

**Note:** User has existing earnings calendar tool - will integrate with that

**Required data:**
- Ticker
- Next earnings date
- Earnings time (before/after market)

---

### 4. Web Dashboard

**Purpose:** Daily view of the system status and signals

**Features:**
- Current blackout status for all tracked stocks
- Highlighted "buy zone" stocks
- Click into individual stock for detail
- Historical performance charts
- Research agent status/last update

**Tech Stack:** FastAPI serving HTML/JS (no heavy framework)

---

## Current State

**Existing code:**
- `buyback_analyzer.py` - Full CLI analyzer (working)
- `blackout_analysis_generic.py` - Generic analysis functions
- Earnings database for: AAPL, GOOGL, META, MSFT, NVDA, AMZN
- Apple-specific analysis and results in `/apple` folder

**What's validated:**
- Apple shows clear blackout effect
- Late blackout = buying opportunity (77% win rate)
- Post-earnings recovery is strong

**What needs validation:**
- Does pattern hold for GOOGL, META, MSFT, NVDA, AMZN?
- What's the minimum buyback size for the effect to matter?

---

## Next Steps

### Phase 1: Validate Strategy
- [ ] Run existing analyzer on all stocks in database (GOOGL, META, MSFT, NVDA, AMZN)
- [ ] Compare results - does the pattern hold?
- [ ] Determine if this is Apple-only or broader strategy

### Phase 2: Build API Service
- [ ] Create FastAPI app structure
- [ ] Implement `/blackout/status` endpoint
- [ ] Implement `/blackout/signals` endpoint
- [ ] Add basic technicals (SMA, RSI) to output
- [ ] Test endpoints

### Phase 3: Research Agent
- [ ] Define data sources (SEC EDGAR, news APIs)
- [ ] Build agent to search for buyback news
- [ ] Build agent to parse SEC filings
- [ ] Create `buyback_universe.json` schema
- [ ] Set up weekly scheduled runs

### Phase 4: Dashboard
- [ ] Simple HTML/JS frontend
- [ ] Connect to API endpoints
- [ ] Display current status grid
- [ ] Add detail view per stock

### Phase 5: Integration
- [ ] Connect to existing earnings calendar
- [ ] Connect to other existing systems (sector strength, technicals)
- [ ] Unified signal output

---

## Open Questions

1. **Buyback threshold:** What's the minimum buyback size for this strategy to work?
2. **Universe size:** How many stocks should we track? (Currently 6, could expand to 20-30)
3. **Data source for prices:** yfinance for now, Schwab API later?
4. **Alert mechanism:** Email? Telegram? Discord?
5. **Backtesting:** Should we build more rigorous backtesting before going live?

---

## File Structure (Proposed)

```
buyback-blackout-analyzer/
├── api/
│   ├── main.py              # FastAPI app
│   ├── routes/
│   │   ├── blackout.py      # Blackout endpoints
│   │   └── health.py        # Health check
│   └── models/
│       └── schemas.py       # Pydantic models
├── agent/
│   ├── research_agent.py    # Buyback research agent
│   ├── sources/
│   │   ├── sec_edgar.py     # SEC filing parser
│   │   └── news_search.py   # News search
│   └── data/
│       └── buyback_universe.json
├── core/
│   ├── analyzer.py          # Core analysis logic (refactored from buyback_analyzer.py)
│   ├── technicals.py        # SMA, RSI calculations
│   └── data_fetcher.py      # Price data fetching
├── dashboard/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       └── index.html
├── data/
│   ├── earnings_database.json
│   └── historical_results/
├── tests/
├── requirements.txt
├── config.py
├── PROJECT_PLAN.md          # This file
└── README.md
```

---

## Notes

- This system doesn't need real-time data - blackout phases move in weekly increments
- Focus on material buybacks only - small programs don't move the needle
- Apple is the canonical example - $90B/year buyback is massive
- The edge is in late blackout + technical confluence
- Keep it simple - don't over-engineer before validating the strategy works broadly
