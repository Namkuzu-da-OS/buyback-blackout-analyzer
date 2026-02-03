"""
Data models for buyback research agent.

These models capture what we DISCOVER, not what we assume.
The agent builds this data through research.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"       # Multiple sources agree, recent SEC filing
    MEDIUM = "medium"   # One reliable source, or older data
    LOW = "low"         # News only, or conflicting data
    UNVERIFIED = "unverified"  # Just discovered, needs validation


class DataSource(BaseModel):
    """Track where data came from."""
    source_type: str  # "sec_10k", "sec_10q", "news", "web_search"
    source_name: str  # "SEC EDGAR", "Bloomberg", etc.
    url: Optional[str] = None
    date_accessed: date
    date_published: Optional[date] = None
    excerpt: Optional[str] = None  # Relevant quote


class DiscoveredBuyback(BaseModel):
    """
    What we discover about a company's buyback program.
    All fields are optional because we learn incrementally.
    """
    ticker: str
    company_name: Optional[str] = None

    # What we discover (all optional until found)
    authorization_billions: Optional[float] = None
    remaining_billions: Optional[float] = None
    annual_rate_billions: Optional[float] = None
    quarterly_rate_billions: Optional[float] = None

    # Context
    program_start_year: Optional[int] = None
    last_increase_date: Optional[str] = None
    last_increase_amount_billions: Optional[float] = None

    # Data quality
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    sources: List[DataSource] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    needs_verification: bool = True

    # Notes from research
    research_notes: List[str] = Field(default_factory=list)

    def add_source(self, source: DataSource):
        self.sources.append(source)
        self.last_updated = datetime.now()

    def add_note(self, note: str):
        self.research_notes.append(f"[{datetime.now().isoformat()}] {note}")


class ResearchCandidate(BaseModel):
    """A company discovered during search that needs deeper research."""
    ticker: str
    company_name: Optional[str] = None

    # How we found it
    discovery_source: str  # "web_search", "sec_scan", "manual"
    discovery_query: Optional[str] = None  # The search that found it
    discovery_date: date = Field(default_factory=date.today)

    # What we initially found
    mentioned_buyback_amount: Optional[str] = None  # Raw text like "$50 billion"
    mention_count: int = 1  # How many sources mention this company

    # Research status
    researched: bool = False
    research_date: Optional[date] = None
    research_result: Optional[str] = None  # "included", "excluded", "watchlist"
    exclusion_reason: Optional[str] = None


class ValidatedCompany(BaseModel):
    """
    A company that has been researched and validated for the strategy.
    This is what goes into the final universe.
    """
    ticker: str
    company_name: str

    # Validated buyback data
    buyback: DiscoveredBuyback

    # Strategy assessment
    meets_threshold: bool  # Annual buyback >= minimum
    has_sufficient_history: bool  # Enough earnings cycles
    recommended_for_strategy: bool
    priority_tier: int  # 1=highest (Apple-tier), 2, 3, 4=watchlist

    # Comparison to archetype (Apple)
    buyback_vs_apple_pct: Optional[float] = None  # Their buyback as % of Apple's

    notes: Optional[str] = None


class BuybackUniverse(BaseModel):
    """
    The universe of companies we track.
    Built through discovery, not assumption.
    """
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    last_discovery_run: Optional[datetime] = None
    version: str = "1.0"

    # The archetype (our baseline)
    archetype_ticker: str = "AAPL"
    archetype_annual_buyback_billions: float = 90.0

    # Discovered and validated companies
    validated_companies: Dict[str, ValidatedCompany] = Field(default_factory=dict)

    # Research pipeline
    candidates: List[ResearchCandidate] = Field(default_factory=list)

    # Excluded (researched but didn't make cut)
    excluded: Dict[str, str] = Field(default_factory=dict)  # ticker -> reason

    # Change tracking
    changes: List[Dict[str, Any]] = Field(default_factory=list)

    def get_by_tier(self, tier: int) -> List[ValidatedCompany]:
        return [c for c in self.validated_companies.values() if c.priority_tier == tier]

    def get_recommended(self) -> List[ValidatedCompany]:
        return [c for c in self.validated_companies.values() if c.recommended_for_strategy]

    def add_candidate(self, candidate: ResearchCandidate):
        # Don't add duplicates
        existing = [c.ticker for c in self.candidates]
        if candidate.ticker not in existing:
            self.candidates.append(candidate)

    def log_change(self, change_type: str, ticker: str, details: str):
        self.changes.append({
            "timestamp": datetime.now().isoformat(),
            "type": change_type,
            "ticker": ticker,
            "details": details
        })


class ResearchReport(BaseModel):
    """Output from a research run."""
    run_date: datetime = Field(default_factory=datetime.now)
    run_type: str  # "discovery", "update", "single_company"

    # What was searched
    queries_run: List[str] = Field(default_factory=list)
    sources_checked: List[str] = Field(default_factory=list)

    # What was found
    new_candidates_found: int = 0
    companies_updated: int = 0
    companies_added: int = 0
    companies_removed: int = 0

    # Details
    findings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    def add_finding(self, finding: str):
        self.findings.append(finding)

    def add_error(self, error: str):
        self.errors.append(error)
