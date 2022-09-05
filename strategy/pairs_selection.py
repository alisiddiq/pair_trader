import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests
from multiprocessing.pool import ThreadPool
from tqdm.auto import tqdm

PAIR_SECURITY_SEPARATOR = "|"


def generate_mdm(p1: pd.Series, p2: pd.Series) -> float:
    """
    Get sum of distances between 2 returns
    :param p1: Returns of 1 security
    :param p2: Returns of another security
    :return: Sum of distance
    """
    p1_cumu = np.cumprod(p1 + 1)
    p2_cumu = np.cumprod(p2 + 1)
    p1_cumu = p1_cumu / p1_cumu.iloc[0]
    p2_cumu = p2_cumu / p2_cumu.iloc[0]
    return ((p1_cumu - p2_cumu) ** 2).sum()


def generate_mfr(p1: pd.Series, p2: pd.Series, index_returns: pd.Series) -> float:
    """
    MFR = abs(b1/b2) - 1 where b1 is the market beta of stock 1, and b2 is the market beta of stock 2
    :param p1: Returns of 1 security
    :param p2: Returns of another security
    :param index_returns: Returns of the index (used as market in this case)
    :return: MFR score
    """
    beta1 = np.cov(p1, index_returns)[0, 1] / np.var(index_returns)
    beta2 = np.cov(p2, index_returns)[0, 1] / np.var(index_returns)
    return np.abs((beta1 / beta2) - 1)


def generate_granger_causality_score(p1: pd.Series, p2: pd.Series) -> float:
    """
    Calculate sum of p values for p1 being Granger follower and p2 being Granger leader, and vice versa
    :param p1: Returns of 1 security
    :param p2: Returns of another security
    :return: Sum of p values for a single representative score
    """
    p12 = pd.DataFrame({"p1": p1, "p2": p2})
    p21 = pd.DataFrame({"p2": p2, "p1": p1})
    g12_pval = grangercausalitytests(p12, maxlag=1, verbose=False)[1][0]['ssr_chi2test'][1]
    g21_pval = grangercausalitytests(p21, maxlag=1, verbose=False)[1][0]['ssr_chi2test'][1]
    return g12_pval + g21_pval


def _gen_all_scores(params):
    pair = params["pair"]
    p1 = params["p1"]
    p2 = params["p2"]
    index = params["index"]

    return {
        "PAIR": pair,
        "MDM": generate_mdm(p1=p1,
                            p2=p2),
        "MFR": generate_mfr(p1=p1,
                            p2=p1,
                            index_returns=index),
        "G": generate_granger_causality_score(p1=p1,
                                              p2=p2)
    }


def generate_pairs_and_scores(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate pairs and their metrics of how good they are as pairs
    :param prices_df: Prices dataframe for index and all its constituents
    :return: Dataframe containing best pairs and their scores
    """
    returns_df = prices_df.pct_change().dropna()

    all_securities = [col for col in prices_df.columns if col != "index"]
    chosen_pairs = []
    all_params = []

    for sec1 in all_securities:
        for sec2 in all_securities:
            pair12 = f"{sec1}{PAIR_SECURITY_SEPARATOR}{sec2}"
            pair21 = f"{sec2}{PAIR_SECURITY_SEPARATOR}{sec1}"
            if (sec1 == sec2) or (pair12 in chosen_pairs) or (pair21 in chosen_pairs):
                continue

            if {sec1, sec2}.intersection({"EUR", "USD", "GBP"}):
                # The data needs a bit of cleaning as some of these symbols have sneaked in, patching for now
                continue
            chosen_pairs.append(pair12)
            all_params.append({
                "pair": pair12,
                "p1": returns_df[sec1],
                "p2": returns_df[sec2],
                "index": returns_df["index"],
            })

    # Using multithreading for faster processing
    with ThreadPool(10) as pool:
        all_metrics = list(tqdm(pool.imap(_gen_all_scores, all_params), total=len(all_params)))
    pairs_df = pd.DataFrame(all_metrics).set_index("PAIR")
    return pairs_df


def select_top_n_pairs(generated_pairs_df: pd.DataFrame,
                       selection_method: str,
                       n: int = 5):
    """
    Select top n pairs based on the given method. Makes sure that if a
    security is chosen, it is not repeated again
    :param generated_pairs_df: Output of generate_pairs_and_scores
    :param selection_method: One of [G, MDM, MFR]
    :param n: How many to choose
    :return: Filtered df
    """
    if selection_method not in ["G", "MDM", "MFR"]:
        raise ValueError("Unexpected value for selection method. Please choose one of [G, MDM, MFR]")

    chosen_securities = set()
    chosen_pairs = []
    top_n_pairs = generated_pairs_df.sort_values(selection_method)

    for pair in top_n_pairs.index:
        sec1, sec2 = pair.split(PAIR_SECURITY_SEPARATOR)
        if {sec1, sec2}.intersection(chosen_securities):
            # One of the securities is already chosen, so we continue to next
            continue
        chosen_securities.update([sec1, sec2])
        chosen_pairs.append(pair)
        if len(chosen_pairs) >= n:
            break

    return top_n_pairs.loc[chosen_pairs]
