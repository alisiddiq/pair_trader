from dash import html, dcc
import dash_bootstrap_components as dbc

LABEL_STYLE = {
    'fontWeight': 'bold',
    'margin': '5px',
    'fontSize': '18px'
}


def gen_layout():
    """
    Generate the full app layout
    """
    app_layout = html.Div([
        html.Div(
            style={'fontFamily': 'Quicksand'},
            children=[
                html.Div(
                    className='flex-container p-4',
                    children=[
                        html.Div(
                            className='row',
                            style={'margin-top': '-25px', 'margin-left': '-25px', 'height': '100vh'},
                            children=[
                                html.Div(
                                    className='col-sm-4',
                                    style={'backgroundColor': '#c8d1e6'},
                                    children=[
                                        html.Div(
                                            className='row',
                                            children=[
                                                html.Div(
                                                    id='title_div',
                                                    className='col-sm-12',
                                                    style={'margin-top': '20px'},
                                                    children=[
                                                        html.H1(
                                                            style={'fontWeight': 'bold',
                                                                   'fontFamily': 'Aboreto',
                                                                   'fontSize': '48px',
                                                                   'marginTop': '50px'},
                                                            children=['Pair Trader']
                                                        ),
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            className='row',
                                            children=[
                                                html.Div(
                                                    className='col-sm-12',
                                                    style={'margin-top': '20px'},
                                                    children=[
                                                        html.Div(
                                                            children=[
                                                                html.Label('Index',
                                                                           style=LABEL_STYLE),
                                                                dcc.Dropdown(
                                                                    id='index_dd',
                                                                    multi=False,
                                                                    clearable=False,
                                                                    options=[
                                                                        {"label": "NASDAQ 100", "value": "nasdaq100"},
                                                                        {"label": "SP 500", "value": "sp500"}],
                                                                    value="nasdaq100"
                                                                )
                                                            ])
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            className='row',
                                            children=[
                                                html.Div(
                                                    className='col-sm-12',
                                                    style={'margin-top': '20px'},
                                                    children=[
                                                        html.Div([
                                                            html.Label('Training Duration',
                                                                       style=LABEL_STYLE),
                                                            dcc.Dropdown(
                                                                id='train_duration_dd',
                                                                options=[{"label": "6 months", "value": 6},
                                                                         {"label": "12 months", "value": 12},
                                                                         {"label": "18 months", "value": 18},
                                                                         {"label": "24 months", "value": 24}],
                                                                value=6,
                                                                multi=False,
                                                                clearable=False
                                                            )
                                                        ])
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            className='row',
                                            children=[
                                                html.Div(
                                                    className='col-sm-12',
                                                    style={'margin-top': '20px'},
                                                    children=[
                                                        html.Div([
                                                            html.Label('Performance Test Start',
                                                                       style=LABEL_STYLE),
                                                            dcc.DatePickerSingle(
                                                                id='test_start_date_picker',
                                                                display_format='YYYY-MM-DD',
                                                                style={"width": "100%"}
                                                            ),
                                                        ])
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            className='row',
                                            children=[
                                                html.Div(
                                                    className='col-sm-12',
                                                    style={'margin-top': '20px'},
                                                    children=[
                                                        html.Div([
                                                            html.Label('Pair selection method',
                                                                       style=LABEL_STYLE),
                                                            dcc.Dropdown(
                                                                id='method_dd',
                                                                options=[{"label": "MDM", "value": "MDM"},
                                                                         {"label": "MFR", "value": "MFR"},
                                                                         {"label": "G", "value": "G"}],
                                                                value="MDM",
                                                                multi=False,
                                                                clearable=False
                                                            )
                                                        ])
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            className='row',
                                            children=[
                                                html.Div(
                                                    className='col-sm-12',
                                                    style={'margin-top': '20px'},
                                                    children=[
                                                        html.Div([
                                                            html.P([
                                                                html.B("MDM: "), "Select pairs where the sum of squared distances between cumulative returns of two stocks is the minimum",
                                                                html.Br(),
                                                                html.Br(),
                                                                html.B("MFR: "), "Select pairs with minimum market factor ratio, an indicator that is the ratio of market betas of the two stocks",
                                                                html.Br(),
                                                                html.Br(),
                                                                html.B("G: "), "Select pairs with minimum sum of p-value of 2 Granger-Causality tests. The test determines whether price of one stock is useful in predicting the price of another",
                                                                html.Br(),
                                                                html.Br(),
                                                                html.Br(),
                                                                "In each instance only top 5 pairs are selected for trading"
                                                            ],
                                                                style={'fontSize': '12px'})
                                                        ])
                                                    ]
                                                )
                                            ]
                                        ),
                                    ]
                                ),
                                # Output
                                html.Div(
                                    className='col-sm-8',
                                    children=[
                                        # Cache to store prices
                                        html.Script(
                                            id="securities_price_cache",
                                            type="text/json",
                                            children=[]
                                        ),
                                        # Cache to store the generated pairs
                                        html.Script(
                                            id="generated_pairs_cache",
                                            type="text/json",
                                            children=[]
                                        ),
                                        # Title Row
                                        html.Div(
                                            className="row",
                                            children=[
                                                html.Div(
                                                    className="col-sm-1",
                                                    style={"marginTop": "41px", "marginRight": "-30px"},
                                                    children=[
                                                        dbc.Spinner(color="dark",
                                                                    size="sm",
                                                                    children=[
                                                                        html.Div(id="output_spinner")
                                                                    ]),
                                                    ]
                                                ),
                                            ]
                                        ),
                                        # Pairs table
                                        html.Div(
                                            className="row",
                                            children=[
                                                html.Div(
                                                    className="col-sm-12",
                                                    children=[
                                                        dbc.Table(
                                                            id="pairs_summary_tbl",
                                                            style={"fontSize": "16px", "marginTop": "20px", "marginBottom": "20px"},
                                                            className="table-sm",
                                                            children=[]
                                                        )
                                                    ]
                                                ),
                                            ]
                                        ),
                                        # Strategy Controls
                                        html.Div(
                                            className="row",
                                            children=[
                                                html.Div(
                                                    className='col-sm-6',
                                                    children=[
                                                        html.Div([
                                                            html.Label('Window Size (Days)', style=LABEL_STYLE),
                                                            html.P("Determines what rolling window should be used to calculate the spread's mean and std",
                                                                    style={'fontStyle': 'italic', 'fontSize': '10px'}),
                                                            dcc.Slider(
                                                                id='window_slider',
                                                                min=10,
                                                                max=130,
                                                                step=10,
                                                                value=30,
                                                            ),
                                                        ])
                                                    ]
                                                ),
                                                html.Div(
                                                    className='col-sm-6',
                                                    children=[
                                                        html.Div([
                                                            html.Label('Long/Short position threshold',
                                                                       style=LABEL_STYLE),
                                                            html.P("Threshold used to enter/exit the trades (z-score). Lower value will be used to close the position, upper value will be used to enter the position",
                                                                style={'fontStyle': 'italic', 'fontSize': '10px'}),
                                                            dcc.RangeSlider(
                                                                id='std_slider',
                                                                min=0,
                                                                max=5,
                                                                step=0.5,
                                                                allowCross=False,
                                                                pushable=0.5,
                                                                value=[0,2]
                                                            )
                                                        ])
                                                    ]
                                                )
                                            ]
                                        ),
                                        # Chart
                                        html.Div(
                                            className="row",
                                            children=[
                                                html.Div(
                                                    className="col-sm-12",
                                                    children=[
                                                        dcc.Graph(
                                                            config={'displayModeBar': False},
                                                            id='output_plt',
                                                            style={'height': '50vh',
                                                                   'min-height': '300px',
                                                                   'min-width': '300px'}
                                                        )
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            className="row",
                                            children=[
                                                html.Div(
                                                    className="col-sm-12",
                                                    children=[
                                                        dbc.Table(
                                                            id="score_summary_tbl",
                                                            style={"fontSize": "16px", "marginTop": "20px"},
                                                            className="table-sm",
                                                            children=[]
                                                        )
                                                    ]
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )]
        )]
    )
    return app_layout
