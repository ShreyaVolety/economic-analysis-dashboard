import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash_plots import *
from calculation import *
from data_read import *
from explanation_cards import *

df, final_daily, final_monthly, final_weekly = read_latest_data()
df['oil_ret'] = df["DCOILWTICO"].pct_change(fill_method=None)
df["REGIME"] = df.apply(classify_regime, axis=1)
ticker_info = pd.read_csv('tickers.csv',index_col=0)
df = df.copy()
if "Date" not in df.columns:
    df = df.reset_index()
df = df.rename(columns={
    "index": "Date",
    "DATE": "Date",
})

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date")

index_df = df.copy()
index_df.index = index_df['Date']
index_df.index = pd.to_datetime(index_df.index)
index_df = index_df.drop(columns=['Date'])
episodes_df = build_episodes(index_df)

swimlane_fig = make_swimlane(episodes_df)
depth_fig = recession_depth(episodes_df)
diffusion_fig = recession_diffusion(episodes_df)

final_daily["OIL_YOY"] = final_daily["DCOILWTICO"].pct_change(252,fill_method=None) * 100  
window = 252
final_daily["OIL_ZSCORE"] = (
    (final_daily["DCOILWTICO"] - final_daily["DCOILWTICO"].rolling(window).mean())
    / final_daily["DCOILWTICO"].rolling(window).std()
)
final_daily["OIL_VS_52WK"] = (
    final_daily["DCOILWTICO"] / final_daily["DCOILWTICO"].rolling(252).max() - 1
) * 100

final_daily['Date'] = pd.to_datetime(final_daily['Date'])
final_daily_signals = final_daily.set_index('Date').sort_index()

transitions = []

for i in range(len(episodes_df) - 1):
    transitions.append({
        "from_regime"    : episodes_df.iloc[i]["regime"],
        "to_regime"      : episodes_df.iloc[i + 1]["regime"],
        "transition_date": episodes_df.iloc[i + 1]["start"],
    })

transitions_df = pd.DataFrame(transitions)

ZSCORE_WINDOW = 252

for series in ["DCOILWTICO", "DTWEXBGS", "DGS10"]:
    roll_mean = final_daily_signals[series].rolling(ZSCORE_WINDOW).mean()
    roll_std  = final_daily_signals[series].rolling(ZSCORE_WINDOW).std()
    final_daily_signals[f"{series}_ZSCORE"] = (
        (final_daily_signals[series] - roll_mean) / roll_std
    )

signals_df = get_signal_df(final_daily_signals,transitions_df)

lead_summary = (
    signals_df
    .dropna(subset=["lead_months"])
    .groupby(["signal", "interpretation"])
    .agg(
        avg_lead_months    = ("lead_months", "mean"),
        median_lead_months = ("lead_months", "median"),
        n_transitions      = ("lead_months", "count"),
        min_lead_months    = ("lead_months", "min"),
        max_lead_months    = ("lead_months", "max"),
        hit_rate           = ("lead_months", "count"),
    )
    .round(1)
    .sort_values("avg_lead_months", ascending=False)
)

n_transitions = len(transitions_df)
lead_summary["hit_rate"] = (lead_summary["hit_rate"] / n_transitions * 100).round(1)
lead_summary["hit_rate"] = lead_summary["hit_rate"].astype(str) + "%"


RECESSION_REGIMES = ["Recession"]  # change/add names based on your regime labels

recession_signals_df = signals_df[
    signals_df["to_regime"].isin(RECESSION_REGIMES)
].copy()

lead_summary_recession = (
    recession_signals_df
    .groupby(["signal", "interpretation"], as_index=False)
    .agg(
        avg_lead_months=("lead_months", "mean"),
        median_lead_months=("lead_months", "median"),
        n_recession_transitions=("transition_date", "nunique"),
        std_lead=("lead_months", "std"),
        hits=("lead_months", lambda x: x.notna().sum()),
        min_lead_months=("lead_months", "min"),
        max_lead_months=("lead_months", "max"),
    )
)

lead_summary_recession["hit_rate"] = (
    lead_summary_recession["hits"]
    / lead_summary_recession["n_recession_transitions"]
)

scatter_indicators_fig = make_signal_scatter_plot(lead_summary_recession)

#!pip install jupyter_dash

from dash import Dash, html, dcc, dash_table, Input, Output, State
from dash import MATCH, ALL, ALLSMALLER
import plotly.express as px
from dash import callback_context
import datetime
from datetime import datetime
import pandas as pd

app = Dash(__name__)
server = app.server

