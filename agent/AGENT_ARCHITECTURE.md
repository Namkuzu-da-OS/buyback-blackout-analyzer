# Buyback Research Agent - Architecture

## Purpose

**Primary Mission:** Discover which companies have buyback programs large enough to matter for our strategy.

**Starting Point:** Apple is the only validated archetype. Everything else must be discovered and validated by this agent.

**Key Question the Agent Answers:** "Which companies should we even be tracking?"

---

## Agent Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      BUYBACK RESEARCH AGENT                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   TRIGGERS:                                                              │
│   ├── Scheduled: Weekly (Sunday night)                                  │
│   ├── On-demand: Manual invocation                                      │
│   └── Event: New earnings season approaching                            │
│                                                                          │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│   │   NEWS       │    │    SEC       │    │  FINANCIAL   │             │
│   │  SEARCH      │    │   EDGAR      │    │    DATA      │             │
│   │              │    │              │    │              │             │
│   │ - Buyback    │    │ - 10-Q       │    │ - Yahoo Fin  │             │
│   │   announce-  │    │ - 10-K       │    │ - Market cap │             │
│   │   ments      │    │ - 8-K        │    │ - Volume     │             │
│   │ - Program    │    │ - DEF 14A    │    │ - Price      │             │
│   │   changes    │    │   (proxy)    │    │              │             │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘             │
│          │                   │                   │                      │
│          └───────────────────┼───────────────────┘                      │
│                              ▼                                          │
│                    ┌─────────────────────┐                              │
│                    │    DATA PROCESSOR   │                              │
│                    │                     │                              │
│                    │ - Parse & extract   │                              │
│                    │ - Validate numbers  │                              │
│                    │ - Cross-reference   │                              │
│                    │ - Score confidence  │                              │
│                    └──────────┬──────────┘                              │
│                               │                                         │
│                               ▼                                         │
│                    ┌─────────────────────┐                              │
│                    │  BUYBACK UNIVERSE   │                              │
│                    │   (JSON Database)   │                              │
│                    │                     │                              │
│                    │ - Company profiles  │                              │
│                    │ - Program details   │                              │
│                    │ - Change history    │                              │
│                    │ - Confidence scores │                              │
│                    └──────────┬──────────┘                              │
│                               │                                         │
│                               ▼                                         │
│                    ┌─────────────────────┐                              │
│                    │      ALERTS         │                              │
│                    │                     │                              │
│                    │ - New programs      │                              │
│                    │ - Size changes      │                              │
│                    │ - Program endings   │                              │
│                    └─────────────────────┘                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### 1. SEC EDGAR (Primary - Most Reliable)

**Filing Types:**
| Filing | Contains | Frequency |
|--------|----------|-----------|
| 10-K | Annual buyback summary, total repurchased, remaining authorization | Annual |
| 10-Q | Quarterly buyback activity, remaining authorization | Quarterly |
| 8-K | New buyback announcements, authorization increases | Event-driven |
| DEF 14A | Proxy statements with buyback program details | Annual |

**What to extract:**
```
- Total authorization amount
- Amount remaining
- Shares repurchased (period)
- Dollar amount repurchased (period)
- Average price paid
- Authorization expiration date (if any)
```

**SEC EDGAR API:**
- Base URL: `https://www.sec.gov/cgi-bin/browse-edgar`
- Full-text search: `https://efts.sec.gov/LATEST/search-index`
- Company filings: `https://data.sec.gov/submissions/CIK{cik}.json`

### 2. Financial News (Secondary - Timely)

**Search queries:**
```
"{company} buyback announcement"
"{company} share repurchase program"
"{company} increases buyback"
"{company} authorizes repurchase"
"{ticker} buyback billion"
```

**News sources to prioritize:**
- Bloomberg
- Reuters
- Wall Street Journal
- Company press releases (via PR Newswire, Business Wire)
- SEC 8-K filings (often simultaneous with press release)

### 3. Financial Data APIs (Supplementary)

