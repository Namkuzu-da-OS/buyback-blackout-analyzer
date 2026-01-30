#!/usr/bin/env python3
"""
Buyback Blackout Period Analyzer
================================
A generic tool for analyzing stock performance during buyback blackout periods.

Thesis: When major buyback programs pause during blackout periods (5 weeks before
earnings through 2 days after), stocks may underperform due to reduced demand.
The weakness is typically front-loaded, creating buying opportunities in late blackout.

Usage:
    python buyback_analyzer.py --ticker AAPL
    python buyback_analyzer.py --ticker GOOGL --benchmark QQQ
    python buyback_analyzer.py --ticker META --start-date 2015-01-01
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# =============================================================================
# CONFIGURATION
# =============================================================================

# Blackout period parameters
BLACKOUT_DAYS_BEFORE = 35  # 5 weeks before earnings
BLACKOUT_DAYS_AFTER = 2    # 2 trading days after earnings
POST_BLACKOUT_DAYS = 20    # Days to track post-blackout recovery

# Analysis parameters
MIN_PERIODS_FOR_ANALYSIS = 4  # Minimum periods needed for statistical tests


# =============================================================================
# EARNINGS DATABASE
# =============================================================================

# Major buyback stocks with historical earnings dates
# Format: 'TICKER': [list of earnings dates as 'YYYY-MM-DD']

EARNINGS_DATABASE = {
    'AAPL': [
        # 2026
        '2026-01-29',
        # 2025
        '2025-10-30', '2025-07-31', '2025-05-01', '2025-01-30',
        # 2024
        '2024-10-31', '2024-08-01', '2024-05-02', '2024-02-01',
        # 2023
        '2023-11-02', '2023-08-03', '2023-05-04', '2023-02-02',
        # 2022
        '2022-10-27', '2022-07-28', '2022-04-28', '2022-01-27',
        # 2021
        '2021-10-28', '2021-07-27', '2021-04-28', '2021-01-27',
        # 2020
        '2020-10-29', '2020-07-30', '2020-04-30', '2020-01-28',
        # 2019
        '2019-10-30', '2019-07-30', '2019-04-30', '2019-01-29',
        # 2018
        '2018-11-01', '2018-07-31', '2018-05-01', '2018-02-01',
        # 2017
        '2017-11-02', '2017-08-01', '2017-05-02', '2017-01-31',
        # 2016
        '2016-10-25', '2016-07-26', '2016-04-26', '2016-01-26',
        # 2015
        '2015-10-27', '2015-07-21', '2015-04-27', '2015-01-27',
        # 2014
        '2014-10-20', '2014-07-22', '2014-04-23', '2014-01-27',
        # 2013
        '2013-10-28', '2013-07-23', '2013-04-23', '2013-01-23',
        # 2012
        '2012-10-25', '2012-07-24', '2012-04-24',
    ],

    'GOOGL': [
        # 2026
        '2026-02-04',
        # 2025
        '2025-10-29', '2025-07-29', '2025-04-24', '2025-02-04',
        # 2024
        '2024-10-29', '2024-07-23', '2024-04-25', '2024-01-30',
        # 2023
        '2023-10-24', '2023-07-25', '2023-04-25', '2023-02-02',
        # 2022
        '2022-10-25', '2022-07-26', '2022-04-26', '2022-02-01',
        # 2021
        '2021-10-26', '2021-07-27', '2021-04-27', '2021-02-02',
        # 2020
        '2020-10-29', '2020-07-30', '2020-04-28', '2020-02-03',
        # 2019
        '2019-10-28', '2019-07-25', '2019-04-29', '2019-02-04',
        # 2018
        '2018-10-25', '2018-07-23', '2018-04-23', '2018-02-01',
        # 2017
        '2017-10-26', '2017-07-24', '2017-04-27', '2017-01-26',
        # 2016
        '2016-10-27', '2016-07-28', '2016-04-21', '2016-02-01',
        # 2015
        '2015-10-22', '2015-07-16', '2015-04-23', '2015-01-29',
    ],

    'META': [
        # 2026
        '2026-01-29',
        # 2025
        '2025-10-29', '2025-07-30', '2025-04-30', '2025-01-29',
        # 2024
        '2024-10-30', '2024-07-31', '2024-04-24', '2024-02-01',
        # 2023
        '2023-10-25', '2023-07-26', '2023-04-26', '2023-02-01',
        # 2022
        '2022-10-26', '2022-07-27', '2022-04-27', '2022-02-02',
        # 2021
        '2021-10-25', '2021-07-28', '2021-04-28', '2021-01-27',
        # 2020
        '2020-10-29', '2020-07-30', '2020-04-29', '2020-01-29',
        # 2019
        '2019-10-30', '2019-07-24', '2019-04-24', '2019-01-30',
        # 2018
        '2018-10-30', '2018-07-25', '2018-04-25', '2018-01-31',
        # 2017
        '2017-11-01', '2017-07-26', '2017-05-03', '2017-02-01',
        # 2016
        '2016-11-02', '2016-07-27', '2016-04-27', '2016-01-27',
        # 2015
        '2015-11-04', '2015-07-29', '2015-04-22', '2015-01-28',
    ],

    'MSFT': [
        # 2026
        '2026-01-29',
        # 2025
        '2025-10-29', '2025-07-29', '2025-04-30', '2025-01-29',
        # 2024
        '2024-10-30', '2024-07-30', '2024-04-25', '2024-01-30',
        # 2023
        '2023-10-24', '2023-07-25', '2023-04-25', '2023-01-24',
        # 2022
        '2022-10-25', '2022-07-26', '2022-04-26', '2022-01-25',
        # 2021
        '2021-10-26', '2021-07-27', '2021-04-27', '2021-01-26',
        # 2020
        '2020-10-27', '2020-07-22', '2020-04-29', '2020-01-29',
        # 2019
        '2019-10-23', '2019-07-18', '2019-04-24', '2019-01-30',
        # 2018
        '2018-10-24', '2018-07-19', '2018-04-26', '2018-02-01',
        # 2017
        '2017-10-26', '2017-07-20', '2017-04-27', '2017-01-26',
        # 2016
        '2016-10-20', '2016-07-19', '2016-04-21', '2016-01-28',
        # 2015
        '2015-10-22', '2015-07-23', '2015-04-23', '2015-01-26',
    ],

    'NVDA': [
        # 2026
        '2026-02-26',
        # 2025
        '2025-11-20', '2025-08-28', '2025-05-28', '2025-02-26',
        # 2024
        '2024-11-20', '2024-08-28', '2024-05-22', '2024-02-21',
        # 2023
        '2023-11-21', '2023-08-23', '2023-05-24', '2023-02-22',
        # 2022
        '2022-11-16', '2022-08-24', '2022-05-25', '2022-02-16',
        # 2021
        '2021-11-17', '2021-08-18', '2021-05-26', '2021-02-24',
        # 2020
        '2020-11-18', '2020-08-19', '2020-05-21', '2020-02-13',
        # 2019
        '2019-11-14', '2019-08-15', '2019-05-16', '2019-02-14',
        # 2018
        '2018-11-15', '2018-08-16', '2018-05-10', '2018-02-08',
        # 2017
        '2017-11-09', '2017-08-10', '2017-05-09', '2017-02-09',
    ],

    'AMZN': [
        # 2026
        '2026-02-06',
        # 2025
        '2025-10-30', '2025-08-01', '2025-05-01', '2025-02-06',
        # 2024
        '2024-10-31', '2024-08-01', '2024-04-30', '2024-02-01',
        # 2023
        '2023-10-26', '2023-08-03', '2023-04-27', '2023-02-02',
        # 2022
        '2022-10-27', '2022-07-28', '2022-04-28', '2022-02-03',
        # 2021
        '2021-10-28', '2021-07-29', '2021-04-29', '2021-02-02',
        # 2020
        '2020-10-29', '2020-07-30', '2020-04-30', '2020-01-30',
        # 2019
        '2019-10-24', '2019-07-25', '2019-04-25', '2019-01-31',
        # 2018
        '2018-10-25', '2018-07-26', '2018-04-26', '2018-02-01',
        # 2017
        '2017-10-26', '2017-07-27', '2017-04-27', '2017-02-02',
    ],
}

# Buyback program info (billions USD, approximate annual)
BUYBACK_INFO = {
    'AAPL': {'annual_buyback': 90, 'program_start': 2012, 'cumulative': 650},
    'GOOGL': {'annual_buyback': 62, 'program_start': 2015, 'cumulative': 200},
    'META': {'annual_buyback': 40, 'program_start': 2017, 'cumulative': 120},
    'MSFT': {'annual_buyback': 35, 'program_start': 2013, 'cumulative': 150},
    'NVDA': {'annual_buyback': 25, 'program_start': 2020, 'cumulative': 50},
    'AMZN': {'annual_buyback': 10, 'program_start': 2022, 'cumulative': 20},
}


# =============================================================================
# CORE ANALYSIS FUNCTIONS
# =============================================================================

def get_earnings_dates(ticker: str, custom_dates: List[str] = None) -> List[str]:
    """Get earnings dates for a ticker from database or custom list."""
    if custom_dates:
        return sorted(custom_dates, reverse=True)

    if ticker.upper() in EARNINGS_DATABASE:
        return EARNINGS_DATABASE[ticker.upper()]

    # Try to fetch from yfinance if not in database
    print(f"[WARNING] {ticker} not in earnings database. Attempting to fetch from yfinance...")
    try:
        stock = yf.Ticker(ticker)
        calendar = stock.calendar
        if calendar is not None and 'Earnings Date' in calendar:
            dates = calendar['Earnings Date']
            if isinstance(dates, list) and len(dates) > 0:
                return [d.strftime('%Y-%m-%d') for d in dates]
    except Exception as e:
        print(f"[ERROR] Could not fetch earnings dates: {e}")

    return []


def download_price_data(ticker: str, benchmark: str, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Download price data for stock and benchmark."""
    print(f"Downloading price data for {ticker} and {benchmark}...")

    stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    benchmark_data = yf.download(benchmark, start=start_date, end=end_date, progress=False)

    if stock_data.empty:
        raise ValueError(f"No data found for {ticker}")
    if benchmark_data.empty:
        raise ValueError(f"No data found for {benchmark}")

    # Flatten MultiIndex columns if present
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = stock_data.columns.get_level_values(0)
    if isinstance(benchmark_data.columns, pd.MultiIndex):
        benchmark_data.columns = benchmark_data.columns.get_level_values(0)

    print(f"  {ticker}: {len(stock_data)} trading days")
    print(f"  {benchmark}: {len(benchmark_data)} trading days")

    return stock_data, benchmark_data