EXCLUDE_TICKERS = ["CPIAUCSL", "CPILFESL", "PPIACO", "M2SL","PAYEMS","AHETPI"]
REGIME_BUTTON_MAP = {
    "btn-recession": "Recession",
    "btn-high-inflation": "High Inflation",
    "btn-overheating": "Overheating",
    "btn-deflationary": "Deflationary Risk",
    "btn-goldilocks": "Goldilocks",
    "btn-reflation": "Reflation/Cooling",
}

app.layout = html.Div([

    # HEADER
    html.Div([
        html.H1("Inflation Regime Analysis", className="page-title"),

        html.Div([
            html.A("Context on Data", href="#context", className="nav-link"),
            html.A("Regime Classification Visuals", href="#regimes", className="nav-link"),
            html.A("Recession Characteristics", href="#recession-characteristics", className="nav-link"),
            html.A("Recession Indicator Analysis", href="#recession-indicators", className="nav-link"),
        ], className="nav-bar")
    ], className="header"),

    # SECTION 1
    html.Section([
    html.H2("Context on Raw Data"),
    html.P("Available macroeconomic indicators from FRED. Each panel shows the historical time series and a short definition. Click on any of the subpanels to expand the block into a chart."),

    html.Div(
    id="ticker-mini-grid",
    children=[
        html.Div([
            html.Div([
                html.H4(row["Name"], className="mini-title"),
                html.P(row["Description"], className="mini-subtitle"),
            ], style={
                "cursor": "pointer",
                "userSelect": "none",
            }, id={"type": "mini-header", "index": row["Ticker"]}),

            html.Div(
                dcc.Graph(
                    figure=make_mini_fig(row["Ticker"], row["Name"]),
                    config={"displayModeBar": False},
                    className="mini-graph"
                ),
                id={"type": "mini-graph-container", "index": row["Ticker"]},
                style={"display": "none"},  # collapsed by default
            )
        ], className="mini-card")
        for _, row in ticker_info.iterrows()
    ],
    className="mini-grid"
)
], id="context", className="section"),

    # SECTION 2
    html.Section([
    html.H2("Regime Anatomy: Inflation, Policy, Labor, and Market Stress"),

    html.Div([
        html.Button("Recession", id="btn-recession", n_clicks=0, className="regime-btn"),
        html.Button("High Inflation", id="btn-high-inflation", n_clicks=0, className="regime-btn"),
        html.Button("Overheating", id="btn-overheating", n_clicks=0, className="regime-btn"),
        html.Button("Deflationary Risk", id="btn-deflationary", n_clicks=0, className="regime-btn"),
        html.Button("Goldilocks", id="btn-goldilocks", n_clicks=0, className="regime-btn"),
        html.Button("Reflation/Cooling", id="btn-reflation", n_clicks=0, className="regime-btn"),
    ], className="regime-button-row"),


    html.Div([
    html.Div(dcc.Graph(figure=swimlane_fig), style={"flex": "2"}),
    html.Div(
        html.Iframe(srcDoc=classifier_html, style={"width":"100%","height":"300px","border":"none"}),
        style={"flex": "1", "paddingLeft": "20px"}
    ),
], style={"display": "flex", "gap": "20px", "marginTop": "20px", "alignItems": "flex-start"}),

    html.H3(id="selected-regime-title", className="selected-regime-title"),

    html.Div(
    [
        html.Strong("How to read density plots: "),
        "Taller regions indicate values that occurred more frequently during the selected regime. Density reflects concentration of observations, not probability itself."
    ],
    className="density-callout"
),

html.Div([html.Br()]),

    dcc.Store(id="selected-regime-store", data="Goldilocks"),

    html.Div([
        dcc.Graph(id="regime-cpi-dist", config={"displayModeBar": False}),
        dcc.Graph(id="regime-realff-dist", config={"displayModeBar": False}),
        dcc.Graph(id="regime-unrate-dist", config={"displayModeBar": False}),
    ], className="three-grid"),

    html.Div([html.Br()]),

    html.Div([
    dcc.Graph(
    id="regime-gold-vol",
    config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False}
),

dcc.Graph(
    id="regime-oil-vol",
    config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False}
)
], className="commodity-grid"),

html.Div([html.Br()]),
html.Div([
    
    # LEFT: dropdown + additional metric
    html.Div([
        html.Div([
            html.Label("Select an additional metric:", className="dropdown-label"),
            dcc.Dropdown(
                id="additional-metric-dropdown",
                options=[
                    {"label": f"{row['Name']} ({row['Ticker']})", "value": row["Ticker"]}
                    for _, row in ticker_info.iterrows()
                    if (
                        (row["Ticker"] in df.columns or row["Ticker"] in final_daily.columns)
                        and row["Ticker"] not in EXCLUDE_TICKERS
                    )
                ],
                value="T10Y2Y",
                clearable=False,
                className="metric-dropdown"
            ),
        ], className="dropdown-wrap"),

        dcc.Graph(
            id="additional-metric-plot",
            config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False}
        )

    ], className="half-panel"),
    # RIGHT: labor dynamics
    html.Div([
        html.H3("Labor Market Dynamics", className="selected-regime-title"),
        dcc.Graph(
            id="labor-dynamics-plot",
            config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False}
        )
    ], className="half-panel"),

], className="two-panel-row"),

