from data_process.db_connector.mysql_connector import MySqlConnector
from datetime import datetime
from typing import List
import pandas as pd


def fetch_prices(db_conn: MySqlConnector,
                 securities_list: List[str],
                 start_date: datetime,
                 end_date: datetime) -> pd.DataFrame:
    """
    Get prices for a given list of securities
    """
    query = """
        SELECT security_code, close_date, adj_close FROM security_prices
        WHERE security_code in ({}) AND
        close_date BETWEEN :start_date AND :end_date
    """.format(str(securities_list).replace("[", "").replace("]", ""))
    prices_df = db_conn.query_db(query=query, params={"start_date": start_date,
                                                      "end_date": end_date})
    return prices_df.set_index(["close_date", "security_code"])["adj_close"].sort_index().unstack("security_code")


def fetch_index_constituents(db_conn: MySqlConnector,
                             sim_start_date: datetime,
                             sim_end_date: datetime,
                             index_code: str) -> pd.DataFrame:
    """
    Gets the constituents in the index, that were present on both sim_start_date and sim_end_date.
    Also makes sure the security_codes returned have prices present in yfinance
    """
    # Get all the constituents that have a price in yfinance, and are active as of a given snapshot_date
    query = """
        SELECT main.security_code, main.pct_weight FROM index_constituents as main
        INNER JOIN (
            -- Making sure we get the security codes as of a given date
            SELECT MAX(snapshot_date) as max_snapshot_dt, index_code from index_constituents
            WHERE snapshot_date <= :snapshot_date and index_code = :index_code
        ) AS prev_snap_dt ON
            prev_snap_dt.max_snapshot_dt = main.snapshot_date AND
            prev_snap_dt.index_code = main.index_code
        INNER JOIN (
            -- Making sure we only get security codes for which prices exist
            SELECT DISTINCT (security_code) as security_code from security_prices
         ) AS prices ON main.security_code = prices.security_code
        ORDER BY security_code
    """
    constituents_at_start = db_conn.query_db(query=query, params={"snapshot_date": sim_start_date,
                                                                  "index_code": index_code})
    constituents_at_end = db_conn.query_db(query=query, params={"snapshot_date": sim_end_date,
                                                                "index_code": index_code})
    # These securities were in the index for the full period and we only do analysis on them
    common_securities_for_the_whole_period = set(constituents_at_start["security_code"]).intersection(
        set(constituents_at_end["security_code"]))
    filtered_constituents = constituents_at_end[
        constituents_at_end["security_code"].isin(common_securities_for_the_whole_period)].sort_values("pct_weight",
                                                                                                       ascending=False)
    return filtered_constituents

def fetch_indices(db_conn: MySqlConnector):
    """
    Get index details, along with the earliest available snapshot date of that index
    """
    query = """
        SELECT index_details.*, min_snapshot_date FROM index_details
        INNER JOIN (
            SELECT MIN(snapshot_date) as min_snapshot_date, index_code from index_constituents group by index_code
        ) as ic on index_details.index_code = ic.index_code
    """
    return db_conn.query_db(query=query)


def get_all_data(db_conn: MySqlConnector,
                 sim_start_date: datetime,
                 sim_end_date: datetime,
                 index_code: str):
    constituents = fetch_index_constituents(db_conn=db_conn,
                                            sim_start_date=sim_start_date,
                                            sim_end_date=sim_end_date,
                                            index_code=index_code)
    prices = fetch_prices(db_conn=db_conn,
                          securities_list=list(constituents["security_code"]),
                          start_date=sim_start_date,
                          end_date=sim_end_date)
    prices.index = pd.to_datetime(prices.index)
    return prices



