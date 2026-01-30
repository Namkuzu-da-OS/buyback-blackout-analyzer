"""
blackout_analysis_generic.py
Generic Buyback Blackout Period Analysis

USAGE:
    1. Edit the CONFIGURATION section below
    2. Run: python blackout_analysis_generic.py

Analyzes whether a stock underperforms during buyback blackout periods
compared to a benchmark index.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
import matplotlib.pyplot as plt
import warnings
import sys

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURATION - EDIT THIS SECTION
# ============================================

# Target stock ticker
STOCK_TICKER = "AAPL"

# Benchmark ticker (SPY, QQQ, IWM, etc.)
BENCHMARK_TICKER = "SPY"

# Data range
START_DATE = "2012-01-01"
END_DATE = "2026-01-17"

# Blackout window parameters (in calendar days)
BLACKOUT_DAYS_BEFORE = 35  # 5 weeks before earnings
BLACKOUT_DAYS_AFTER = 2    # 2 trading days after earnings
POST_BLACKOUT_DAYS = 10    # Recovery window analysis

# Earnings dates - REPLACE WITH YOUR TARGET COMPANY'S DATES
# Format: "YYYY-MM-DD"
EARNINGS_DATES = [
    # 2026
    "2026-01-29",
    # 2025
    "2025-10-30",
    "2025-07-31",
    "2025-05-01",
    "2025-01-30",
    # 2024
    "2024-10-31",
    "2024-08-01",
    "2024-05-02",
    "2024-02-01",
    # 2023
    "2023-11-02",
    "2023-08-03",
    "2023-05-04",
    "2023-02-02",
    # 2022
    "2022-10-27",
    "2022-07-28",
    "2022-04-28",
    "2022-01-27",
    # 2021
    "2021-10-28",
    "2021-07-27",
    "2021-04-28",
    "2021-01-27",
    # 2020
    "2020-10-29",
    "2020-07-30",
    "2020-04-30",
    "2020-01-28",
    # 2019
    "2019-10-30",
    "2019-07-30",
    "2019-04-30",
    "2019-01-29",
    # 2018
    "2018-11-01",
    "2018-07-31",
    "2018-05-01",
    "2018-02-01",
    # 2017
    "2017-11-02",
    "2017-08-01",
    "2017-05-02",
    "2017-01-31",
    # 2016
    "2016-10-25",
    "2016-07-26",
    "2016-04-26",
    "2016-01-26",
    # 2015
    "2015-10-27",
    "2015-07-21",
    "2015-04-27",
    "2015-01-27",
    # 2014
    "2014-10-20",
    "2014-07-22",
    "2014-04-23",
    "2014-01-27",
    # 2013
    "2013-10-28",
    "2013-07-23",
    "2013-04-23",
    "2013-01-23",
    # 2012
    "2012-10-25",
    "2012-07-24",
    "2012-04-24",
]

# ============================================
# END CONFIGURATION
# ============================================


def load_data():
    """Download stock and benchmark price data."""
    print(f"Downloading {STOCK_TICKER} and {BENCHMARK_TICKER} data...")

    stock = yf.download(STOCK_TICKER, start=START_DATE, end=END_DATE, progress=False)
    benchmark = yf.download(BENCHMARK_TICKER, start=START_DATE, end=END_DATE, progress=False)

    # Flatten multi-index columns if present
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    if isinstance(benchmark.columns, pd.MultiIndex):
        benchmark.columns = benchmark.columns.get_level_values(0)

    print(f"  {STOCK_TICKER}: {len(stock)} trading days ({stock.index.min().date()} to {stock.index.max().date()})")
    print(f"  {BENCHMARK_TICKER}: {len(benchmark)} trading days ({benchmark.index.min().date()} to {benchmark.index.max().date()})")

    return stock, benchmark


def get_blackout_window(earnings_date_str):
    """Returns (blackout_start, blackout_end) for a given earnings date."""
    earnings_date = pd.to_datetime(earnings_date_str)
    blackout_start = earnings_date - timedelta(days=BLACKOUT_DAYS_BEFORE)
    blackout_end = earnings_date + timedelta(days=BLACKOUT_DAYS_AFTER)
    return blackout_start, blackout_end


def generate_blackout_windows(earnings_dates):
    """Create list of (start, end, earnings_date) tuples for each blackout period."""
    windows = []
    for date_str in earnings_dates:
        start, end = get_blackout_window(date_str)
        windows.append((start, end, pd.to_datetime(date_str)))
    return windows


def calculate_period_return(price_data, start_date, end_date):
    """Calculate total return between two dates."""
    price_col = 'Adj Close' if 'Adj Close' in price_data.columns else 'Close'
    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    period_data = price_data.loc[mask, price_col]

    if len(period_data) < 2:
        return np.nan

    start_price = period_data.iloc[0]
    end_price = period_data.iloc[-1]
    return (end_price / start_price - 1) * 100


def analyze_blackout_periods(stock_data, benchmark_data, windows):
    """Calculate returns during each blackout period."""
    results = []

    for start, end, earnings_date in windows:
        if start > stock_data.index.max():
            continue

        stock_return = calculate_period_return(stock_data, start, end)
        bench_return = calculate_period_return(benchmark_data, start, end)

        if pd.isna(stock_return) or pd.isna(bench_return):
            continue

        excess_return = stock_return - bench_return

        results.append({
            'earnings_date': earnings_date.date(),
            'blackout_start': start.date(),
            'blackout_end': end.date(),
            'stock_return': stock_return,
            'benchmark_return': bench_return,
            'excess_return': excess_return
        })

    return pd.DataFrame(results)


def analyze_post_blackout(stock_data, benchmark_data, windows):
    """Calculate returns after each blackout period."""
    results = []

    for start, end, earnings_date in windows:
        recovery_start = earnings_date + timedelta(days=3)
        recovery_end = earnings_date + timedelta(days=POST_BLACKOUT_DAYS + 5)

        if recovery_start > stock_data.index.max():
            continue

        stock_return = calculate_period_return(stock_data, recovery_start, recovery_end)
        bench_return = calculate_period_return(benchmark_data, recovery_start, recovery_end)

        if pd.isna(stock_return) or pd.isna(bench_return):
            continue

        results.append({
            'earnings_date': earnings_date.date(),
            'recovery_start': recovery_start.date(),
            'stock_return': stock_return,
            'benchmark_return': bench_return,
            'excess_return': stock_return - bench_return
        })

    return pd.DataFrame(results)


def is_in_blackout(date, windows):
    """Check if a date falls within any blackout window."""
    for start, end, _ in windows:
        if start <= date <= end:
            return True
    return False


def analyze_daily_returns(stock_data, benchmark_data, windows):
    """Classify each day and calculate daily excess returns."""
    price_col = 'Adj Close' if 'Adj Close' in stock_data.columns else 'Close'

    daily_data = pd.DataFrame(index=stock_data.index)
    daily_data['stock_return'] = stock_data[price_col].pct_change() * 100
    daily_data['benchmark_return'] = benchmark_data[price_col].pct_change() * 100
    daily_data['excess_return'] = daily_data['stock_return'] - daily_data['benchmark_return']
    daily_data['in_blackout'] = daily_data.index.map(lambda x: is_in_blackout(x, windows))

    return daily_data.dropna()


def run_statistical_tests(blackout_returns, non_blackout_returns):
    """Run t-test and Mann-Whitney U test."""
    results = {}

    t_stat, t_p_value = stats.ttest_ind(blackout_returns, non_blackout_returns)
    results['t_stat'] = t_stat
    results['t_p_value'] = t_p_value

    u_stat, u_p_value = stats.mannwhitneyu(
        blackout_returns,
        non_blackout_returns,
        alternative='two-sided'
    )
    results['u_stat'] = u_stat
    results['u_p_value'] = u_p_value

    return results


def analyze_by_month(blackout_results):
    """Analyze performance by earnings month."""
    if len(blackout_results) == 0:
        return pd.DataFrame()

    df = blackout_results.copy()
    df['earnings_month'] = pd.to_datetime(df['earnings_date']).dt.month
    df['earnings_month_name'] = pd.to_datetime(df['earnings_date']).dt.strftime('%B')

    monthly_stats = df.groupby(['earnings_month', 'earnings_month_name']).agg({
        'stock_return': ['mean', 'std', 'count'],
        'benchmark_return': ['mean', 'std'],
        'excess_return': ['mean', 'std', 'min', 'max']
    }).round(2)

    monthly_stats.columns = ['_'.join(col).strip() for col in monthly_stats.columns.values]
    monthly_stats = monthly_stats.reset_index()

    win_rates = df.groupby('earnings_month').apply(
        lambda x: (x['excess_return'] < 0).mean() * 100
    ).reset_index()
    win_rates.columns = ['earnings_month', 'underperf_rate']

    monthly_stats = monthly_stats.merge(win_rates, on='earnings_month')

    t_test_results = []
    for month in df['earnings_month'].unique():
        month_data = df[df['earnings_month'] == month]['excess_return']
        if len(month_data) >= 3:
            t_stat, p_val = stats.ttest_1samp(month_data, 0)
            t_test_results.append({'earnings_month': month, 't_stat': t_stat, 'p_value': p_val})
        else:
            t_test_results.append({'earnings_month': month, 't_stat': np.nan, 'p_value': np.nan})

    monthly_stats = monthly_stats.merge(pd.DataFrame(t_test_results), on='earnings_month')
    return monthly_stats.sort_values('earnings_month')


def analyze_by_year(blackout_results):
    """Analyze performance by year."""
    if len(blackout_results) == 0:
        return pd.DataFrame()

    df = blackout_results.copy()
    df['year'] = pd.to_datetime(df['earnings_date']).dt.year

    yearly_stats = df.groupby('year').agg({
        'stock_return': ['mean', 'count'],
        'benchmark_return': 'mean',
        'excess_return': ['mean', 'std', 'min', 'max']
    }).round(2)

    yearly_stats.columns = ['_'.join(col).strip() for col in yearly_stats.columns.values]
    yearly_stats = yearly_stats.reset_index()

    win_rates = df.groupby('year').apply(
        lambda x: (x['excess_return'] < 0).mean() * 100
    ).reset_index()
    win_rates.columns = ['year', 'underperf_rate']

    return yearly_stats.merge(win_rates, on='year')


def print_summary(blackout_results, post_blackout_results, daily_results, stats_results):
    """Print formatted summary statistics."""

    print("\n" + "=" * 60)
    print(f"BLACKOUT PERIOD ANALYSIS: {STOCK_TICKER} vs {BENCHMARK_TICKER}")
    print("=" * 60)

    if len(blackout_results) > 0:
        print(f"Total Blackout Periods Analyzed: {len(blackout_results)}")
        print(f"Average {STOCK_TICKER} Return During Blackout: {blackout_results['stock_return'].mean():.2f}%")
        print(f"Average {BENCHMARK_TICKER} Return During Blackout: {blackout_results['benchmark_return'].mean():.2f}%")
        print(f"Average {STOCK_TICKER} Excess Return: {blackout_results['excess_return'].mean():.2f}%")
        win_rate = (blackout_results['excess_return'] < 0).mean() * 100
        print(f"Underperformance Rate ({STOCK_TICKER} < {BENCHMARK_TICKER}): {win_rate:.1f}%")

    print("\n" + "=" * 60)
    print("DAILY RETURN ANALYSIS")
    print("=" * 60)

    blackout_days = daily_results[daily_results['in_blackout']]
    non_blackout_days = daily_results[~daily_results['in_blackout']]

    print(f"Days IN Blackout: {len(blackout_days)}")
    print(f"Days OUTSIDE Blackout: {len(non_blackout_days)}")
    print(f"Mean Daily Excess Return (Blackout): {blackout_days['excess_return'].mean():.4f}%")
    print(f"Mean Daily Excess Return (Non-Blackout): {non_blackout_days['excess_return'].mean():.4f}%")

    daily_diff = non_blackout_days['excess_return'].mean() - blackout_days['excess_return'].mean()
    print(f"Annualized Difference: {daily_diff * 252:.2f}%")

    print("\n" + "=" * 60)
    print("STATISTICAL SIGNIFICANCE")
    print("=" * 60)

    print(f"T-test statistic: {stats_results['t_stat']:.4f}")
    print(f"T-test p-value: {stats_results['t_p_value']:.4f}")
    print(f"Mann-Whitney U statistic: {stats_results['u_stat']:.0f}")
    print(f"Mann-Whitney p-value: {stats_results['u_p_value']:.4f}")

    if stats_results['t_p_value'] < 0.05:
        print("Result: STATISTICALLY SIGNIFICANT (p < 0.05)")
    elif stats_results['t_p_value'] < 0.10:
        print("Result: MARGINALLY SIGNIFICANT (p < 0.10)")
    else:
        print("Result: NOT STATISTICALLY SIGNIFICANT (p >= 0.10)")

    print("\n" + "=" * 60)
    print("POST-BLACKOUT RECOVERY")
    print("=" * 60)

    if len(post_blackout_results) > 0:
        print(f"Periods Analyzed: {len(post_blackout_results)}")
        print(f"Average {STOCK_TICKER} Excess Return: {post_blackout_results['excess_return'].mean():.2f}%")
        win_rate = (post_blackout_results['excess_return'] > 0).mean() * 100
        print(f"Outperformance Rate ({STOCK_TICKER} > {BENCHMARK_TICKER}): {win_rate:.1f}%")

    print("\n" + "=" * 60)
    print("INTERPRETATION")
    print("=" * 60)

    avg_excess = blackout_results['excess_return'].mean()
    if avg_excess < -1:
        print("Finding: STRONG support for thesis (excess return < -1%)")
    elif avg_excess < -0.5:
        print("Finding: MODERATE support for thesis (excess return -0.5% to -1%)")
    elif avg_excess < 0.5:
        print("Finding: No clear effect (excess return -0.5% to +0.5%)")
    else:
        print("Finding: Thesis NOT supported (excess return > +0.5%)")


def print_monthly_analysis(monthly_stats, yearly_stats):
    """Print monthly and yearly breakdowns."""

    print("\n" + "=" * 100)
    print("ANALYSIS BY EARNINGS MONTH")
    print("=" * 100)

    if len(monthly_stats) > 0:
        print(f"\n{'Month':<12} {'Count':>6} {STOCK_TICKER+' Ret':>10} {BENCHMARK_TICKER+' Ret':>10} {'Excess':>10} {'Underperf%':>12} {'P-value':>10} {'Sig?':>6}")
        print("-" * 100)

        for _, row in monthly_stats.iterrows():
            sig = "**" if pd.notna(row['p_value']) and row['p_value'] < 0.05 else ("*" if pd.notna(row['p_value']) and row['p_value'] < 0.10 else "")
            print(f"{row['earnings_month_name']:<12} {int(row['stock_return_count']):>6} "
                  f"{row['stock_return_mean']:>+10.2f}% {row['benchmark_return_mean']:>+9.2f}% "
                  f"{row['excess_return_mean']:>+9.2f}% {row['underperf_rate']:>11.1f}% "
                  f"{row['p_value']:>10.4f} {sig:>6}")

    print("\n" + "=" * 100)
    print("ANALYSIS BY YEAR")
    print("=" * 100)

    if len(yearly_stats) > 0:
        print(f"\n{'Year':<6} {'Count':>6} {STOCK_TICKER+' Ret':>10} {BENCHMARK_TICKER+' Ret':>10} {'Excess':>10} {'Min':>10} {'Max':>10} {'Underperf%':>12}")
        print("-" * 100)

        for _, row in yearly_stats.iterrows():
            print(f"{int(row['year']):<6} {int(row['stock_return_count']):>6} "
                  f"{row['stock_return_mean']:>+10.2f}% {row['benchmark_return_mean']:>+9.2f}% "
                  f"{row['excess_return_mean']:>+9.2f}% "
                  f"{row['excess_return_min']:>+9.2f}% {row['excess_return_max']:>+9.2f}% "
                  f"{row['underperf_rate']:>11.1f}%")

    print("\n" + "-" * 100)
    print("Legend: ** = p < 0.05 (significant), * = p < 0.10 (marginally significant)")


def create_visualizations(daily_results, blackout_results, windows):
    """Generate charts."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Chart 1: Cumulative Excess Return
    ax1 = axes[0, 0]
    cumulative = daily_results['excess_return'].cumsum()
    ax1.plot(cumulative.index, cumulative.values, 'b-', linewidth=1)

    for start, end, _ in windows:
        if start >= daily_results.index.min() and end <= daily_results.index.max():
            ax1.axvspan(start, end, alpha=0.3, color='gray')

    ax1.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax1.set_title(f'Cumulative {STOCK_TICKER}-{BENCHMARK_TICKER} Excess Return\n(Gray = Blackout Periods)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative Excess Return (%)')
    ax1.grid(True, alpha=0.3)

    # Chart 2: Box Plot
    ax2 = axes[0, 1]
    blackout_returns = daily_results[daily_results['in_blackout']]['excess_return']
    non_blackout_returns = daily_results[~daily_results['in_blackout']]['excess_return']

    bp = ax2.boxplot([blackout_returns, non_blackout_returns],
                     labels=['During Blackout', 'Outside Blackout'],
                     patch_artist=True)
    bp['boxes'][0].set_facecolor('lightcoral')
    bp['boxes'][1].set_facecolor('lightgreen')
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax2.set_title('Daily Excess Returns Distribution')
    ax2.set_ylabel('Daily Excess Return (%)')
    ax2.grid(True, alpha=0.3)
    ax2.scatter([1], [blackout_returns.mean()], color='red', marker='D', s=100, zorder=5)
    ax2.scatter([2], [non_blackout_returns.mean()], color='green', marker='D', s=100, zorder=5)

    # Chart 3: Bar Chart
    ax3 = axes[1, 0]
    if len(blackout_results) > 0:
        colors = ['red' if x < 0 else 'green' for x in blackout_results['excess_return']]
        x_positions = range(len(blackout_results))
        ax3.bar(x_positions, blackout_results['excess_return'], color=colors, alpha=0.7)
        ax3.set_xticks(x_positions[::4])
        ax3.set_xticklabels([str(d) for d in blackout_results['earnings_date'].iloc[::4]], rotation=45, ha='right', fontsize=8)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax3.axhline(y=blackout_results['excess_return'].mean(), color='blue', linestyle='--', linewidth=2)

    ax3.set_title(f'{STOCK_TICKER} Excess Return by Blackout Period')
    ax3.set_xlabel('Earnings Date')
    ax3.set_ylabel('Excess Return (%)')
    ax3.grid(True, alpha=0.3, axis='y')

    # Chart 4: Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    summary_text = f"""
    SUMMARY: {STOCK_TICKER} vs {BENCHMARK_TICKER}
    {'='*40}

    BLACKOUT PERIODS
    • Periods: {len(blackout_results)}
    • Avg Excess Return: {blackout_results['excess_return'].mean():.2f}%
    • Median: {blackout_results['excess_return'].median():.2f}%
    • Std Dev: {blackout_results['excess_return'].std():.2f}%

    DAILY ANALYSIS
    • Days in Blackout: {len(blackout_returns)}
    • Days Outside: {len(non_blackout_returns)}

    CONCLUSION
    • Thesis: {'SUPPORTED' if blackout_results['excess_return'].mean() < 0 else 'NOT SUPPORTED'}
    """
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    output_file = f'{STOCK_TICKER.lower()}_blackout_analysis.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"\nVisualization saved to '{output_file}'")


def main():
    print("=" * 60)
    print(f"BUYBACK BLACKOUT PERIOD ANALYSIS")
    print(f"Stock: {STOCK_TICKER} | Benchmark: {BENCHMARK_TICKER}")
    print("=" * 60)
    print(f"\nBlackout window: {BLACKOUT_DAYS_BEFORE} days before to {BLACKOUT_DAYS_AFTER} days after earnings\n")

    # Load data
    stock, benchmark = load_data()

    # Generate windows
    windows = generate_blackout_windows(EARNINGS_DATES)
    print(f"\nGenerated {len(windows)} blackout windows")

    # Run analyses
    print("\nRunning analysis...")
    blackout_results = analyze_blackout_periods(stock, benchmark, windows)
    post_blackout_results = analyze_post_blackout(stock, benchmark, windows)
    daily_results = analyze_daily_returns(stock, benchmark, windows)

    # Statistical tests
    blackout_returns = daily_results[daily_results['in_blackout']]['excess_return']
    non_blackout_returns = daily_results[~daily_results['in_blackout']]['excess_return']
    stats_results = run_statistical_tests(blackout_returns, non_blackout_returns)

    # Monthly/yearly analysis
    monthly_stats = analyze_by_month(blackout_results)
    yearly_stats = analyze_by_year(blackout_results)

    # Print results
    print_summary(blackout_results, post_blackout_results, daily_results, stats_results)
    print_monthly_analysis(monthly_stats, yearly_stats)

    # Visualizations
    try:
        create_visualizations(daily_results, blackout_results, windows)
    except Exception as e:
        print(f"\nVisualization error: {e}")

    # Save to CSV
    prefix = STOCK_TICKER.lower()
    blackout_results.to_csv(f'{prefix}_blackout_results.csv', index=False)
    post_blackout_results.to_csv(f'{prefix}_post_blackout_results.csv', index=False)
    daily_results.to_csv(f'{prefix}_daily_analysis.csv')
    monthly_stats.to_csv(f'{prefix}_monthly_analysis.csv', index=False)
    yearly_stats.to_csv(f'{prefix}_yearly_analysis.csv', index=False)

    print("\n" + "=" * 60)
    print("RESULTS SAVED")
    print("=" * 60)
    print(f"  • {prefix}_blackout_results.csv")
    print(f"  • {prefix}_post_blackout_results.csv")
    print(f"  • {prefix}_daily_analysis.csv")
    print(f"  • {prefix}_monthly_analysis.csv")
    print(f"  • {prefix}_yearly_analysis.csv")
    print(f"  • {prefix}_blackout_analysis.png")

    return blackout_results, post_blackout_results, daily_results


if __name__ == "__main__":
    main()