# ✅ THIS WAS MISSING
], id="regimes", className="section"),

    # SECTION 3
    html.Section([
    html.H2("Recession Characteristics - Depth, Diffusion, Duration"),
    html.Ul([
    html.Li("Recession Depth: How severe the economic decline is during a recession."),
    html.Li("Recession Diffusion: How widespread the weakness is across the economy."),
    html.Li("Recession Duration: How long the recession lasts, typically measured in months from peak to trough.")]),


    html.Div([
    html.Div(dcc.Graph(figure=diffusion_fig), style={"flex": "2"}),
    html.Div(
        html.Iframe(
            srcDoc=diffusion_card_html,
            style={"width": "100%", "height": "420px", "border": "none"}
        ),
        style={"flex": "1", "paddingLeft": "20px"}
    ),
], style={"display": "flex", "gap": "20px", "alignItems": "flex-start"}),

    # Row 2 — 1 figure full width
    html.Div([
        dcc.Graph(figure=depth_fig)
    ]),

], id="recession-characteristics", className="section"),

    # SECTION 4
    html.Section([
        html.H2("Recession Indicator Analysis"),

        html.Div([
              html.Div(dcc.Graph(figure=scatter_indicators_fig, style={"flex": "2"})),
              html.Div(
        html.Iframe(
            srcDoc=signal_card_html,
            style={"width": "100%", "height": "520px", "border": "none"}
        ),
        style={"flex": "1", "paddingLeft": "20px"}
    ),
], style={"display": "flex", "gap": "20px", "alignItems": "flex-start"}),


], id="recession-indicators", className="section"),

], className="app-container")

@app.callback(
    Output({"type": "mini-graph-container", "index": MATCH}, "style"),
    Input({"type": "mini-header", "index": MATCH}, "n_clicks"),
    State({"type": "mini-graph-container", "index": MATCH}, "style"),
    prevent_initial_call=True,
)
def toggle_mini_graph(n_clicks, current_style):
    if current_style.get("display") == "none":
        return {"display": "block"}
    return {"display": "none"}

@app.callback(
    Output("selected-regime-store", "data"),
    [Input(btn_id, "n_clicks") for btn_id in REGIME_BUTTON_MAP.keys()]
)
def store_selected_regime(*clicks):
    ctx = callback_context

    if not ctx.triggered:
        return "Goldilocks"

    btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return REGIME_BUTTON_MAP.get(btn_id, "Goldilocks")

@app.callback(
    Output("selected-regime-title", "children"),
    Output("regime-cpi-dist", "figure"),
    Output("regime-realff-dist", "figure"),
    Output("regime-unrate-dist", "figure"),
    Output("regime-gold-vol", "figure"),
    Output("regime-oil-vol", "figure"),
    Output("additional-metric-plot", "figure"),
    Output("labor-dynamics-plot", "figure"),
    Input("selected-regime-store", "data"),
    Input("additional-metric-dropdown", "value")
)
def update_regime_graphs(selected_regime,selected_ticker):

    dff = df[df["REGIME"] == selected_regime].copy()

    cpi_fig = make_distribution_fig(
        dff,
        "CPI_YOY",
        selected_regime,
        f"CPI YoY Density Distribution — {selected_regime}",
        "CPI YoY (%)"
    )

    realff_fig = make_distribution_fig(
        dff,
        "REAL_FEDFUNDS",
        selected_regime,
        f"Real Fed Funds Density Distribution — {selected_regime}",
        "Real Fed Funds (%)"
    )

    unrate_fig = make_distribution_fig(
        dff,
        "UNRATE",
        selected_regime,
        f"Unemployment Density Distribution — {selected_regime}",
        "Unemployment Rate (%)"
    )

    gold_fig, oil_fig = make_vol_episode_boxplots(final_daily, df, selected_regime)

    additional_fig = make_additional_metric_fig(
        df, final_daily, ticker_info, selected_ticker, selected_regime
    )

    labor_fig = make_labor_regime_scatter(df,selected_regime)

    return (
        f"Selected Regime: {selected_regime}",
        cpi_fig,
        realff_fig,
        unrate_fig,
        gold_fig,
        oil_fig,
        additional_fig,
        labor_fig
    )


if __name__ == "__main__":
    app.run(debug=True, port=8052)