def calculate_blackout_windows(earnings_dates: List[str]) -> List[Dict]:
    """Calculate blackout windows for each earnings date."""
    windows = []

    for earnings_date_str in earnings_dates:
        earnings_date = pd.to_datetime(earnings_date_str)
        blackout_start = earnings_date - timedelta(days=BLACKOUT_DAYS_BEFORE)
        blackout_end = earnings_date + timedelta(days=BLACKOUT_DAYS_AFTER)

        windows.append({
            'earnings_date': earnings_date,
            'blackout_start': blackout_start,
            'blackout_end': blackout_end,
        })

    return windows


def calculate_period_returns(stock_data: pd.DataFrame, benchmark_data: pd.DataFrame,
                            start_date: pd.Timestamp, end_date: pd.Timestamp) -> Dict:
    """Calculate returns for stock and benchmark over a period."""
    # Find valid trading days
    stock_mask = (stock_data.index >= start_date) & (stock_data.index <= end_date)
    benchmark_mask = (benchmark_data.index >= start_date) & (benchmark_data.index <= end_date)

    stock_period = stock_data[stock_mask]
    benchmark_period = benchmark_data[benchmark_mask]

    if len(stock_period) < 2 or len(benchmark_period) < 2:
        return None

    # Calculate total returns
    stock_return = (stock_period['Adj Close'].iloc[-1] / stock_period['Adj Close'].iloc[0] - 1) * 100
    benchmark_return = (benchmark_period['Adj Close'].iloc[-1] / benchmark_period['Adj Close'].iloc[0] - 1) * 100
    excess_return = stock_return - benchmark_return

    return {
        'stock_return': stock_return,
        'benchmark_return': benchmark_return,
        'excess_return': excess_return,
        'trading_days': len(stock_period),
    }