**For market context:**
- Market cap (to calculate buyback as % of market cap)
- Average daily volume (to calculate buyback as % of volume)
- Current price

**Sources:**
- yfinance (free, sufficient for our needs)
- Alpha Vantage (free tier available)
- Polygon.io (if we need more)

---

## Data Schema

### buyback_universe.json

```json
{
  "metadata": {
    "last_updated": "2026-02-03T12:00:00Z",
    "agent_version": "1.0",
    "total_companies": 25,
    "update_frequency": "weekly"
  },
  "companies": {
    "AAPL": {
      "company_name": "Apple Inc.",
      "cik": "0000320193",
      "sector": "Technology",
      "industry": "Consumer Electronics",

      "current_program": {
        "authorization_total_billions": 110,
        "authorization_remaining_billions": 45,
        "annual_run_rate_billions": 90,
        "quarterly_pace_billions": 22.5,
        "program_start_date": "2012-03-19",
        "last_increase_date": "2025-05-01",
        "last_increase_amount_billions": 10,
        "expiration_date": null
      },

      "market_context": {
        "market_cap_billions": 3500,
        "buyback_as_pct_of_market_cap": 2.57,
        "avg_daily_volume_millions": 42,
        "buyback_as_pct_of_daily_volume": 6.0
      },

      "historical": {
        "cumulative_buybacks_billions": 650,
        "years_active": 14,
        "largest_single_year_billions": 95
      },

      "data_quality": {
        "last_verified": "2026-02-01",
        "primary_source": "10-K FY2025",
        "confidence": "high",
        "notes": "Largest corporate buyback program in history"
      },

      "strategy_fit": {
        "material_buyback": true,
        "sufficient_history": true,
        "recommended_for_strategy": true,
        "priority": 1
      }
    }
  },

  "watchlist": {
    "potential_additions": [
      {
        "ticker": "AVGO",
        "reason": "Growing buyback program, $10B+ annual",
        "needs_research": true
      }
    ],
    "recently_removed": [
      {
        "ticker": "XYZ",
        "reason": "Program ended",
        "removed_date": "2026-01-15"
      }
    ]
  },

  "change_log": [
    {
      "date": "2026-02-01",
      "ticker": "AAPL",
      "change_type": "authorization_increase",
      "old_value": 100,
      "new_value": 110,
      "source": "Q4 2025 Earnings Call"
    }
  ]
}
```

---

## Discovery Mode (How We Find Candidates)

**The agent doesn't start with a list - it builds one through research.**

### Initial Discovery Workflow

```
1. BROAD SEARCH - Cast a wide net
   │
   ├── Web search: "largest stock buyback programs 2025 2026"
   ├── Web search: "biggest share repurchase authorizations"
   ├── Web search: "companies buying back most stock"
   ├── Web search: "S&P 500 buyback leaders"
   │
   └── Output: List of company names/tickers mentioned

2. CANDIDATE RANKING - Which names come up most?
   │
   ├── Count mentions across sources
   ├── Note any dollar amounts mentioned
   ├── Filter to US-listed stocks
   │
   └── Output: Ranked list of potential candidates

3. DEEP DIVE - Research each candidate
   │
   FOR EACH candidate (starting with most mentioned):
   │
   ├── Search SEC EDGAR for recent 10-Q/10-K
   ├── Extract actual buyback numbers:
   │   ├── Total authorization
   │   ├── Remaining authorization
   │   ├── Quarterly/annual activity
   │   └── Program start date
   │
   ├── Search news for recent announcements
   ├── Cross-reference multiple sources
   │
   └── Output: Validated buyback data OR "insufficient data"

4. MATERIALITY CHECK - Does it meet our threshold?
   │
   ├── Annual buyback rate > $10B? (adjustable threshold)
   ├── Data quality sufficient?
   ├── Enough history for backtesting?
   │
   └── Output: INCLUDE / EXCLUDE / WATCHLIST

5. BUILD UNIVERSE - Compile validated companies
   │
   ├── Add validated companies to universe
   ├── Add borderline cases to watchlist
   ├── Document exclusions with reasons
   │
   └── Output: buyback_universe.json
```

