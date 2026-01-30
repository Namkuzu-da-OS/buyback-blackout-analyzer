"""
aapl_blackout_analysis.py
Apple Buyback Blackout Period Analysis

Tests whether Apple (AAPL) stock underperforms during buyback blackout periods
compared to the S&P 500 (SPY).
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
    "2026-01-29",  # Upcoming Q1 FY2026
    # 2025
    "2025-10-30",  # Q4 FY2025
    "2025-07-31",  # Q3 FY2025
    "2025-05-01",  # Q2 FY2025
    "2025-01-30",  # Q1 FY2025
    # 2024
    "2024-10-31",  # Q4 FY2024
    "2024-08-01",  # Q3 FY2024
    "2024-05-02",  # Q2 FY2024
    "2024-02-01",  # Q1 FY2024
    # 2023
    "2023-11-02",  # Q4 FY2023
    "2023-08-03",  # Q3 FY2023
    "2023-05-04",  # Q2 FY2023
    "2023-02-02",  # Q1 FY2023
    # 2022
    "2022-10-27",  # Q4 FY2022
    "2022-07-28",  # Q3 FY2022
    "2022-04-28",  # Q2 FY2022
    "2022-01-27",  # Q1 FY2022
    # 2021
    "2021-10-28",  # Q4 FY2021
    "2021-07-27",  # Q3 FY2021
    "2021-04-28",  # Q2 FY2021
    "2021-01-27",  # Q1 FY2021
    # 2020
    "2020-10-29",  # Q4 FY2020
    "2020-07-30",  # Q3 FY2020
    "2020-04-30",  # Q2 FY2020
    "2020-01-28",  # Q1 FY2020
    # 2019
    "2019-10-30",  # Q4 FY2019
    "2019-07-30",  # Q3 FY2019
    "2019-04-30",  # Q2 FY2019
    "2019-01-29",  # Q1 FY2019
    # 2018
    "2018-11-01",  # Q4 FY2018
    "2018-07-31",  # Q3 FY2018
    "2018-05-01",  # Q2 FY2018
    "2018-02-01",  # Q1 FY2018
    # 2017
    "2017-11-02",  # Q4 FY2017
    "2017-08-01",  # Q3 FY2017
    "2017-05-02",  # Q2 FY2017
    "2017-01-31",  # Q1 FY2017
    # 2016
    "2016-10-25",  # Q4 FY2016
    "2016-07-26",  # Q3 FY2016
    "2016-04-26",  # Q2 FY2016
    "2016-01-26",  # Q1 FY2016
    # 2015
    "2015-10-27",  # Q4 FY2015
    "2015-07-21",  # Q3 FY2015
    "2015-04-27",  # Q2 FY2015
    "2015-01-27",  # Q1 FY2015
    # 2014
    "2014-10-20",  # Q4 FY2014
    "2014-07-22",  # Q3 FY2014
    "2014-04-23",  # Q2 FY2014
    "2014-01-27",  # Q1 FY2014
    # 2013
    "2013-10-28",  # Q4 FY2013
    "2013-07-23",  # Q3 FY2013
    "2013-04-23",  # Q2 FY2013
    "2013-01-23",  # Q1 FY2013
    # 2012 (buyback program announced April 2012)
    "2012-10-25",  # Q4 FY2012
    "2012-07-24",  # Q3 FY2012
    "2012-04-24",  # Q2 FY2012
]

BLACKOUT_DAYS_BEFORE = 35  # 5 weeks before earnings
BLACKOUT_DAYS_AFTER = 2    # 2 trading days after earnings
POST_BLACKOUT_DAYS = 10    # Recovery window analysis


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

    print(f"  AAPL: {len(aapl)} trading days ({aapl.index.min().date()} to {aapl.index.max().date()})")
    print(f"  SPY:  {len(spy)} trading days ({spy.index.min().date()} to {spy.index.max().date()})")

    return aapl, spy


# ============================================
# BLACKOUT WINDOW GENERATION
# ============================================
def get_blackout_window(earnings_date_str):
    """
    Returns (blackout_start, blackout_end) for a given earnings date.
    """
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


# ============================================
# ANALYSIS FUNCTIONS
# ============================================
def calculate_period_return(price_data, start_date, end_date):
    """
    Calculate total return between two dates.
    Use 'Adj Close' to account for splits/dividends.
    """
    # Handle case where Adj Close might not exist
    price_col = 'Adj Close' if 'Adj Close' in price_data.columns else 'Close'

    mask = (price_data.index >= start_date) & (price_data.index <= end_date)
    period_data = price_data.loc[mask, price_col]

    if len(period_data) < 2:
        return np.nan

    start_price = period_data.iloc[0]
    end_price = period_data.iloc[-1]
    return (end_price / start_price - 1) * 100  # Return as percentage


def analyze_blackout_periods(aapl_data, spy_data, windows):
    """Calculate returns during each blackout period."""
    results = []

    for start, end, earnings_date in windows:
        # Skip future dates
        if start > aapl_data.index.max():
            continue

        aapl_return = calculate_period_return(aapl_data, start, end)
        spy_return = calculate_period_return(spy_data, start, end)

        if pd.isna(aapl_return) or pd.isna(spy_return):
            continue

        excess_return = aapl_return - spy_return

        results.append({
            'earnings_date': earnings_date.date(),
            'blackout_start': start.date(),
            'blackout_end': end.date(),
            'aapl_return': aapl_return,
            'spy_return': spy_return,
            'excess_return': excess_return
        })

    return pd.DataFrame(results)


def analyze_post_blackout(aapl_data, spy_data, windows):
    """Calculate returns after each blackout period (recovery window)."""
    results = []

    for start, end, earnings_date in windows:
        # Post-blackout starts 3 days after earnings, ends 10 trading days after
        recovery_start = earnings_date + timedelta(days=3)
        recovery_end = earnings_date + timedelta(days=POST_BLACKOUT_DAYS + 5)  # Extra buffer for weekends

        # Skip future dates
        if recovery_start > aapl_data.index.max():
            continue

        aapl_return = calculate_period_return(aapl_data, recovery_start, recovery_end)
        spy_return = calculate_period_return(spy_data, recovery_start, recovery_end)

        if pd.isna(aapl_return) or pd.isna(spy_return):
            continue

        excess_return = aapl_return - spy_return

        results.append({
            'earnings_date': earnings_date.date(),
            'recovery_start': recovery_start.date(),
            'aapl_return': aapl_return,
            'spy_return': spy_return,
            'excess_return': excess_return
        })

    return pd.DataFrame(results)


def is_in_blackout(date, windows):
    """Check if a date falls within any blackout window."""
    for start, end, _ in windows:
        if start <= date <= end:
            return True
    return False


def analyze_daily_returns(aapl_data, spy_data, windows):
    """Classify each day and calculate daily excess returns."""
    price_col = 'Adj Close' if 'Adj Close' in aapl_data.columns else 'Close'

    # Calculate daily returns
    daily_data = pd.DataFrame(index=aapl_data.index)
    daily_data['aapl_return'] = aapl_data[price_col].pct_change() * 100
    daily_data['spy_return'] = spy_data[price_col].pct_change() * 100
    daily_data['excess_return'] = daily_data['aapl_return'] - daily_data['spy_return']

    # Classify each day
    daily_data['in_blackout'] = daily_data.index.map(lambda x: is_in_blackout(x, windows))

    # Drop NaN values
    daily_data = daily_data.dropna()

    return daily_data


def run_statistical_tests(blackout_returns, non_blackout_returns):
    """Run t-test and Mann-Whitney U test."""
    results = {}

    # T-test
    t_stat, t_p_value = stats.ttest_ind(blackout_returns, non_blackout_returns)
    results['t_stat'] = t_stat
    results['t_p_value'] = t_p_value

    # Mann-Whitney U test
    u_stat, u_p_value = stats.mannwhitneyu(
        blackout_returns,
        non_blackout_returns,
        alternative='two-sided'
    )
    results['u_stat'] = u_stat
    results['u_p_value'] = u_p_value

    return results


def analyze_by_month(blackout_results):
    """Analyze blackout performance broken down by earnings month."""
    if len(blackout_results) == 0:
        return pd.DataFrame()

    # Add month column
    df = blackout_results.copy()
    df['earnings_month'] = pd.to_datetime(df['earnings_date']).dt.month
    df['earnings_month_name'] = pd.to_datetime(df['earnings_date']).dt.strftime('%B')

    # Group by month
    monthly_stats = df.groupby(['earnings_month', 'earnings_month_name']).agg({
        'aapl_return': ['mean', 'std', 'count'],
        'spy_return': ['mean', 'std'],
        'excess_return': ['mean', 'std', 'min', 'max']
    }).round(2)

    # Flatten column names
    monthly_stats.columns = ['_'.join(col).strip() for col in monthly_stats.columns.values]
    monthly_stats = monthly_stats.reset_index()

    # Calculate win rate (underperformance rate) per month
    win_rates = df.groupby('earnings_month').apply(
        lambda x: (x['excess_return'] < 0).mean() * 100
    ).reset_index()
    win_rates.columns = ['earnings_month', 'underperf_rate']

    monthly_stats = monthly_stats.merge(win_rates, on='earnings_month')

    # Run t-test for each month (excess return vs 0)
    t_test_results = []
    for month in df['earnings_month'].unique():
        month_data = df[df['earnings_month'] == month]['excess_return']
        if len(month_data) >= 3:
            t_stat, p_val = stats.ttest_1samp(month_data, 0)
            t_test_results.append({
                'earnings_month': month,
                't_stat': t_stat,
                'p_value': p_val
            })
        else:
            t_test_results.append({
                'earnings_month': month,
                't_stat': np.nan,
                'p_value': np.nan
            })

    t_test_df = pd.DataFrame(t_test_results)
    monthly_stats = monthly_stats.merge(t_test_df, on='earnings_month')

    return monthly_stats.sort_values('earnings_month')


def analyze_by_quarter(blackout_results):
    """Analyze blackout performance by fiscal quarter."""
    if len(blackout_results) == 0:
        return pd.DataFrame()

    df = blackout_results.copy()

    # Map earnings months to Apple fiscal quarters
    # Apple FY: Oct-Dec = Q1, Jan-Mar = Q2, Apr-Jun = Q3, Jul-Sep = Q4
    # Earnings are reported ~1 month after quarter end
    month_to_quarter = {
        1: 'Q1 (Oct-Dec)',   # January earnings = Q1
        2: 'Q1 (Oct-Dec)',   # February earnings = Q1
        4: 'Q2 (Jan-Mar)',   # April earnings = Q2
        5: 'Q2 (Jan-Mar)',   # May earnings = Q2
        7: 'Q3 (Apr-Jun)',   # July earnings = Q3
        8: 'Q3 (Apr-Jun)',   # August earnings = Q3
        10: 'Q4 (Jul-Sep)',  # October earnings = Q4
        11: 'Q4 (Jul-Sep)',  # November earnings = Q4
    }

    df['earnings_month'] = pd.to_datetime(df['earnings_date']).dt.month
    df['fiscal_quarter'] = df['earnings_month'].map(month_to_quarter)

    # Group by quarter
    quarterly_stats = df.groupby('fiscal_quarter').agg({
        'aapl_return': ['mean', 'count'],
        'spy_return': 'mean',
        'excess_return': ['mean', 'std', 'min', 'max']
    }).round(2)

    quarterly_stats.columns = ['_'.join(col).strip() for col in quarterly_stats.columns.values]
    quarterly_stats = quarterly_stats.reset_index()

    # Win rate per quarter
    win_rates = df.groupby('fiscal_quarter').apply(
        lambda x: (x['excess_return'] < 0).mean() * 100
    ).reset_index()
    win_rates.columns = ['fiscal_quarter', 'underperf_rate']

    quarterly_stats = quarterly_stats.merge(win_rates, on='fiscal_quarter')

    # T-test per quarter
    t_test_results = []
    for quarter in df['fiscal_quarter'].unique():
        quarter_data = df[df['fiscal_quarter'] == quarter]['excess_return']
        if len(quarter_data) >= 3:
            t_stat, p_val = stats.ttest_1samp(quarter_data, 0)
            t_test_results.append({
                'fiscal_quarter': quarter,
                't_stat': t_stat,
                'p_value': p_val
            })

    t_test_df = pd.DataFrame(t_test_results)
    quarterly_stats = quarterly_stats.merge(t_test_df, on='fiscal_quarter', how='left')

    return quarterly_stats


def analyze_by_year(blackout_results):
    """Analyze blackout performance by year."""
    if len(blackout_results) == 0:
        return pd.DataFrame()

    df = blackout_results.copy()
    df['year'] = pd.to_datetime(df['earnings_date']).dt.year

    yearly_stats = df.groupby('year').agg({
        'aapl_return': ['mean', 'count'],
        'spy_return': 'mean',
        'excess_return': ['mean', 'std', 'min', 'max']
    }).round(2)

    yearly_stats.columns = ['_'.join(col).strip() for col in yearly_stats.columns.values]
    yearly_stats = yearly_stats.reset_index()

    # Win rate per year
    win_rates = df.groupby('year').apply(
        lambda x: (x['excess_return'] < 0).mean() * 100
    ).reset_index()
    win_rates.columns = ['year', 'underperf_rate']

    yearly_stats = yearly_stats.merge(win_rates, on='year')

    return yearly_stats


def print_monthly_analysis(monthly_stats, quarterly_stats, yearly_stats):
    """Print detailed monthly/quarterly/yearly breakdown."""

    print("\n" + "=" * 100)
    print("ANALYSIS BY EARNINGS MONTH")
    print("=" * 100)

    if len(monthly_stats) > 0:
        print(f"\n{'Month':<12} {'Count':>6} {'AAPL Ret':>10} {'SPY Ret':>10} {'Excess':>10} {'Std Dev':>10} {'Underperf%':>12} {'P-value':>10} {'Sig?':>8}")
        print("-" * 100)

        for _, row in monthly_stats.iterrows():
            sig = ""
            if pd.notna(row['p_value']):
                if row['p_value'] < 0.05:
                    sig = "**"
                elif row['p_value'] < 0.10:
                    sig = "*"

            print(f"{row['earnings_month_name']:<12} {int(row['aapl_return_count']):>6} "
                  f"{row['aapl_return_mean']:>+10.2f}% {row['spy_return_mean']:>+9.2f}% "
                  f"{row['excess_return_mean']:>+9.2f}% {row['excess_return_std']:>9.2f}% "
                  f"{row['underperf_rate']:>11.1f}% "
                  f"{row['p_value']:>10.4f} {sig:>8}")

    print("\n" + "=" * 100)
    print("ANALYSIS BY FISCAL QUARTER")
    print("=" * 100)

    if len(quarterly_stats) > 0:
        print(f"\n{'Quarter':<16} {'Count':>6} {'AAPL Ret':>10} {'SPY Ret':>10} {'Excess':>10} {'Underperf%':>12} {'P-value':>10} {'Sig?':>8}")
        print("-" * 100)

        for _, row in quarterly_stats.iterrows():
            sig = ""
            if 'p_value' in row and pd.notna(row.get('p_value')):
                if row['p_value'] < 0.05:
                    sig = "**"
                elif row['p_value'] < 0.10:
                    sig = "*"

            p_val = row.get('p_value', np.nan)
            p_str = f"{p_val:.4f}" if pd.notna(p_val) else "N/A"

            print(f"{row['fiscal_quarter']:<16} {int(row['aapl_return_count']):>6} "
                  f"{row['aapl_return_mean']:>+10.2f}% {row['spy_return_mean']:>+9.2f}% "
                  f"{row['excess_return_mean']:>+9.2f}% "
                  f"{row['underperf_rate']:>11.1f}% "
                  f"{p_str:>10} {sig:>8}")

    print("\n" + "=" * 100)
    print("ANALYSIS BY YEAR")
    print("=" * 100)

    if len(yearly_stats) > 0:
        print(f"\n{'Year':<6} {'Count':>6} {'AAPL Ret':>10} {'SPY Ret':>10} {'Excess':>10} {'Min':>10} {'Max':>10} {'Underperf%':>12}")
        print("-" * 100)

        for _, row in yearly_stats.iterrows():
            print(f"{int(row['year']):<6} {int(row['aapl_return_count']):>6} "
                  f"{row['aapl_return_mean']:>+10.2f}% {row['spy_return_mean']:>+9.2f}% "
                  f"{row['excess_return_mean']:>+9.2f}% "
                  f"{row['excess_return_min']:>+9.2f}% {row['excess_return_max']:>+9.2f}% "
                  f"{row['underperf_rate']:>11.1f}%")

    print("\n" + "-" * 100)
    print("Legend: ** = p < 0.05 (significant), * = p < 0.10 (marginally significant)")
    print("Underperf% = percentage of periods where AAPL underperformed SPY")


# ============================================
# REPORTING
# ============================================
def print_summary(blackout_results, post_blackout_results, daily_results, stats_results):
    """Print formatted summary statistics."""

    print("\n" + "=" * 60)
    print("BLACKOUT PERIOD ANALYSIS")
    print("=" * 60)

    if len(blackout_results) > 0:
        print(f"Total Blackout Periods Analyzed: {len(blackout_results)}")
        print(f"Average AAPL Return During Blackout: {blackout_results['aapl_return'].mean():.2f}%")
        print(f"Average SPY Return During Blackout: {blackout_results['spy_return'].mean():.2f}%")
        print(f"Average AAPL Excess Return: {blackout_results['excess_return'].mean():.2f}%")
        win_rate = (blackout_results['excess_return'] < 0).mean() * 100
        print(f"Underperformance Rate (AAPL < SPY during blackout): {win_rate:.1f}%")

    print("\n" + "=" * 60)
    print("DAILY RETURN ANALYSIS")
    print("=" * 60)

    blackout_days = daily_results[daily_results['in_blackout']]
    non_blackout_days = daily_results[~daily_results['in_blackout']]

    print(f"Days IN Blackout: {len(blackout_days)}")
    print(f"Days OUTSIDE Blackout: {len(non_blackout_days)}")
    print(f"Mean Daily Excess Return (Blackout): {blackout_days['excess_return'].mean():.4f}%")
    print(f"Mean Daily Excess Return (Non-Blackout): {non_blackout_days['excess_return'].mean():.4f}%")

    # Annualize the difference (roughly 252 trading days)
    daily_diff = non_blackout_days['excess_return'].mean() - blackout_days['excess_return'].mean()
    annualized_diff = daily_diff * 252
    print(f"Annualized Difference: {annualized_diff:.2f}%")

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
        print(f"Average AAPL Return (10 days post): {post_blackout_results['aapl_return'].mean():.2f}%")
        print(f"Average SPY Return (10 days post): {post_blackout_results['spy_return'].mean():.2f}%")
        print(f"Average AAPL Excess Return: {post_blackout_results['excess_return'].mean():.2f}%")
        win_rate = (post_blackout_results['excess_return'] > 0).mean() * 100
        print(f"Outperformance Rate (AAPL > SPY post-blackout): {win_rate:.1f}%")

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


def create_visualizations(daily_results, blackout_results, windows):
    """Generate charts."""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Chart 1: Cumulative Excess Return with Blackout Shading
    ax1 = axes[0, 0]
    cumulative = daily_results['excess_return'].cumsum()
    ax1.plot(cumulative.index, cumulative.values, 'b-', linewidth=1)

    # Shade blackout periods
    for start, end, _ in windows:
        if start >= daily_results.index.min() and end <= daily_results.index.max():
            ax1.axvspan(start, end, alpha=0.3, color='gray')

    ax1.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax1.set_title('Cumulative AAPL-SPY Excess Return\n(Gray = Blackout Periods)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative Excess Return (%)')
    ax1.grid(True, alpha=0.3)

    # Chart 2: Box Plot of Daily Excess Returns
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

    # Add means
    ax2.scatter([1], [blackout_returns.mean()], color='red', marker='D', s=100, zorder=5, label='Mean')
    ax2.scatter([2], [non_blackout_returns.mean()], color='green', marker='D', s=100, zorder=5)

    # Chart 3: Bar Chart of Blackout Period Excess Returns
    ax3 = axes[1, 0]
    if len(blackout_results) > 0:
        colors = ['red' if x < 0 else 'green' for x in blackout_results['excess_return']]
        x_positions = range(len(blackout_results))
        bars = ax3.bar(x_positions, blackout_results['excess_return'], color=colors, alpha=0.7)

        ax3.set_xticks(x_positions)
        ax3.set_xticklabels([str(d) for d in blackout_results['earnings_date']],
                           rotation=45, ha='right', fontsize=8)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax3.axhline(y=blackout_results['excess_return'].mean(), color='blue',
                   linestyle='--', linewidth=2, label=f"Mean: {blackout_results['excess_return'].mean():.2f}%")
        ax3.legend()

    ax3.set_title('AAPL Excess Return by Blackout Period')
    ax3.set_xlabel('Earnings Date')
    ax3.set_ylabel('Excess Return (%)')
    ax3.grid(True, alpha=0.3, axis='y')

    # Chart 4: Summary Statistics Text
    ax4 = axes[1, 1]
    ax4.axis('off')

    summary_text = f"""
    SUMMARY STATISTICS
    ══════════════════════════════════════

    BLACKOUT PERIODS
    • Periods Analyzed: {len(blackout_results)}
    • Avg AAPL Excess Return: {blackout_results['excess_return'].mean():.2f}%
    • Median AAPL Excess Return: {blackout_results['excess_return'].median():.2f}%
    • Std Dev: {blackout_results['excess_return'].std():.2f}%

    DAILY ANALYSIS
    • Days in Blackout: {len(blackout_returns)}
    • Days Outside: {len(non_blackout_returns)}
    • Mean Daily (Blackout): {blackout_returns.mean():.4f}%
    • Mean Daily (Non-Blackout): {non_blackout_returns.mean():.4f}%

    HYPOTHESIS TEST
    • Does AAPL underperform during blackout?
    • Thesis supported if excess return < 0
    • Current finding: {'SUPPORTED' if blackout_results['excess_return'].mean() < 0 else 'NOT SUPPORTED'}
    """

    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig('aapl_blackout_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\nVisualization saved to 'aapl_blackout_analysis.png'")


def print_detailed_tables(blackout_results, post_blackout_results):
    """Print detailed results tables."""

    print("\n" + "=" * 100)
    print("TABLE 1: BLACKOUT PERIOD PERFORMANCE")
    print("=" * 100)

    if len(blackout_results) > 0:
        table1 = blackout_results.copy()
        table1['aapl_return'] = table1['aapl_return'].apply(lambda x: f"{x:+.2f}%")
        table1['spy_return'] = table1['spy_return'].apply(lambda x: f"{x:+.2f}%")
        table1['excess_return'] = table1['excess_return'].apply(lambda x: f"{x:+.2f}%")
        print(table1.to_string(index=False))

    print("\n" + "=" * 100)
    print("TABLE 2: POST-BLACKOUT RECOVERY PERFORMANCE")
    print("=" * 100)

    if len(post_blackout_results) > 0:
        table2 = post_blackout_results.copy()
        table2['aapl_return'] = table2['aapl_return'].apply(lambda x: f"{x:+.2f}%")
        table2['spy_return'] = table2['spy_return'].apply(lambda x: f"{x:+.2f}%")
        table2['excess_return'] = table2['excess_return'].apply(lambda x: f"{x:+.2f}%")
        print(table2.to_string(index=False))


# ============================================
# MAIN
# ============================================
def main():
    print("=" * 60)
    print("APPLE BUYBACK BLACKOUT PERIOD ANALYSIS")
    print("=" * 60)
    print("\nHypothesis: AAPL underperforms during buyback blackout periods")
    print(f"Blackout window: {BLACKOUT_DAYS_BEFORE} days before to {BLACKOUT_DAYS_AFTER} days after earnings\n")

    # 1. Load data
    aapl, spy = load_data()

    # 2. Generate blackout windows
    windows = generate_blackout_windows(APPLE_EARNINGS_DATES)
    print(f"\nGenerated {len(windows)} blackout windows")

    # 3. Run analyses
    print("\nRunning analysis...")
    blackout_results = analyze_blackout_periods(aapl, spy, windows)
    post_blackout_results = analyze_post_blackout(aapl, spy, windows)
    daily_results = analyze_daily_returns(aapl, spy, windows)

    # 4. Statistical tests
    blackout_returns = daily_results[daily_results['in_blackout']]['excess_return']
    non_blackout_returns = daily_results[~daily_results['in_blackout']]['excess_return']
    stats_results = run_statistical_tests(blackout_returns, non_blackout_returns)

    # 5. Monthly/Quarterly/Yearly analysis
    monthly_stats = analyze_by_month(blackout_results)
    quarterly_stats = analyze_by_quarter(blackout_results)
    yearly_stats = analyze_by_year(blackout_results)

    # 6. Print detailed tables
    print_detailed_tables(blackout_results, post_blackout_results)

    # 7. Print summary
    print_summary(blackout_results, post_blackout_results, daily_results, stats_results)

    # 8. Print monthly breakdown
    print_monthly_analysis(monthly_stats, quarterly_stats, yearly_stats)

    # 9. Create visualizations
    try:
        create_visualizations(daily_results, blackout_results, windows)
    except Exception as e:
        print(f"\nVisualization error (non-critical): {e}")

    # 10. Save to CSV
    blackout_results.to_csv('aapl_blackout_results.csv', index=False)
    post_blackout_results.to_csv('aapl_post_blackout_results.csv', index=False)
    daily_results.to_csv('aapl_daily_analysis.csv')
    monthly_stats.to_csv('aapl_monthly_analysis.csv', index=False)
    quarterly_stats.to_csv('aapl_quarterly_analysis.csv', index=False)
    yearly_stats.to_csv('aapl_yearly_analysis.csv', index=False)

    print("\n" + "=" * 60)
    print("RESULTS SAVED")
    print("=" * 60)
    print("  • aapl_blackout_results.csv")
    print("  • aapl_post_blackout_results.csv")
    print("  • aapl_daily_analysis.csv")
    print("  • aapl_monthly_analysis.csv")
    print("  • aapl_quarterly_analysis.csv")
    print("  • aapl_yearly_analysis.csv")
    print("  • aapl_blackout_analysis.png")

    return blackout_results, post_blackout_results, daily_results, stats_results


if __name__ == "__main__":
    main()