def analyze_blackout_periods(stock_data: pd.DataFrame, benchmark_data: pd.DataFrame,
                            earnings_dates: List[str], ticker: str, benchmark: str) -> pd.DataFrame:
    """Analyze all blackout periods and return results DataFrame."""
    windows = calculate_blackout_windows(earnings_dates)
    results = []

    for window in windows:
        returns = calculate_period_returns(
            stock_data, benchmark_data,
            window['blackout_start'], window['blackout_end']
        )

        if returns is None:
            continue

        # Get earnings month for seasonality analysis
        earnings_month = window['earnings_date'].month
        earnings_year = window['earnings_date'].year

        results.append({
            'earnings_date': window['earnings_date'],
            'blackout_start': window['blackout_start'],
            'blackout_end': window['blackout_end'],
            'earnings_month': earnings_month,
            'earnings_year': earnings_year,
            f'{ticker.lower()}_return': returns['stock_return'],
            f'{benchmark.lower()}_return': returns['benchmark_return'],
            'excess_return': returns['excess_return'],
            'trading_days': returns['trading_days'],
            'underperformed': returns['excess_return'] < 0,
        })

    return pd.DataFrame(results)


def analyze_post_blackout(stock_data: pd.DataFrame, benchmark_data: pd.DataFrame,
                         earnings_dates: List[str], ticker: str, benchmark: str) -> pd.DataFrame:
    """Analyze post-blackout recovery periods."""
    windows = calculate_blackout_windows(earnings_dates)
    results = []
    recovery_windows = [2, 5, 10, 15, 20]

    for window in windows:
        post_start = window['blackout_end'] + timedelta(days=1)

        row = {
            'earnings_date': window['earnings_date'],
        }

        for days in recovery_windows:
            post_end = post_start + timedelta(days=days + 5)  # Buffer for weekends
            returns = calculate_period_returns(stock_data, benchmark_data, post_start, post_end)

            if returns:
                row[f'{days}_day_excess'] = returns['excess_return']
            else:
                row[f'{days}_day_excess'] = None

        results.append(row)

    return pd.DataFrame(results)


