import dash
import pandas as pd
from dash.dependencies import Input, Output, State
from flask import Flask
from typing import Union, List
from data_process.db_connector.mysql_connector import MySqlConnector
from data_process.data_fetcher import fetch_securities
from strategy import pairs_selection, backtesting
from webapp import app_layout, output_gen
from datetime import datetime
from pathlib import Path
import os

curr_dir_path = Path(__file__).resolve().parent
server = Flask(__name__)
external_stylesheets = ["https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css",
                        "https://fonts.googleapis.com/css?family=Quicksand:400,700&display=swap",
                        "https://fonts.googleapis.com/css?family=Aboreto:400,700&display=swap",
                        ]
external_scripts = ["https://code.jquery.com/jquery-3.3.1.slim.min.js",
                    "https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js",
                    "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"]
app = dash.Dash(__name__,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                external_stylesheets=external_stylesheets,
                external_scripts=external_scripts,
                server=server)
app.config["suppress_callback_exceptions"] = True
app.title = "Pair Trader"
app.layout = app_layout.gen_layout()
db_conn = MySqlConnector(conn_json_path=os.path.join(curr_dir_path.parent, "db_conn_details.json"))
index_data = pd.DataFrame()


def update_index_details():
    global index_data
    # This is used to determine when the simulations can start for each exchange
    index_data = fetch_securities.fetch_indices(db_conn=db_conn).set_index("index_code")

update_index_details()


@app.callback([Output("test_start_date_picker", "date"),
               Output("test_start_date_picker", "min_date_allowed"),
               Output("test_start_date_picker", "max_date_allowed")],
               [Input("index_dd", "value"),
                Input("train_duration_dd", "value")])
def set_test_date_ranges(selected_index: str, training_period: int):
    """
    Sets the min/max test dates depending on the chosen index, based on how much data is available
    """
    chosen_index_details = index_data.loc[selected_index]
    min_snapshot_date = chosen_index_details["min_snapshot_date"].date()
    default_test_duration_months = 6
    # Adding 1 as a buffer to cover mid month dates
    min_allowed_test_start_date = min_snapshot_date + pd.offsets.MonthBegin(training_period + 1)
    # Get the start of previous month as the max test start date
    max_allowed_test_start_date = pd.Timestamp.today().normalize() - pd.offsets.MonthBegin(2)
    # Adding 1 as a buffer to cover mid month dates
    default_test_start_date = pd.to_datetime(pd.Timestamp.today().normalize() - pd.offsets.MonthBegin(default_test_duration_months + 1))
    return default_test_start_date, min_allowed_test_start_date, max_allowed_test_start_date

@app.callback([Output("securities_price_cache", "children"),
               Output("generated_pairs_cache", "children"),
               Output("output_spinner", "children")],
              [Input("index_dd", "value"),
               Input("train_duration_dd", "value"),
               Input("test_start_date_picker", "date"),
               ])
def fetch_and_store_prices(selected_index: str, training_duration: int, test_start_date: Union[datetime, str]):
    """
    Fetches the appropriate prices and caches them into the DOM
    """
    fetch_start_date = pd.to_datetime(test_start_date) - pd.offsets.MonthBegin(training_duration + 1)
    fetch_end_date = pd.Timestamp.today().normalize()
    fetched_prices = fetch_securities.get_all_data(db_conn=db_conn,
                                                   sim_start_date=fetch_start_date,
                                                   sim_end_date=fetch_end_date,
                                                   index_code=selected_index)
    index_price = fetch_securities.fetch_prices(db_conn=db_conn,
                                                securities_list=[index_data.loc[selected_index]["security_code"]],
                                                start_date=fetch_start_date,
                                                end_date=fetch_end_date)
    fetched_prices["index"] = index_price
    generated_pairs = pairs_selection.generate_pairs_and_scores(prices_df=fetched_prices)
    generated_pairs_json = generated_pairs.reset_index().to_json(orient="records")
    fetched_prices = fetched_prices.reset_index()
    fetched_prices["close_date"] = fetched_prices["close_date"].dt.strftime("%Y-%m-%d")
    prices_json = fetched_prices.to_json(orient="records")
    return prices_json, generated_pairs_json, ""



@app.callback(Output("pairs_summary_tbl", "children"),
              [Input("generated_pairs_cache", "children"),
               Input("method_dd", "value")])
def generate_pairs_summary_table(cached_pairs_metrics: str, chosen_method: str):
    """
    Generate the table to display the selected pairs
    """
    pairs_df = pd.read_json(cached_pairs_metrics).set_index("PAIR")
    selected_pairs = pairs_selection.select_top_n_pairs(generated_pairs_df=pairs_df,
                                                        selection_method=chosen_method,
                                                        n=5).round(4).reset_index()
    selected_pairs["PAIR"] = selected_pairs["PAIR"].str.replace("\|", ", ")
    return output_gen.gen_html_tbl_from_df(selected_pairs)


@app.callback([Output("output_plt", "figure"),
               Output("score_summary_tbl", "children")],
              [Input("generated_pairs_cache", "children"),
               Input("securities_price_cache", "children"),
               Input("method_dd", "value"),
               Input("window_slider", "value"),
               Input("std_slider", "value")],
               [State("test_start_date_picker", "date"),
                State("index_dd", "value"),])
def generate_performance_plot(cached_pairs_metrics: str,
                              cached_prices: str,
                              chosen_method: str,
                              window_size: int,
                              z_score_range: List[int],
                              test_start_date: Union[datetime, str],
                              selected_index: str):
    """
    Generate the graph of performance comparison
    """
    prices_df = pd.read_json(cached_prices).set_index("close_date")
    prices_df.index = pd.to_datetime(prices_df.index)
    pairs_df = pd.read_json(cached_pairs_metrics).set_index("PAIR")
    selected_pairs = pairs_selection.select_top_n_pairs(generated_pairs_df=pairs_df,
                                                        selection_method=chosen_method,
                                                        n=5)
    strategy_performance = backtesting.get_performance(chosen_pairs=list(selected_pairs.index),
                                                       prices_df=prices_df,
                                                       test_start_date=pd.to_datetime(test_start_date),
                                                       window_size=window_size,
                                                       open_threshold=z_score_range[1],
                                                       close_threshold=z_score_range[0])
    performance_metrics = backtesting.gen_performance_metrics(performance_df=strategy_performance).round(3)
    index_full_name = index_data.loc[selected_index]["index_name"]
    performance_metrics["Type"] = performance_metrics["Type"].str.title().replace("Index", index_full_name)
    perf_metrics_tbl = output_gen.gen_html_tbl_from_df(performance_metrics)
    perf_chart = output_gen.plot_performance(performance_df=strategy_performance,
                                             chart_title=f"Strategy {chosen_method} performance vs. {index_full_name}")

    return perf_chart, perf_metrics_tbl


## RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