### Discovery Search Queries

**Tier 1 - General Discovery:**
```
"largest corporate buyback programs"
"biggest stock repurchase 2025 2026"
"companies with biggest buybacks"
"top 10 buyback stocks"
"S&P 500 buyback spending"
```

**Tier 2 - Sector-Specific:**
```
"tech companies buyback programs"
"financial sector share repurchase"
"healthcare buyback leaders"
```

**Tier 3 - Recent Activity:**
```
"new buyback authorization billion"
"buyback increase announcement"
"share repurchase program announced"
```

**Tier 4 - Comparative:**
```
"Apple vs Microsoft buyback comparison"
"which company buys back most stock"
"buyback as percentage of market cap"
```

### What Makes a Good Candidate?

| Criterion | Minimum | Why It Matters |
|-----------|---------|----------------|
| Annual buyback | $10B+ | Below this, price impact is minimal |
| Program age | 2+ years | Need historical data for backtesting |
| Consistency | Regular quarterly | Sporadic buybacks = unpredictable |
| Data availability | SEC filings exist | Must be verifiable |

### Known Starting Point

**Apple is the ONLY validated archetype.** We know:
- $90B/year buyback (largest in the world)
- 14 years of history
- Strategy works (77% win rate in late blackout)

**Everything else is hypothesis until validated.**

The agent's job is to find: "Are there other Apples out there?"

---

## Agent Workflow

### Weekly Run (Scheduled)

```
1. INITIALIZE
   ├── Load current buyback_universe.json
   ├── Load list of tracked companies
   └── Set date range for searches (last 7 days)

2. FOR EACH TRACKED COMPANY:
   │
   ├── 2a. CHECK SEC EDGAR
   │   ├── Query for new 10-Q, 10-K, 8-K filings
   │   ├── If found: Parse for buyback data
   │   └── Update company record if changed
   │
   ├── 2b. SEARCH NEWS
   │   ├── Search for "{company} buyback" news
   │   ├── Filter to last 7 days
   │   ├── If found: Extract key information
   │   └── Cross-reference with SEC data
   │
   └── 2c. UPDATE MARKET CONTEXT
       ├── Fetch current market cap
       ├── Fetch average volume
       └── Recalculate percentages

3. DISCOVER NEW CANDIDATES
   ├── Search for "largest stock buybacks 2026"
   ├── Search for "biggest share repurchase programs"
   ├── Compare against current universe
   └── Add to watchlist if not tracked

4. VALIDATE & SCORE
   ├── Cross-reference multiple sources
   ├── Flag discrepancies
   ├── Update confidence scores
   └── Mark stale data (>90 days old)

5. GENERATE OUTPUT
   ├── Update buyback_universe.json
   ├── Generate change_log entries
   ├── Create alerts for significant changes
   └── Update last_updated timestamp

6. ALERT (if changes detected)
   ├── New programs > $10B
   ├── Authorization increases > $5B
   ├── Programs ending
   └── Companies leaving/entering top 20
```

### On-Demand Research (Single Company)

```
research_company(ticker: str) -> CompanyBuybackData
   │
   ├── Fetch all SEC filings (last 2 years)
   ├── Search news (last 6 months)
   ├── Extract buyback data from each source
   ├── Cross-reference and validate
   ├── Calculate confidence score
   └── Return structured data
```

---

## Implementation Plan

### Phase 1: Core Data Structures
- [ ] Define Pydantic models for buyback data
- [ ] Create buyback_universe.json with initial companies
- [ ] Build manual data entry for known companies (AAPL, GOOGL, etc.)

### Phase 2: SEC EDGAR Integration
- [ ] Implement SEC EDGAR API client
- [ ] Build 10-Q/10-K parser for buyback sections
- [ ] Extract authorization amounts and activity
- [ ] Handle CIK lookups

### Phase 3: News Search Integration
- [ ] Implement news search (web search API or scraping)
- [ ] Build buyback-specific query generator
- [ ] Parse news articles for key data points
- [ ] Cross-reference with SEC data

