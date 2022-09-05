import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from strategy.pairs_selection import PAIR_SECURITY_SEPARATOR

def gen_pair_spread_dfs(chosen_pairs: List[str],
                        prices_df: pd.DataFrame,
                        window_size: int) -> Dict[str, pd.DataFrame]:
    """
    Generate spreads for the given pairs
    :param chosen_pairs: List of pairs chosen
    :param prices_df: Raw prices
    :param window_size: Rolling window size to determine entry/exit points
    :return: spreads per pair
    """
    pairs_dfs = {}
    for pair in chosen_pairs:
        sec1, sec2 = pair.split(PAIR_SECURITY_SEPARATOR)
        spread = prices_df[sec1]/prices_df[sec2]
        rolling_mu = spread.rolling(window_size).mean()
        rolling_std = spread.rolling(window_size).std()

        df = pd.DataFrame({
            "R": spread,
            "rolling_mu": rolling_mu,
            "rolling_std": rolling_std
        })
        pairs_dfs[pair] = df
    return pairs_dfs

def get_performance(chosen_pairs: List[str],
                    prices_df: pd.DataFrame,
                    test_start_date: datetime,
                    window_size: int,
                    open_threshold: float,
                    close_threshold: float) -> pd.DataFrame:
    """
    Generate the returns of the pair trading strategy
    :param chosen_pairs: List of pairs chosen
    :param prices_df: Raw prices
    :param test_start_date: from when should the backtest begin
    :param window_size: Rolling window size to determine entry/exit points
    :param open_threshold: z-score used to enter trade
    :param close_threshold: z-score used to exit trade
    :return: Performance df
    """
    returns_df = prices_df.pct_change().dropna().loc[test_start_date:]
    # Initialise a positions df, 1 means we are long, -1 means we are short, 0 means we dont hold any pos
    positions_df = pd.DataFrame(index=returns_df.index)
    # Calculate spreads
    pairs_spreads = gen_pair_spread_dfs(chosen_pairs=chosen_pairs,
                                        prices_df=prices_df,
                                        window_size=window_size)

    for pair, spread_df in pairs_spreads.items():
        is_long = False
        is_short = False
        sec1, sec2 = pair.split(PAIR_SECURITY_SEPARATOR)
        for dt in returns_df.index:
            spread_row = spread_df.loc[dt]
            # Going short on spread means sell sec1 and buy sec2
            # Going long on spread means buy sec1, and sell sec2
            if spread_row["R"] > spread_row["rolling_mu"] + open_threshold * spread_row["rolling_std"]:
                # Go short
                positions_df.loc[dt, sec1] = -1
                positions_df.loc[dt, sec2] = 1
                is_short = True
            elif spread_row["R"] < spread_row["rolling_mu"] - open_threshold * spread_row["rolling_std"]:
                # Go long
                positions_df.loc[dt, sec1] = 1
                positions_df.loc[dt, sec2] = -1
                is_long = True
            elif is_short and spread_row["R"] <= spread_row["rolling_mu"] + close_threshold * spread_row["rolling_std"]:
                # Close short
                positions_df.loc[dt, sec1] = 0
                positions_df.loc[dt, sec2] = 0
                is_short = False
            elif is_long and spread_row["R"] >= spread_row["rolling_mu"] - close_threshold * spread_row["rolling_std"]:
                # Close long
                positions_df.loc[dt, sec1] = 0
                positions_df.loc[dt, sec2] = 0
                is_long = False

    positions_df = positions_df.fillna(method="ffill").fillna(0)
    # Shift since we determine today what needs to be done tomorrow
    filtered_returns = (positions_df.shift() * returns_df[positions_df.columns]).sum(axis=1)
    cumulative_returns = pd.Series(np.nancumprod(filtered_returns+1), index=filtered_returns.index)
    cumulative_returns_index = pd.Series(np.nancumprod(returns_df["index"] + 1), index=filtered_returns.index)

    performance_df = pd.DataFrame({"index":cumulative_returns_index,
                                   "strategy": cumulative_returns})
    # Normalising
    performance_df = performance_df/performance_df.iloc[0]
    return performance_df

def _get_sharpe(returns: pd.Series):
    return np.sqrt(252) * np.nanmean(returns) / np.nanstd(returns)

def _get_max_drawdown(cumu_returns: pd.Series):
    return np.ptp(cumu_returns)/cumu_returns.max()


def gen_performance_metrics(performance_df: pd.DataFrame) -> pd.DataFrame:
    """
    :param performance_df: Output of get_performance
    :return: Performance metrics
    """
    returns = performance_df.pct_change()
    metrics = []
    for strat_type in performance_df.columns:
        metrics.append({
            "Type": strat_type,
            "Sharpe": _get_sharpe(returns[strat_type]),
            "MDD": _get_max_drawdown(performance_df[strat_type])
        })
    return pd.DataFrame(metrics)






























