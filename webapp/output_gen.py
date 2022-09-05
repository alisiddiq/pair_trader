import pandas as pd
from plotly import graph_objs as go
from dash import html
from typing import List, Any


def plot_performance(performance_df: pd.DataFrame, chart_title: str) -> go.Figure:
    """
    Generate a plot of all the regression outputs
    """
    traces = [
        go.Scatter(
            x=performance_df.index,
            y=performance_df["strategy"],
            name="Strategy",
            line=dict(color="blue", width=4)
        ),
        go.Scatter(
            x=performance_df.index,
            y=performance_df["index"],
            name="Index",
            line=dict(color="red", width=4)
        ),
    ]
    layout = dict(
        title=chart_title,
        legend=dict(orientation="h"),
        font=dict(family='Quicksand', size=14),
        yaxis=dict(title="Returns")
    )
    return go.Figure(data=traces, layout=layout)


def _gen_single_data_row_for_table(row: pd.Series) -> List[Any]:
    """
    Generates a table row from the given row dict
    :param row: Data for the row
    :return: html.Td objects
    """
    return [html.Td(val) for val in row.to_dict().values()]


def gen_html_tbl_from_df(inp_df: pd.DataFrame) -> List[Any]:
    """
    Generates a table to show the user what they have already selected
    :param inp_df: Dataframe that needs to be converted to table
    :return: Returns header and rows of the table
    """
    # Making an empty column that will hold delete button
    header_cols = [html.Th(col) for col in inp_df.columns]
    tbl_header = [
        html.Thead(
            html.Tr(header_cols)
        )
    ]
    rows = [
        html.Tr(_gen_single_data_row_for_table(row))
        for ind, row in inp_df.iterrows()
    ]
    return tbl_header + rows