### Phase 4: Agent Orchestration
- [ ] Build main agent loop
- [ ] Implement scheduling (cron or APScheduler)
- [ ] Add logging and error handling
- [ ] Create alert system

### Phase 5: Validation & Refinement
- [ ] Test on known companies
- [ ] Validate data accuracy
- [ ] Tune confidence scoring
- [ ] Add new companies to universe

---

## Key Functions

```python
# Core agent functions (to be implemented)

async def run_weekly_update() -> UpdateReport:
    """Run full weekly update cycle."""
    pass

async def research_company(ticker: str) -> CompanyBuybackData:
    """Deep research on a single company."""
    pass

async def search_sec_filings(cik: str, filing_types: list, date_range: tuple) -> list[Filing]:
    """Search SEC EDGAR for filings."""
    pass

async def parse_buyback_from_filing(filing: Filing) -> BuybackData:
    """Extract buyback data from SEC filing."""
    pass

async def search_buyback_news(company: str, date_range: tuple) -> list[NewsArticle]:
    """Search for buyback-related news."""
    pass

def calculate_confidence_score(data: CompanyBuybackData) -> float:
    """Score data quality 0-1 based on recency and source reliability."""
    pass

def detect_changes(old: CompanyBuybackData, new: CompanyBuybackData) -> list[Change]:
    """Detect and classify changes between data versions."""
    pass

def should_alert(change: Change) -> bool:
    """Determine if a change warrants an alert."""
    pass
```

---

## Materiality Thresholds

**For a company to be included in the strategy universe:**

| Criterion | Minimum | Ideal | Notes |
|-----------|---------|-------|-------|
| Annual buyback rate | $5B | $20B+ | Below $5B unlikely to move needle |
| Buyback as % of market cap | 1% | 2%+ | Higher = more price impact |
| Program history | 2 years | 5+ years | Need data for backtesting |
| Data quality | Medium | High | Must be verifiable |

**Priority tiers:**

| Tier | Annual Buyback | Examples |
|------|----------------|----------|
| 1 (Must Track) | $50B+ | AAPL |
| 2 (High Priority) | $20-50B | GOOGL, META, MSFT |
| 3 (Track) | $10-20B | NVDA, various |
| 4 (Watch) | $5-10B | AMZN, others |

---

## Error Handling

| Error | Handling |
|-------|----------|
| SEC API rate limit | Exponential backoff, cache responses |
| Filing not found | Log, continue, flag for manual review |
| Parse failure | Log error, use last known good data |
| News search fails | Continue with SEC data only |
| Data conflict | Flag discrepancy, use SEC as primary |

---

## Monitoring & Logging

**Log events:**
- Agent start/stop
- Each company processed
- New filings found
- Data changes detected
- Errors and warnings
- Alert triggers

**Metrics to track:**
- Last successful run
- Companies updated
- Data freshness (avg days since last update)
- Confidence score distribution
- Alert count

---

## Future Enhancements

1. **Earnings call transcript parsing** - Extract buyback commentary from calls
2. **Insider trading correlation** - Cross-reference with Form 4 filings
3. **Sector aggregates** - Track total tech sector buybacks
4. **Prediction model** - Predict future buyback announcements
5. **Real-time 8-K monitoring** - Immediate alerts on new announcements

---

## File Structure

```
agent/
├── AGENT_ARCHITECTURE.md     # This file
├── research_agent.py         # Main agent orchestration
├── models.py                 # Pydantic data models
├── sources/
│   ├── sec_edgar.py          # SEC EDGAR API client
│   ├── news_search.py        # News search integration
│   └── market_data.py        # Financial data (yfinance)
├── parsers/
│   ├── filing_parser.py      # Parse SEC filings
│   └── news_parser.py        # Parse news articles
├── data/
│   ├── buyback_universe.json # Main database
│   └── change_log.json       # Historical changes
└── tests/
    └── test_agent.py
```