def analyze_by_month(results_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Analyze results grouped by earnings month."""
    monthly = results_df.groupby('earnings_month').agg({
        'excess_return': ['mean', 'std', 'count'],
        'underperformed': 'mean',
    }).round(4)

    monthly.columns = ['avg_excess', 'std_excess', 'count', 'underperf_rate']
    monthly['underperf_rate'] = monthly['underperf_rate'] * 100

    # Calculate p-values
    p_values = []
    for month in monthly.index:
        month_data = results_df[results_df['earnings_month'] == month]['excess_return']
        if len(month_data) >= MIN_PERIODS_FOR_ANALYSIS:
            _, p_value = stats.ttest_1samp(month_data, 0)
        else:
            p_value = None
        p_values.append(p_value)

    monthly['p_value'] = p_values
    monthly['significant'] = monthly['p_value'].apply(lambda x: x < 0.05 if x else False)

    # Add month names
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                   5: 'May', 6: 'June', 7: 'July', 8: 'August',
                   9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    monthly['month_name'] = monthly.index.map(month_names)

    return monthly


def analyze_by_year(results_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Analyze results grouped by year."""
    yearly = results_df.groupby('earnings_year').agg({
        'excess_return': ['mean', 'std', 'count'],
        'underperformed': 'mean',
    }).round(4)

    yearly.columns = ['avg_excess', 'std_excess', 'count', 'underperf_rate']
    yearly['underperf_rate'] = yearly['underperf_rate'] * 100

    return yearly


def calculate_intra_blackout_timing(stock_data: pd.DataFrame, benchmark_data: pd.DataFrame,
                                   earnings_dates: List[str], target_month: int = None) -> pd.DataFrame:
    """Analyze returns within different segments of the blackout period."""
    windows = calculate_blackout_windows(earnings_dates)

    segments = {
        'early': (1, 14),
        'mid': (15, 28),
        'late': (29, 35),
    }

    results = []

    for window in windows:
        if target_month and window['earnings_date'].month != target_month:
            continue

        row = {'earnings_date': window['earnings_date']}

        for seg_name, (start_day, end_day) in segments.items():
            seg_start = window['blackout_start'] + timedelta(days=start_day - 1)
            seg_end = window['blackout_start'] + timedelta(days=end_day)

            returns = calculate_period_returns(stock_data, benchmark_data, seg_start, seg_end)

            if returns:
                row[f'{seg_name}_excess'] = returns['excess_return']
            else:
                row[f'{seg_name}_excess'] = None

        results.append(row)

    return pd.DataFrame(results)


def classify_market_regime(stock_data: pd.DataFrame, blackout_start: pd.Timestamp) -> Dict:
    """Classify market regime at the start of blackout."""
    # Get data for regime classification
    lookback_start = blackout_start - timedelta(days=60)
    regime_data = stock_data[(stock_data.index >= lookback_start) & (stock_data.index < blackout_start)]

    if len(regime_data) < 20:
        return {'regime': 'unknown', 'details': {}}

    current_price = regime_data['Adj Close'].iloc[-1]

    # Calculate metrics
    ma_50 = regime_data['Adj Close'].tail(50).mean() if len(regime_data) >= 50 else regime_data['Adj Close'].mean()
    ma_200 = regime_data['Adj Close'].tail(200).mean() if len(regime_data) >= 200 else regime_data['Adj Close'].mean()

    # 52-week high (approximate with available data)
    high_52w = stock_data[(stock_data.index >= blackout_start - timedelta(days=365)) &
                          (stock_data.index < blackout_start)]['High'].max()
    pct_from_high = ((current_price / high_52w) - 1) * 100 if high_52w else 0

    # Pre-blackout momentum (30-day return)
    if len(regime_data) >= 30:
        momentum = ((regime_data['Adj Close'].iloc[-1] / regime_data['Adj Close'].iloc[-30]) - 1) * 100
    else:
        momentum = 0

    # Classify regime
    is_weak = (current_price < ma_50) or (pct_from_high < -10) or (momentum < -5)

    return {
        'regime': 'weak' if is_weak else 'strong',
        'details': {
            'above_50ma': current_price > ma_50,
            'above_200ma': current_price > ma_200,
            'pct_from_high': pct_from_high,
            'momentum_30d': momentum,
        }
    }


def analyze_by_regime(stock_data: pd.DataFrame, benchmark_data: pd.DataFrame,
                     results_df: pd.DataFrame, target_month: int = None) -> pd.DataFrame:
    """Analyze results grouped by market regime."""
    regime_results = []

    for _, row in results_df.iterrows():
        if target_month and row['earnings_month'] != target_month:
            continue

        regime = classify_market_regime(stock_data, row['blackout_start'])

        regime_results.append({
            'earnings_date': row['earnings_date'],
            'excess_return': row['excess_return'],
            'regime': regime['regime'],
            **regime['details']
        })

    return pd.DataFrame(regime_results)


def get_current_setup(stock_data: pd.DataFrame, benchmark_data: pd.DataFrame,
                     ticker: str, benchmark: str, earnings_date: str) -> Dict:
    """Get current setup information for an ongoing blackout period."""
    earnings_dt = pd.to_datetime(earnings_date)
    blackout_start = earnings_dt - timedelta(days=BLACKOUT_DAYS_BEFORE)
    blackout_end = earnings_dt + timedelta(days=BLACKOUT_DAYS_AFTER)

    current_date = stock_data.index[-1]

    # Check if we're in a blackout period
    if current_date < blackout_start:
        return {'status': 'pre_blackout', 'message': f'Blackout starts {blackout_start.date()}'}
    if current_date > blackout_end:
        return {'status': 'post_blackout', 'message': f'Blackout ended {blackout_end.date()}'}

    # Calculate current progress
    days_elapsed = (current_date - blackout_start).days
    total_days = BLACKOUT_DAYS_BEFORE + BLACKOUT_DAYS_AFTER
    progress_pct = (days_elapsed / total_days) * 100

    # Calculate returns so far
    returns = calculate_period_returns(stock_data, benchmark_data, blackout_start, current_date)

    # Get current regime
    regime = classify_market_regime(stock_data, blackout_start)

    # Determine current phase
    if days_elapsed <= 14:
        phase = 'early_blackout'
    elif days_elapsed <= 28:
        phase = 'mid_blackout'
    else:
        phase = 'late_blackout'

    return {
        'status': 'in_blackout',
        'ticker': ticker,
        'benchmark': benchmark,
        'earnings_date': earnings_date,
        'blackout_start': blackout_start.strftime('%Y-%m-%d'),
        'blackout_end': blackout_end.strftime('%Y-%m-%d'),
        'current_date': current_date.strftime('%Y-%m-%d'),
        'current_day': days_elapsed,
        'total_days': total_days,
        'progress_pct': round(progress_pct, 1),
        'phase': phase,
        'stock_return': round(returns['stock_return'], 2) if returns else None,
        'benchmark_return': round(returns['benchmark_return'], 2) if returns else None,
        'excess_return': round(returns['excess_return'], 2) if returns else None,
        'regime': regime['regime'],
        'regime_details': regime['details'],
    }


# =============================================================================
# REPORTING FUNCTIONS
# =============================================================================

def generate_summary_stats(results_df: pd.DataFrame, ticker: str, benchmark: str) -> Dict:
    """Generate summary statistics for the analysis."""
    excess_returns = results_df['excess_return'].dropna()

    if len(excess_returns) < MIN_PERIODS_FOR_ANALYSIS:
        return {'error': f'Insufficient data ({len(excess_returns)} periods)'}

    t_stat, p_value = stats.ttest_1samp(excess_returns, 0)

    return {
        'ticker': ticker,
        'benchmark': benchmark,
        'total_periods': len(results_df),
        'avg_stock_return': round(results_df[f'{ticker.lower()}_return'].mean(), 2),
        'avg_benchmark_return': round(results_df[f'{benchmark.lower()}_return'].mean(), 2),
        'avg_excess_return': round(excess_returns.mean(), 2),
        'std_excess_return': round(excess_returns.std(), 2),
        'underperformance_rate': round(results_df['underperformed'].mean() * 100, 1),
        't_statistic': round(t_stat, 4),
        'p_value': round(p_value, 4),
        'significant': p_value < 0.05,
    }


def create_visualization(results_df: pd.DataFrame, monthly_df: pd.DataFrame,
                        yearly_df: pd.DataFrame, ticker: str, benchmark: str,
                        output_dir: str):
    """Create visualization charts."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'{ticker} Buyback Blackout Period Analysis', fontsize=14, fontweight='bold')

    # Chart 1: Excess returns over time
    ax1 = axes[0, 0]
    colors = ['green' if x > 0 else 'red' for x in results_df['excess_return']]
    ax1.bar(range(len(results_df)), results_df['excess_return'], color=colors, alpha=0.7)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.axhline(y=results_df['excess_return'].mean(), color='blue', linestyle='--',
                label=f'Avg: {results_df["excess_return"].mean():.2f}%')
    ax1.set_xlabel('Period')
    ax1.set_ylabel('Excess Return (%)')
    ax1.set_title(f'{ticker} vs {benchmark} Excess Return by Period')
    ax1.legend()

    # Chart 2: Monthly performance
    ax2 = axes[0, 1]
    monthly_sorted = monthly_df.sort_values('avg_excess')
    colors = ['green' if x > 0 else 'red' for x in monthly_sorted['avg_excess']]
    bars = ax2.barh(monthly_sorted['month_name'], monthly_sorted['avg_excess'], color=colors, alpha=0.7)
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_xlabel('Average Excess Return (%)')
    ax2.set_title('Average Excess Return by Earnings Month')

    # Highlight significant months
    for i, (idx, row) in enumerate(monthly_sorted.iterrows()):
        if row['significant']:
            ax2.annotate('*', xy=(row['avg_excess'], i), fontsize=14, color='blue')

    # Chart 3: Yearly performance
    ax3 = axes[1, 0]
    colors = ['green' if x > 0 else 'red' for x in yearly_df['avg_excess']]
    ax3.bar(yearly_df.index, yearly_df['avg_excess'], color=colors, alpha=0.7)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax3.set_xlabel('Year')
    ax3.set_ylabel('Average Excess Return (%)')
    ax3.set_title('Average Excess Return by Year')
    ax3.tick_params(axis='x', rotation=45)

    # Chart 4: Distribution
    ax4 = axes[1, 1]
    ax4.hist(results_df['excess_return'], bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    ax4.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero')
    ax4.axvline(x=results_df['excess_return'].mean(), color='green', linestyle='--',
                linewidth=2, label=f'Mean: {results_df["excess_return"].mean():.2f}%')
    ax4.set_xlabel('Excess Return (%)')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Distribution of Excess Returns')
    ax4.legend()

    plt.tight_layout()

    output_path = os.path.join(output_dir, f'{ticker.lower()}_blackout_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  Chart saved: {output_path}")


def save_results(results_df: pd.DataFrame, monthly_df: pd.DataFrame, yearly_df: pd.DataFrame,
                post_blackout_df: pd.DataFrame, summary: Dict, ticker: str, output_dir: str):
    """Save all results to CSV and JSON files."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Save DataFrames
    results_df.to_csv(os.path.join(output_dir, f'{ticker.lower()}_blackout_results.csv'), index=False)
    monthly_df.to_csv(os.path.join(output_dir, f'{ticker.lower()}_monthly_analysis.csv'))
    yearly_df.to_csv(os.path.join(output_dir, f'{ticker.lower()}_yearly_analysis.csv'))
    post_blackout_df.to_csv(os.path.join(output_dir, f'{ticker.lower()}_post_blackout.csv'), index=False)

    # Save summary as JSON
    summary_path = os.path.join(output_dir, f'{ticker.lower()}_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"  Results saved to: {output_dir}")


def print_report(summary: Dict, monthly_df: pd.DataFrame, results_df: pd.DataFrame,
                ticker: str, benchmark: str):
    """Print analysis report to console."""
    print("\n" + "="*70)
    print(f"  {ticker} BUYBACK BLACKOUT ANALYSIS REPORT")
    print("="*70)

    print(f"\n  Benchmark: {benchmark}")
    print(f"  Total Periods Analyzed: {summary['total_periods']}")
    print(f"  Average {ticker} Return: {summary['avg_stock_return']:.2f}%")
    print(f"  Average {benchmark} Return: {summary['avg_benchmark_return']:.2f}%")
    print(f"  Average Excess Return: {summary['avg_excess_return']:.2f}%")
    print(f"  Underperformance Rate: {summary['underperformance_rate']:.1f}%")
    print(f"  P-value: {summary['p_value']:.4f}")
    print(f"  Statistically Significant: {'YES' if summary['significant'] else 'No'}")

    if summary['avg_excess_return'] < 0:
        print(f"\n  >>> THESIS SUPPORTED: {ticker} tends to underperform during blackout")
    else:
        print(f"\n  >>> THESIS NOT SUPPORTED: {ticker} tends to outperform during blackout")

    print("\n" + "-"*70)
    print("  PERFORMANCE BY EARNINGS MONTH")
    print("-"*70)
    print(f"  {'Month':<12} {'Count':>6} {'Avg Excess':>12} {'Underperf%':>12} {'P-value':>10} {'Sig?':>6}")
    print("  " + "-"*60)

    for idx, row in monthly_df.iterrows():
        sig = "*" if row['significant'] else ""
        p_val = f"{row['p_value']:.3f}" if pd.notna(row['p_value']) else "N/A"
        print(f"  {row['month_name']:<12} {int(row['count']):>6} {row['avg_excess']:>11.2f}% {row['underperf_rate']:>11.1f}% {p_val:>10} {sig:>6}")

    print("\n" + "="*70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_analysis(ticker: str, benchmark: str = 'SPY', start_date: str = None,
                end_date: str = None, output_dir: str = None, earnings_dates: List[str] = None) -> Dict:
    """Run complete blackout period analysis for a stock."""

    ticker = ticker.upper()
    benchmark = benchmark.upper()

    # Set defaults
    if not start_date:
        start_date = '2012-01-01'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(__file__), ticker.lower())

    print(f"\n{'='*70}")
    print(f"  BUYBACK BLACKOUT ANALYZER")
    print(f"  Stock: {ticker} | Benchmark: {benchmark}")
    print(f"  Period: {start_date} to {end_date}")
    print(f"{'='*70}\n")

    # Get earnings dates
    earnings = get_earnings_dates(ticker, earnings_dates)
    if not earnings:
        return {'error': f'No earnings dates found for {ticker}'}

    print(f"Found {len(earnings)} earnings dates")

    # Download data
    stock_data, benchmark_data = download_price_data(ticker, benchmark, start_date, end_date)

    # Run analyses
    print("\nAnalyzing blackout periods...")
    results_df = analyze_blackout_periods(stock_data, benchmark_data, earnings, ticker, benchmark)

    if len(results_df) == 0:
        return {'error': 'No valid blackout periods found in date range'}

    print(f"  Analyzed {len(results_df)} blackout periods")

    # Monthly and yearly analysis
    monthly_df = analyze_by_month(results_df, ticker)
    yearly_df = analyze_by_year(results_df, ticker)

    # Post-blackout analysis
    print("Analyzing post-blackout recovery...")
    post_blackout_df = analyze_post_blackout(stock_data, benchmark_data, earnings, ticker, benchmark)

    # Generate summary
    summary = generate_summary_stats(results_df, ticker, benchmark)

    # Check for current setup
    next_earnings = earnings[0] if earnings else None
    if next_earnings:
        current_setup = get_current_setup(stock_data, benchmark_data, ticker, benchmark, next_earnings)
        summary['current_setup'] = current_setup

    # Add buyback info if available
    if ticker in BUYBACK_INFO:
        summary['buyback_info'] = BUYBACK_INFO[ticker]

    # Print report
    print_report(summary, monthly_df, results_df, ticker, benchmark)

    # Save results
    print("\nSaving results...")
    save_results(results_df, monthly_df, yearly_df, post_blackout_df, summary, ticker, output_dir)

    # Create visualization
    print("Creating visualization...")
    create_visualization(results_df, monthly_df, yearly_df, ticker, benchmark, output_dir)

    print("\n" + "="*70)
    print("  ANALYSIS COMPLETE")
    print("="*70 + "\n")

    return {
        'summary': summary,
        'results': results_df,
        'monthly': monthly_df,
        'yearly': yearly_df,
        'post_blackout': post_blackout_df,
        'output_dir': output_dir,
    }


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Analyze stock performance during buyback blackout periods',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python buyback_analyzer.py --ticker AAPL
  python buyback_analyzer.py --ticker GOOGL --benchmark QQQ
  python buyback_analyzer.py --ticker META --start-date 2018-01-01
  python buyback_analyzer.py --list-stocks
        """
    )

    parser.add_argument('--ticker', '-t', type=str, help='Stock ticker to analyze')
    parser.add_argument('--benchmark', '-b', type=str, default='SPY', help='Benchmark ticker (default: SPY)')
    parser.add_argument('--start-date', '-s', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', '-e', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', '-o', type=str, help='Output directory')
    parser.add_argument('--list-stocks', action='store_true', help='List available stocks in database')

    args = parser.parse_args()

    if args.list_stocks:
        print("\nStocks in earnings database:")
        print("-" * 50)
        for ticker in sorted(EARNINGS_DATABASE.keys()):
            info = BUYBACK_INFO.get(ticker, {})
            annual = info.get('annual_buyback', '?')
            count = len(EARNINGS_DATABASE[ticker])
            print(f"  {ticker:<8} {count:>3} earnings dates | ~${annual}B annual buyback")
        print()
        return

    if not args.ticker:
        parser.print_help()
        return

    run_analysis(
        ticker=args.ticker,
        benchmark=args.benchmark,
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=args.output_dir,
    )


if __name__ == '__main__':
    main()
