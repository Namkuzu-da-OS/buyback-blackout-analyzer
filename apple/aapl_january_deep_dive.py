"""
aapl_january_deep_dive.py
Deep analysis of Apple January blackout patterns

Analyzes:
1. Market regime effects on January underperformance
2. Intra-blackout timing (when does weakness occur)
3. Post-earnings recovery patterns
4. Current setup scorecard for January 2026
5. Trade recommendations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURATION
# ============================================

APPLE_EARNINGS_DATES = [
    # 2026
    "2026-01-29",
    # 2025
    "2025-10-30", "2025-07-31", "2025-05-01", "2025-01-30",
    # 2024
    "2024-10-31", "2024-08-01", "2024-05-02", "2024-02-01",
    # 2023
    "2023-11-02", "2023-08-03", "2023-05-04", "2023-02-02",
    # 2022
    "2022-10-27", "2022-07-28", "2022-04-28", "2022-01-27",
    # 2021
    "2021-10-28", "2021-07-27", "2021-04-28", "2021-01-27",
    # 2020
    "2020-10-29", "2020-07-30", "2020-04-30", "2020-01-28",
    # 2019
    "2019-10-30", "2019-07-30", "2019-04-30", "2019-01-29",
    # 2018
    "2018-11-01", "2018-07-31", "2018-05-01", "2018-02-01",
    # 2017
    "2017-11-02", "2017-08-01", "2017-05-02", "2017-01-31",
    # 2016
    "2016-10-25", "2016-07-26", "2016-04-26", "2016-01-26",
    # 2015
    "2015-10-27", "2015-07-21", "2015-04-27", "2015-01-27",
    # 2014
    "2014-10-20", "2014-07-22", "2014-04-23", "2014-01-27",
    # 2013
    "2013-10-28", "2013-07-23", "2013-04-23", "2013-01-23",
]

# Get January/February earnings only (Q1 fiscal reports)
JANUARY_EARNINGS = [e for e in APPLE_EARNINGS_DATES
                    if pd.to_datetime(e).month in [1, 2]]

BLACKOUT_DAYS_BEFORE = 35
BLACKOUT_DAYS_AFTER = 2


# ============================================
# DATA LOADING
# ============================================

def load_data():
    """Download AAPL and SPY price data."""
    print("Downloading AAPL and SPY data...")

    aapl = yf.download("AAPL", start="2012-01-01", end="2026-01-17", progress=False)
    spy = yf.download("SPY", start="2012-01-01", end="2026-01-17", progress=False)

    # Flatten multi-index columns if present
    if isinstance(aapl.columns, pd.MultiIndex):
        aapl.columns = aapl.columns.get_level_values(0)
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)

    print(f"  AAPL: {len(aapl)} trading days")
    print(f"  SPY:  {len(spy)} trading days")

    return aapl, spy


def calculate_period_return(price_data, start_date, end_date):
    """Calculate total return between two dates."""
    price_col = 'Adj Close' if 'Adj Close' in price_data.columns else 'Close'
    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    period_data = price_data.loc[mask, price_col]

    if len(period_data) < 2:
        return np.nan

    return (period_data.iloc[-1] / period_data.iloc[0] - 1) * 100


# ============================================
# ANALYSIS 1: MARKET REGIME EFFECT
# ============================================

def classify_market_regime(aapl_data, spy_data, blackout_start, earnings_date):
    """
    Classify market conditions at the START of each blackout.
    """
    price_col = 'Adj Close' if 'Adj Close' in aapl_data.columns else 'Close'

    # Look at 30 calendar days before blackout starts
    lookback_start = blackout_start - timedelta(days=30)

    mask = (aapl_data.index >= lookback_start) & (aapl_data.index < blackout_start)
    aapl_lookback = aapl_data.loc[mask]
    spy_lookback = spy_data.loc[mask]

    if len(aapl_lookback) < 10:
        return None

    regime = {'earnings_date': earnings_date}

    # 1. AAPL momentum (20-day return before blackout)
    regime['aapl_pre_momentum'] = (
        aapl_lookback[price_col].iloc[-1] / aapl_lookback[price_col].iloc[0] - 1
    ) * 100

    # 2. SPY momentum (market trend)
    regime['spy_pre_momentum'] = (
        spy_lookback[price_col].iloc[-1] / spy_lookback[price_col].iloc[0] - 1
    ) * 100

    # 3. AAPL relative strength
    regime['relative_strength'] = regime['aapl_pre_momentum'] - regime['spy_pre_momentum']

    # 4. AAPL vs 50-day MA at blackout start
    aapl_50ma = aapl_data[price_col].rolling(50).mean()
    valid_prices = aapl_data.loc[aapl_data.index <= blackout_start, price_col]
    valid_ma = aapl_50ma.loc[aapl_50ma.index <= blackout_start]

    if len(valid_prices) > 0 and len(valid_ma) > 0:
        blackout_price = valid_prices.iloc[-1]
        ma_50 = valid_ma.iloc[-1]
        regime['above_50ma'] = blackout_price > ma_50
        regime['pct_from_50ma'] = (blackout_price / ma_50 - 1) * 100
    else:
        regime['above_50ma'] = None
        regime['pct_from_50ma'] = np.nan

    # 5. AAPL vs 200-day MA
    aapl_200ma = aapl_data[price_col].rolling(200).mean()
    valid_ma_200 = aapl_200ma.loc[aapl_200ma.index <= blackout_start]

    if len(valid_prices) > 0 and len(valid_ma_200) > 0 and not pd.isna(valid_ma_200.iloc[-1]):
        ma_200 = valid_ma_200.iloc[-1]
        regime['above_200ma'] = blackout_price > ma_200
        regime['pct_from_200ma'] = (blackout_price / ma_200 - 1) * 100
    else:
        regime['above_200ma'] = None
        regime['pct_from_200ma'] = np.nan

    # 6. Market volatility (SPY realized vol)
    spy_returns = spy_lookback[price_col].pct_change()
    regime['market_volatility'] = spy_returns.std() * np.sqrt(252) * 100

    # 7. Distance from 52-week high
    aapl_52wk = aapl_data.loc[aapl_data.index <= blackout_start].tail(252)
    if len(aapl_52wk) > 0:
        high_52wk = aapl_52wk[price_col].max()
        regime['pct_from_52wk_high'] = (blackout_price / high_52wk - 1) * 100
    else:
        regime['pct_from_52wk_high'] = np.nan

    return regime


def analyze_regime_effect(aapl_data, spy_data, january_earnings):
    """
    Analyze how market regime affects January blackout performance.
    """
    results = []

    for earnings_str in january_earnings:
        earnings_date = pd.to_datetime(earnings_str)
        blackout_start = earnings_date - timedelta(days=BLACKOUT_DAYS_BEFORE)
        blackout_end = earnings_date + timedelta(days=BLACKOUT_DAYS_AFTER)

        # Skip if data not available
        if blackout_start < aapl_data.index.min() or blackout_end > aapl_data.index.max():
            continue

        # Get regime classification
        regime = classify_market_regime(aapl_data, spy_data, blackout_start, earnings_date)
        if regime is None:
            continue

        # Calculate blackout performance
        aapl_ret = calculate_period_return(aapl_data, blackout_start, blackout_end)
        spy_ret = calculate_period_return(spy_data, blackout_start, blackout_end)

        if pd.isna(aapl_ret) or pd.isna(spy_ret):
            continue

        regime['aapl_return'] = aapl_ret
        regime['spy_return'] = spy_ret
        regime['excess_return'] = aapl_ret - spy_ret

        results.append(regime)

    df = pd.DataFrame(results)

    print("\n" + "=" * 80)
    print("ANALYSIS 1: MARKET REGIME EFFECT ON JANUARY BLACKOUT")
    print("=" * 80)
    print("\nDoes market condition at blackout start affect the underperformance?\n")

    if len(df) == 0:
        print("No data available for analysis.")
        return df

    # Split by AAPL pre-momentum
    weak_momentum = df[df['aapl_pre_momentum'] < 0]
    strong_momentum = df[df['aapl_pre_momentum'] >= 0]

    print("BY PRE-BLACKOUT MOMENTUM (20 days before):")
    print("-" * 60)
    print(f"When AAPL FALLING into blackout (negative momentum):")
    print(f"  Count: {len(weak_momentum)}")
    if len(weak_momentum) > 0:
        print(f"  Avg Excess Return: {weak_momentum['excess_return'].mean():+.2f}%")
        print(f"  Underperformance Rate: {(weak_momentum['excess_return'] < 0).mean()*100:.1f}%")

    print(f"\nWhen AAPL RISING into blackout (positive momentum):")
    print(f"  Count: {len(strong_momentum)}")
    if len(strong_momentum) > 0:
        print(f"  Avg Excess Return: {strong_momentum['excess_return'].mean():+.2f}%")
        print(f"  Underperformance Rate: {(strong_momentum['excess_return'] < 0).mean()*100:.1f}%")

    # Split by distance from 52-week high
    print("\n\nBY DISTANCE FROM 52-WEEK HIGH:")
    print("-" * 60)
    near_highs = df[df['pct_from_52wk_high'] > -10]
    off_highs = df[df['pct_from_52wk_high'] <= -10]

    print(f"When AAPL near 52-week highs (within 10%):")
    print(f"  Count: {len(near_highs)}")
    if len(near_highs) > 0:
        print(f"  Avg Excess Return: {near_highs['excess_return'].mean():+.2f}%")
        print(f"  Underperformance Rate: {(near_highs['excess_return'] < 0).mean()*100:.1f}%")

    print(f"\nWhen AAPL off 52-week highs (>10% down):")
    print(f"  Count: {len(off_highs)}")
    if len(off_highs) > 0:
        print(f"  Avg Excess Return: {off_highs['excess_return'].mean():+.2f}%")
        print(f"  Underperformance Rate: {(off_highs['excess_return'] < 0).mean()*100:.1f}%")

    # Split by 50-day MA
    print("\n\nBY 50-DAY MOVING AVERAGE:")
    print("-" * 60)
    above_ma = df[df['above_50ma'] == True]
    below_ma = df[df['above_50ma'] == False]

    print(f"When AAPL ABOVE 50-day MA:")
    print(f"  Count: {len(above_ma)}")
    if len(above_ma) > 0:
        print(f"  Avg Excess Return: {above_ma['excess_return'].mean():+.2f}%")
        print(f"  Underperformance Rate: {(above_ma['excess_return'] < 0).mean()*100:.1f}%")

    print(f"\nWhen AAPL BELOW 50-day MA:")
    print(f"  Count: {len(below_ma)}")
    if len(below_ma) > 0:
        print(f"  Avg Excess Return: {below_ma['excess_return'].mean():+.2f}%")
        print(f"  Underperformance Rate: {(below_ma['excess_return'] < 0).mean()*100:.1f}%")

    # Split by market volatility
    print("\n\nBY MARKET VOLATILITY:")
    print("-" * 60)
    median_vol = df['market_volatility'].median()
    high_vol = df[df['market_volatility'] > median_vol]
    low_vol = df[df['market_volatility'] <= median_vol]

    print(f"High volatility environment (vol > {median_vol:.1f}%):")
    print(f"  Count: {len(high_vol)}")
    if len(high_vol) > 0:
        print(f"  Avg Excess Return: {high_vol['excess_return'].mean():+.2f}%")

    print(f"\nLow volatility environment (vol <= {median_vol:.1f}%):")
    print(f"  Count: {len(low_vol)}")
    if len(low_vol) > 0:
        print(f"  Avg Excess Return: {low_vol['excess_return'].mean():+.2f}%")

    return df


# ============================================
# ANALYSIS 2: INTRA-BLACKOUT TIMING
# ============================================

def analyze_intra_blackout_timing(aapl_data, spy_data, january_earnings):
    """
    Break down each blackout period into segments and measure returns.
    """
    all_segments = []

    for earnings_str in january_earnings:
        earnings_date = pd.to_datetime(earnings_str)
        blackout_start = earnings_date - timedelta(days=BLACKOUT_DAYS_BEFORE)
        blackout_end = earnings_date + timedelta(days=BLACKOUT_DAYS_AFTER)

        # Skip if data not available
        if blackout_start < aapl_data.index.min() or blackout_end > aapl_data.index.max():
            continue

        segments = {
            'earnings_date': earnings_date,
            'early_blackout': {},  # Days 1-14
            'mid_blackout': {},    # Days 15-28
            'late_blackout': {},   # Days 29-35 (pre-earnings)
            'post_earnings': {},   # Days 36-37 (earnings reaction)
        }

        # Early blackout (first 2 weeks)
        start = blackout_start
        end = blackout_start + timedelta(days=14)
        segments['early_blackout'] = {
            'aapl_return': calculate_period_return(aapl_data, start, end),
            'spy_return': calculate_period_return(spy_data, start, end),
        }
        segments['early_blackout']['excess_return'] = (
            segments['early_blackout']['aapl_return'] - segments['early_blackout']['spy_return']
            if not pd.isna(segments['early_blackout']['aapl_return']) else np.nan
        )

        # Mid blackout (weeks 3-4)
        start = blackout_start + timedelta(days=14)
        end = blackout_start + timedelta(days=28)
        segments['mid_blackout'] = {
            'aapl_return': calculate_period_return(aapl_data, start, end),
            'spy_return': calculate_period_return(spy_data, start, end),
        }
        segments['mid_blackout']['excess_return'] = (
            segments['mid_blackout']['aapl_return'] - segments['mid_blackout']['spy_return']
            if not pd.isna(segments['mid_blackout']['aapl_return']) else np.nan
        )

        # Late blackout (week 5 to earnings)
        start = blackout_start + timedelta(days=28)
        end = earnings_date
        segments['late_blackout'] = {
            'aapl_return': calculate_period_return(aapl_data, start, end),
            'spy_return': calculate_period_return(spy_data, start, end),
        }
        segments['late_blackout']['excess_return'] = (
            segments['late_blackout']['aapl_return'] - segments['late_blackout']['spy_return']
            if not pd.isna(segments['late_blackout']['aapl_return']) else np.nan
        )

        # Post earnings (earnings reaction)
        start = earnings_date
        end = blackout_end
        segments['post_earnings'] = {
            'aapl_return': calculate_period_return(aapl_data, start, end),
            'spy_return': calculate_period_return(spy_data, start, end),
        }
        segments['post_earnings']['excess_return'] = (
            segments['post_earnings']['aapl_return'] - segments['post_earnings']['spy_return']
            if not pd.isna(segments['post_earnings']['aapl_return']) else np.nan
        )

        all_segments.append(segments)

    print("\n" + "=" * 80)
    print("ANALYSIS 2: INTRA-BLACKOUT TIMING")
    print("=" * 80)
    print("\nWhen during the blackout does the underperformance occur?\n")

    segment_names = ['early_blackout', 'mid_blackout', 'late_blackout', 'post_earnings']
    segment_labels = {
        'early_blackout': 'Early Blackout (Days 1-14, ~Dec 25 - Jan 8)',
        'mid_blackout': 'Mid Blackout (Days 15-28, ~Jan 8-22)',
        'late_blackout': 'Late Blackout (Days 29-35, ~Jan 22-29)',
        'post_earnings': 'Post Earnings (Days 36-37, Jan 29-31)',
    }

    print(f"{'Segment':<50} {'AAPL':>10} {'SPY':>10} {'Excess':>10} {'Win%':>8}")
    print("-" * 90)

    segment_stats = []

    for segment in segment_names:
        excess_returns = [s[segment]['excess_return'] for s in all_segments
                         if not pd.isna(s[segment]['excess_return'])]
        aapl_returns = [s[segment]['aapl_return'] for s in all_segments
                       if not pd.isna(s[segment]['aapl_return'])]
        spy_returns = [s[segment]['spy_return'] for s in all_segments
                      if not pd.isna(s[segment]['spy_return'])]

        if excess_returns:
            avg_excess = np.mean(excess_returns)
            avg_aapl = np.mean(aapl_returns)
            avg_spy = np.mean(spy_returns)
            win_rate = sum(1 for r in excess_returns if r > 0) / len(excess_returns) * 100

            print(f"{segment_labels[segment]:<50} {avg_aapl:>+9.2f}% {avg_spy:>+9.2f}% "
                  f"{avg_excess:>+9.2f}% {win_rate:>7.1f}%")

            segment_stats.append({
                'segment': segment,
                'avg_aapl': avg_aapl,
                'avg_spy': avg_spy,
                'avg_excess': avg_excess,
                'win_rate': win_rate,
                'count': len(excess_returns)
            })

    print("\nINTERPRETATION:")

    # Find worst segment
    if segment_stats:
        worst = min(segment_stats, key=lambda x: x['avg_excess'])
        best = max(segment_stats, key=lambda x: x['avg_excess'])

        print(f"  - WORST segment: {worst['segment'].replace('_', ' ').title()} ({worst['avg_excess']:+.2f}%)")
        print(f"  - BEST segment: {best['segment'].replace('_', ' ').title()} ({best['avg_excess']:+.2f}%)")

    return all_segments, segment_stats


# ============================================
# ANALYSIS 3: POST-EARNINGS RECOVERY
# ============================================

def analyze_post_earnings_recovery(aapl_data, spy_data, january_earnings):
    """
    Analyze AAPL performance in the days and weeks AFTER January earnings.
    """
    windows = {
        '2_day': 2,
        '5_day': 5,
        '10_day': 10,
        '15_day': 15,
        '20_day': 20,
        '1_month': 30,
    }

    results = []

    for earnings_str in january_earnings:
        earnings_date = pd.to_datetime(earnings_str)

        # Skip future or very recent dates
        if earnings_date > aapl_data.index.max() - timedelta(days=35):
            continue

        row = {'earnings_date': earnings_date}

        for window_name, days in windows.items():
            start = earnings_date + timedelta(days=3)  # After blackout ends
            end = earnings_date + timedelta(days=3 + days)

            aapl_ret = calculate_period_return(aapl_data, start, end)
            spy_ret = calculate_period_return(spy_data, start, end)

            row[f'{window_name}_aapl'] = aapl_ret
            row[f'{window_name}_spy'] = spy_ret
            row[f'{window_name}_excess'] = aapl_ret - spy_ret if not pd.isna(aapl_ret) else np.nan

        results.append(row)

    df = pd.DataFrame(results)

    print("\n" + "=" * 80)
    print("ANALYSIS 3: POST-JANUARY EARNINGS RECOVERY")
    print("=" * 80)
    print("\nDoes AAPL bounce back after January earnings when buybacks resume?\n")

    print(f"{'Window':<12} {'AAPL Avg':>12} {'SPY Avg':>12} {'Excess':>12} {'Win Rate':>12} {'Count':>8}")
    print("-" * 70)

    for window_name in windows.keys():
        excess_col = f'{window_name}_excess'
        if excess_col in df.columns:
            excess = df[excess_col].dropna()
            aapl = df[f'{window_name}_aapl'].dropna()
            spy = df[f'{window_name}_spy'].dropna()

            if len(excess) > 0:
                win_rate = (excess > 0).mean() * 100
                print(f"{window_name:<12} {aapl.mean():>+11.2f}% {spy.mean():>+11.2f}% "
                      f"{excess.mean():>+11.2f}% {win_rate:>11.1f}% {len(excess):>8}")

    print("\nINTERPRETATION:")
    print("  - POSITIVE excess return = buyback resumption provides support")
    print("  - Win rate > 50% = the pattern is consistent")
    print("  - Look for window with highest excess return for optimal holding period")

    return df


# ============================================
# ANALYSIS 4: CURRENT SETUP SCORECARD
# ============================================

def generate_current_setup_scorecard(aapl_data, spy_data, current_date="2026-01-16"):
    """
    Score the current January 2026 setup based on historical patterns.
    """
    price_col = 'Adj Close' if 'Adj Close' in aapl_data.columns else 'Close'

    current = pd.to_datetime(current_date)
    earnings_date = pd.to_datetime("2026-01-29")
    blackout_start = earnings_date - timedelta(days=BLACKOUT_DAYS_BEFORE)

    print("\n" + "=" * 80)
    print("ANALYSIS 4: JANUARY 2026 SETUP SCORECARD")
    print("=" * 80)
    print()

    scorecard = {}

    # 1. Days into blackout
    days_into_blackout = (current - blackout_start).days
    days_remaining = (earnings_date - current).days
    print(f"BLACKOUT PROGRESS:")
    print(f"  Blackout started: {blackout_start.date()}")
    print(f"  Current date: {current.date()}")
    print(f"  Day {days_into_blackout} of 35 ({days_into_blackout/35*100:.0f}% complete)")
    print(f"  Days until earnings: {days_remaining}")
    print()

    # 2. Current price vs moving averages
    current_price = aapl_data.loc[aapl_data.index <= current, price_col].iloc[-1]
    ma_50 = aapl_data[price_col].rolling(50).mean().loc[aapl_data.index <= current].iloc[-1]
    ma_200 = aapl_data[price_col].rolling(200).mean().loc[aapl_data.index <= current].iloc[-1]

    scorecard['current_price'] = current_price
    scorecard['above_50ma'] = current_price > ma_50
    scorecard['above_200ma'] = current_price > ma_200

    print(f"TECHNICAL POSITION:")
    print(f"  Current Price: ${current_price:.2f}")
    print(f"  50-day MA: ${ma_50:.2f} ({'ABOVE' if current_price > ma_50 else 'BELOW'})")
    print(f"  200-day MA: ${ma_200:.2f} ({'ABOVE' if current_price > ma_200 else 'BELOW'})")
    print(f"  % from 50-day MA: {(current_price/ma_50-1)*100:+.2f}%")
    print(f"  % from 200-day MA: {(current_price/ma_200-1)*100:+.2f}%")
    print()

    # 3. Distance from 52-week high
    aapl_52wk = aapl_data.loc[aapl_data.index <= current].tail(252)
    high_52wk = aapl_52wk[price_col].max()
    pct_from_high = (current_price / high_52wk - 1) * 100
    scorecard['pct_from_52wk_high'] = pct_from_high

    print(f"52-WEEK CONTEXT:")
    print(f"  52-week High: ${high_52wk:.2f}")
    print(f"  Distance from High: {pct_from_high:.1f}%")
    print()

    # 4. Pre-blackout momentum
    lookback_start = blackout_start - timedelta(days=30)
    pre_blackout_data = aapl_data.loc[
        (aapl_data.index >= lookback_start) & (aapl_data.index < blackout_start),
        price_col
    ]
    if len(pre_blackout_data) > 1:
        pre_momentum = (pre_blackout_data.iloc[-1] / pre_blackout_data.iloc[0] - 1) * 100
        scorecard['pre_momentum'] = pre_momentum
        print(f"PRE-BLACKOUT MOMENTUM (20 days before Dec 25):")
        print(f"  AAPL return: {pre_momentum:+.2f}%")
    print()

    # 5. Performance so far this blackout
    blackout_aapl = aapl_data.loc[
        (aapl_data.index >= blackout_start) & (aapl_data.index <= current),
        price_col
    ]
    blackout_spy = spy_data.loc[
        (spy_data.index >= blackout_start) & (spy_data.index <= current),
        'Adj Close' if 'Adj Close' in spy_data.columns else 'Close'
    ]

    if len(blackout_aapl) > 1:
        aapl_blackout_ret = (blackout_aapl.iloc[-1] / blackout_aapl.iloc[0] - 1) * 100
        spy_blackout_ret = (blackout_spy.iloc[-1] / blackout_spy.iloc[0] - 1) * 100
        excess_so_far = aapl_blackout_ret - spy_blackout_ret

        scorecard['blackout_aapl_return'] = aapl_blackout_ret
        scorecard['blackout_spy_return'] = spy_blackout_ret
        scorecard['blackout_excess'] = excess_so_far

        print(f"PERFORMANCE THIS BLACKOUT (Dec 25 - Jan 16):")
        print(f"  AAPL: {aapl_blackout_ret:+.2f}%")
        print(f"  SPY:  {spy_blackout_ret:+.2f}%")
        print(f"  Excess: {excess_so_far:+.2f}%")
    print()

    # 6. Historical comparison
    print("HISTORICAL JANUARY BLACKOUT STATS:")
    print("  Average Excess Return: -2.02%")
    print("  Underperformance Rate: 54.5%")
    print("  Sample Size: 11 January cycles")
    print()

    # 7. Regime classification
    print("=" * 80)
    print("SETUP ASSESSMENT")
    print("=" * 80)

    bearish_factors = []
    bullish_factors = []
    neutral_factors = []

    # MA analysis
    if not scorecard.get('above_50ma', True):
        bearish_factors.append("Below 50-day moving average")
    else:
        bullish_factors.append("Above 50-day moving average")

    if not scorecard.get('above_200ma', True):
        bearish_factors.append("Below 200-day moving average")
    else:
        bullish_factors.append("Above 200-day moving average")

    # Distance from highs
    if pct_from_high < -15:
        bearish_factors.append(f"Already down {abs(pct_from_high):.1f}% from 52-week highs (extended decline)")
    elif pct_from_high < -10:
        neutral_factors.append(f"Down {abs(pct_from_high):.1f}% from highs (moderate pullback)")
    else:
        bullish_factors.append("Near 52-week highs")

    # Pre-momentum
    if scorecard.get('pre_momentum', 0) < -5:
        bearish_factors.append(f"Negative pre-blackout momentum ({scorecard.get('pre_momentum', 0):+.1f}%)")
    elif scorecard.get('pre_momentum', 0) > 5:
        bullish_factors.append(f"Positive pre-blackout momentum ({scorecard.get('pre_momentum', 0):+.1f}%)")

    # Blackout performance so far
    if scorecard.get('blackout_excess', 0) < -3:
        bearish_factors.append(f"Already underperforming this blackout ({scorecard.get('blackout_excess', 0):+.1f}%)")
    elif scorecard.get('blackout_excess', 0) > 3:
        bullish_factors.append(f"Outperforming this blackout so far ({scorecard.get('blackout_excess', 0):+.1f}%)")

    # Timing
    if days_into_blackout > 25:
        neutral_factors.append("Late in blackout - most weakness may have occurred")
    elif days_into_blackout < 14:
        neutral_factors.append("Early in blackout - weakness may still be ahead")

    print("\nBEARISH FACTORS:")
    if bearish_factors:
        for f in bearish_factors:
            print(f"  - {f}")
    else:
        print("  (none)")

    print("\nBULLISH FACTORS:")
    if bullish_factors:
        for f in bullish_factors:
            print(f"  - {f}")
    else:
        print("  (none)")

    print("\nNEUTRAL FACTORS:")
    if neutral_factors:
        for f in neutral_factors:
            print(f"  - {f}")
    else:
        print("  (none)")

    # Overall score
    score = len(bearish_factors) - len(bullish_factors)
    print(f"\nOVERALL BIAS: ", end="")
    if score > 1:
        print("BEARISH (favors underperformance thesis)")
    elif score < -1:
        print("BULLISH (thesis may not work this time)")
    else:
        print("NEUTRAL (mixed signals)")

    return scorecard


# ============================================
# ANALYSIS 5: TRADE RECOMMENDATION
# ============================================

def generate_trade_recommendation(scorecard, regime_df, recovery_df):
    """
    Generate specific trade recommendations based on analysis.
    """
    print("\n" + "=" * 80)
    print("ANALYSIS 5: TRADE RECOMMENDATIONS")
    print("=" * 80)

    print("\nBased on January blackout historical performance:")
    print("  Expected AAPL underperformance vs SPY: -2.02%")
    print("  Historical win rate for underperformance: 54.5%")
    print()

    print("OPTION A: PAIRS TRADE (Market Neutral)")
    print("-" * 60)
    print("  Strategy: Short AAPL / Long SPY")
    print("  Entry: Now (or early blackout)")
    print("  Exit: 2 days after earnings (Jan 31)")
    print("  Expected profit: ~2% of notional")
    print("  Risk: Strong earnings causes AAPL outperformance")
    print()

    print("OPTION B: PUT SPREAD (Defined Risk)")
    print("-" * 60)
    print("  Strategy: Buy AAPL Feb ATM put, Sell Feb 5% OTM put")
    print("  Max loss: Premium paid")
    print("  Max gain: Spread width minus premium")
    print("  Breakeven: Strike minus premium")
    print()

    print("OPTION C: POST-EARNINGS LONG (Buyback Resumption)")
    print("-" * 60)
    print("  Strategy: Wait until Jan 31, go long AAPL")
    print("  Entry: After blackout ends (Jan 31)")
    print("  Exit: 10-20 trading days later")
    print("  Rationale: Buybacks resume, providing support")

    # Best recovery window
    if len(recovery_df) > 0:
        best_window = None
        best_excess = -999
        for col in recovery_df.columns:
            if '_excess' in col:
                avg = recovery_df[col].dropna().mean()
                if avg > best_excess:
                    best_excess = avg
                    best_window = col.replace('_excess', '')

        if best_window:
            print(f"  Best historical window: {best_window} ({best_excess:+.2f}% avg excess)")
    print()

    print("RISK FACTORS:")
    print("-" * 60)
    print("  - Sample size is small (11-14 January cycles)")
    print("  - p-value = 0.507 (NOT statistically significant)")
    print("  - Strong earnings guidance could invalidate thesis")
    print("  - iPhone cycle timing affects results")
    print("  - Macro environment (rates, growth) matters")
    print()

    print("POSITION SIZING RECOMMENDATION:")
    print("-" * 60)
    print("  Given lack of statistical significance:")
    print("  - Maximum 2-3% of portfolio")
    print("  - Use defined-risk structures (spreads)")
    print("  - Consider this a 'tilted bet' not a 'sure thing'")


# ============================================
# VISUALIZATION
# ============================================

def create_january_visualizations(regime_df, segment_stats, recovery_df):
    """Create visualizations for January deep dive."""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Chart 1: Regime Effect
    ax1 = axes[0, 0]
    if len(regime_df) > 0:
        # Bar chart by momentum regime
        weak = regime_df[regime_df['aapl_pre_momentum'] < 0]['excess_return'].mean()
        strong = regime_df[regime_df['aapl_pre_momentum'] >= 0]['excess_return'].mean()

        bars = ax1.bar(['Negative Momentum', 'Positive Momentum'], [weak, strong],
                       color=['red' if weak < 0 else 'green', 'red' if strong < 0 else 'green'])
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.axhline(y=-2.02, color='blue', linestyle='--', label='Overall Avg (-2.02%)')
        ax1.set_ylabel('Excess Return (%)')
        ax1.set_title('January Excess Return by Pre-Blackout Momentum')
        ax1.legend()

    # Chart 2: Intra-Blackout Timing
    ax2 = axes[0, 1]
    if segment_stats:
        segments = [s['segment'].replace('_', '\n') for s in segment_stats]
        excess_returns = [s['avg_excess'] for s in segment_stats]
        colors = ['red' if r < 0 else 'green' for r in excess_returns]

        ax2.bar(segments, excess_returns, color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_ylabel('Avg Excess Return (%)')
        ax2.set_title('January Blackout: When Does Weakness Occur?')

    # Chart 3: Post-Earnings Recovery
    ax3 = axes[1, 0]
    if len(recovery_df) > 0:
        windows = ['2_day', '5_day', '10_day', '15_day', '20_day', '1_month']
        window_labels = ['2d', '5d', '10d', '15d', '20d', '30d']
        excess_means = [recovery_df[f'{w}_excess'].dropna().mean() for w in windows]
        colors = ['green' if r > 0 else 'red' for r in excess_means]

        ax3.bar(window_labels, excess_means, color=colors, alpha=0.7)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax3.set_xlabel('Days After Earnings')
        ax3.set_ylabel('Avg Excess Return (%)')
        ax3.set_title('Post-January Earnings Recovery')

    # Chart 4: Historical January Results
    ax4 = axes[1, 1]
    if len(regime_df) > 0:
        dates = regime_df['earnings_date']
        excess = regime_df['excess_return']
        colors = ['red' if r < 0 else 'green' for r in excess]

        x_pos = range(len(dates))
        ax4.bar(x_pos, excess, color=colors, alpha=0.7)
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels([d.strftime('%Y') for d in dates], rotation=45)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.axhline(y=excess.mean(), color='blue', linestyle='--',
                   label=f'Avg: {excess.mean():+.2f}%')
        ax4.set_ylabel('Excess Return (%)')
        ax4.set_title('January Blackout Excess Returns by Year')
        ax4.legend()

    plt.tight_layout()
    plt.savefig('january_deep_dive_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\nVisualization saved to 'january_deep_dive_analysis.png'")


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 80)
    print("APPLE JANUARY BLACKOUT DEEP DIVE ANALYSIS")
    print("=" * 80)
    print()
    print("This analysis drills deeper into January earnings blackout patterns.")
    print(f"January earnings dates analyzed: {len(JANUARY_EARNINGS)}")
    print()

    # 1. Load data
    aapl, spy = load_data()

    # 2. Run regime analysis
    regime_df = analyze_regime_effect(aapl, spy, JANUARY_EARNINGS)

    # 3. Run intra-blackout timing analysis
    all_segments, segment_stats = analyze_intra_blackout_timing(aapl, spy, JANUARY_EARNINGS)

    # 4. Run post-earnings recovery analysis
    recovery_df = analyze_post_earnings_recovery(aapl, spy, JANUARY_EARNINGS)

    # 5. Generate current setup scorecard
    scorecard = generate_current_setup_scorecard(aapl, spy)

    # 6. Generate trade recommendations
    generate_trade_recommendation(scorecard, regime_df, recovery_df)

    # 7. Create visualizations
    try:
        create_january_visualizations(regime_df, segment_stats, recovery_df)
    except Exception as e:
        print(f"\nVisualization error: {e}")

    # 8. Save results
    regime_df.to_csv('january_regime_analysis.csv', index=False)
    recovery_df.to_csv('january_recovery_analysis.csv', index=False)
    pd.DataFrame(segment_stats).to_csv('january_segment_analysis.csv', index=False)

    print("\n" + "=" * 80)
    print("RESULTS SAVED")
    print("=" * 80)
    print("  - january_regime_analysis.csv")
    print("  - january_recovery_analysis.csv")
    print("  - january_segment_analysis.csv")
    print("  - january_deep_dive_analysis.png")

    return regime_df, recovery_df, segment_stats, scorecard


if __name__ == "__main__":
    main()
