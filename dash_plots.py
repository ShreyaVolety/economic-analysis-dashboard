import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
from datetime import datetime
from dash import dash_table

# using this palette throughout plots
REGIME_COLORS = {
    "Goldilocks"       : "#69b34c",
    "Reflation/Cooling": "#acb334",
    "Overheating"      : "#fab733",
    "High Inflation"   : "#ff8e15",
    "Deflationary Risk": "#ff4e11",
    "Recession"        : "#ff0d0d",
}


#--------------------SECTION 1 ----------------------------------------#
#----------------------------------------------------------------------#
#making data context plots
def make_mini_fig(ticker, name):
    fig = go.Figure()

    #reading from raw_data stored - last pull is being hardcode, but in the future data can be auto-refreshed

    df = pd.read_csv(f'raw_data/latest_pull_{ticker}_2026-05-06.csv',index_col=0)
    df = df.reset_index()
    df.columns = ['Date',ticker]

    fig.add_trace(go.Scatter(
        
        x=df["Date"],
        y=df[ticker],
        mode="lines",
        line=dict(color="#a2bffe", width=1),
        hovertemplate=(
            "Date: %{x}<br>"
            f"{ticker}: " + "%{y:.2f}<extra></extra>"
        )
    ))

    fig.update_layout(
        template="plotly_white",height=180,margin=dict(l=38, r=12, t=8, b=30),paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        xaxis=dict(
            title="Date",
            title_font=dict(size=9),
            tickfont=dict(size=8),
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title=ticker,
            title_font=dict(size=9),
            tickfont=dict(size=8),
            showgrid=True,
            gridcolor="#eeeeee",
            zeroline=False
        )
    )

    return fig

#making regime classification time-line plot
def make_swimlane(episodes: pd.DataFrame) -> go.Figure:

    df = episodes.copy()
    df["start"] = pd.to_datetime(df["start"])
    df["end"]   = pd.to_datetime(df["end"])

    regimes   = list(REGIME_COLORS.keys())
    lane_map  = {r: i for i, r in enumerate(regimes)}
    seen      = set()
    traces    = []

    for _, row in df.iterrows():
        regime = row["regime"]
        if regime not in lane_map:
            continue
    
        color      = REGIME_COLORS[regime]
        lane_y     = lane_map[regime]
        show_leg   = regime not in seen
        seen.add(regime)

        tooltip = (
            f"<b>{regime}</b><br>"
            f"Start: {row['start'].strftime('%b %Y')}<br>"
            f"End:   {row['end'].strftime('%b %Y')}<br>"
            f"Duration: {int(row['duration_months'])}m<br>"
            f"CPI Max: {row['peak_cpi']}%<br>"
            f"CPI Min: {row['trough_cpi']}%"
        )

        traces.append(go.Bar(
            x          = [( row["end"] - row["start"]).total_seconds() * 1000],
            y          = [lane_y],
            base       = [row["start"].value//10**6],
            orientation= "h",
            marker_color    = color,
            marker_opacity  = 0.65,
            marker_line_width = 0,
            name            = regime,
            legendgroup     = regime,
            showlegend      = show_leg,
            hovertemplate   = tooltip + "<extra></extra>",
            width           = 0.6,
        ))

    fig = go.Figure(traces)
    fig.update_layout(
        barmode   = "overlay",
        bargap    = 0.3,
        xaxis     = dict(
            type      = "date",
            tickformat= "%Y",
            dtick     = "M120",  # every 10 years
            gridcolor = "rgba(0,0,0,0.08)",
            showgrid  = True,
        ),
        yaxis = dict(
            tickvals = list(lane_map.values()),
            ticktext = list(lane_map.keys()),
            autorange= "reversed",
            showgrid = False,
        ),
        legend = dict(
            orientation = "h",
            yanchor     = "bottom",
            y           = 1.02,
            xanchor     = "left",
            x           = 0,
        ),
        plot_bgcolor  = "white",
        paper_bgcolor = "white",
        margin        = dict(l=130, r=20, t=60, b=40),
        height        = 320,
    )
    return fig


#making 3 distribution plots for callback in recession classification section
def make_distribution_fig(dff, col, regime, title, x_label):
    
    color = REGIME_COLORS[regime]
    data = dff[col].dropna()

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=data,
        histnorm="probability density",
        nbinsx=30,
        marker=dict(color=color, opacity=0.45),
        name=title
    ))

    # plotting mean line
    mean_val = data.mean()
    median_val = data.median()
    fig.add_trace(go.Scatter(
        x=[mean_val, mean_val],
        y=[0, 1],  # full height
        mode="lines",
        line=dict(color=color, dash="dash", width=2),
        name=f"Mean: {mean_val:.1f}",
        showlegend=False
    ))

    # plotting median line
    fig.add_trace(go.Scatter(
        x=[median_val, median_val],
        y=[0, 1],
        mode="lines",
        line=dict(color=color, dash="dot", width=2),
        name=f"Median: {median_val:.1f}",
        showlegend=False
))

    fig.update_layout(
        title=dict(text=title, font=dict(size=15), x=0.02),
        template="plotly_white",
        height=320,
        margin=dict(l=45, r=20, t=55, b=45),
        showlegend=False,
        xaxis_title=x_label,
        bargap=0.04
    )

    return fig

#--- helper functions for additional shaded time series plots -----

#calculating bands for each regime as start:end windows
def get_regime_bands(base_df, regime):
    bands = []
    in_band = False
    start = None

    for i in range(len(base_df)):
        is_regime = base_df["REGIME"].iloc[i] == regime
        date = base_df["Date"].iloc[i]

        if is_regime and not in_band:
            start = date
            in_band = True

        elif not is_regime and in_band:
            end = base_df["Date"].iloc[i - 1]
            bands.append((start, end))
            in_band = False

    if in_band:
        bands.append((start, base_df["Date"].iloc[-1]))

    return bands

#clipping bands based on data availability for each data point 
# - different data is available for different time periods based on inception of the index
def clip_bands(bands, start_date, end_date):
    clipped = []

    for start, end in bands:
        clipped_start = max(start, start_date)
        clipped_end = min(end, end_date)

        if clipped_start <= clipped_end:
            clipped.append((clipped_start, clipped_end))

    return clipped

#adding hover on the shaded bands for additional info
def add_bands_with_hover(fig, bands, data_df, date_col, value_col, color, regime, metric_label):
    y_min = data_df[value_col].min()
    y_max = data_df[value_col].max()

    for start, end in bands:
        window = data_df[
            (data_df[date_col] >= start) &
            (data_df[date_col] <= end)
        ][value_col].dropna()

        if window.empty:
            continue

        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor=color,
            opacity=0.14,
            line_width=0,
            layer="below"
        )

        fig.add_trace(go.Scatter(
            x=[start, end, end, start, start],
            y=[y_min, y_min, y_max, y_max, y_min],
            fill="toself",
            mode="none",
            fillcolor="rgba(0,0,0,0)",
            hoveron="fills",
            hoverinfo="text",
            text=(
                f"<b>{regime} Period</b><br>"
                f"Start: {start.strftime('%Y-%m-%d')}<br>"
                f"End: {end.strftime('%Y-%m-%d')}<br><br>"
                f"<b>{metric_label}</b><br>"
                f"Mean: {window.mean():.2f}<br>"
                f"Median: {window.median():.2f}<br>"
                f"Min: {window.min():.2f}<br>"
                f"Max: {window.max():.2f}"
            ),
            showlegend=False
        ))

    return fig

#adding time span controls for additional viewing depths
def add_time_controls(fig, title, yaxis_title):
    fig.update_layout(
        title=dict(text=title, font=dict(size=15), x=0.02),
        template="plotly_white",
        height=430,
        margin=dict(l=55, r=20, t=75, b=45),
        showlegend=False,
        dragmode="zoom",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10)
        ),
        xaxis=dict(
            title="Date",
            type="date",
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(count=10, label="10Y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            )
        ),
        yaxis=dict(title=yaxis_title)
    )

    return fig

#--- helper functions: done -----

#plotting additional metric figures

def make_additional_metric_fig(df, final_daily, ticker_info, selected_ticker, regime):

    color = REGIME_COLORS[regime]

    base_df = df.copy()
    base_df["Date"] = pd.to_datetime(base_df["Date"])
    base_df = base_df.sort_values("Date")

    # use df first, otherwise final_daily
    if selected_ticker in base_df.columns:
        plot_df = base_df[["Date", selected_ticker]].copy()
    else:
        plot_df = final_daily[["Date", selected_ticker]].copy()

    plot_df = plot_df.dropna(subset=[selected_ticker])
    plot_df["Date"] = pd.to_datetime(plot_df["Date"])
    plot_df = plot_df.sort_values("Date")

    metric_row = ticker_info[ticker_info["Ticker"] == selected_ticker]

    if len(metric_row) > 0:
        metric_name = metric_row.iloc[0]["Name"]
    else:
        metric_name = selected_ticker

    regime_bands = get_regime_bands(base_df, regime)
    clipped = clip_bands(
        regime_bands,
        plot_df["Date"].min(),
        plot_df["Date"].max()
    )

    fig = go.Figure()

    fig = add_bands_with_hover(
        fig,
        clipped,
        plot_df,
        "Date",
        selected_ticker,
        color,
        regime,
        metric_name
    )

    fig.add_trace(go.Scatter(
        x=plot_df["Date"],
        y=plot_df[selected_ticker],
        mode="lines",
        name=metric_name,
        line=dict(color="black", width=1.5),
        hovertemplate=(
            "Date: %{x}<br>"
            f"{selected_ticker}: " + "%{y:.2f}<extra></extra>"
        )
    ))

    fig = add_time_controls(
        fig,
        f"{metric_name} During {regime}",
        selected_ticker
    )

    return fig

#commodity plots
def make_vol_episode_boxplots(final_daily, df, regime):
    color = REGIME_COLORS[regime]

    base_df = df.copy()
    base_df["Date"] = pd.to_datetime(base_df["Date"])
    base_df = base_df.sort_values("Date")

    gold_df = final_daily[["Date", "GVZCLS"]].copy()
    gold_df["Date"] = pd.to_datetime(gold_df["Date"])
    gold_df = gold_df.dropna(subset=["GVZCLS"]).sort_values("Date")

    oil_df = final_daily[["Date", "DCOILWTICO"]].copy()
    oil_df["Date"] = pd.to_datetime(oil_df["Date"])
    oil_df = oil_df.dropna(subset=["DCOILWTICO"]).sort_values("Date")

    oil_df["oil_ret"] = oil_df["DCOILWTICO"].pct_change()
    oil_df["oil_vol"] = (
        oil_df["oil_ret"]
        .rolling(30, min_periods=20)
        .std()
        * np.sqrt(252)
        * 100
    )

    # identify continuous selected-regime bands
    bands = []
    in_band = False
    start = None

    for i in range(len(base_df)):
        is_regime = base_df["REGIME"].iloc[i] == regime
        date = base_df["Date"].iloc[i]

        if is_regime and not in_band:
            start = date
            in_band = True

        elif not is_regime and in_band:
            end = base_df["Date"].iloc[i - 1]
            bands.append((start, end))
            in_band = False

    if in_band:
        bands.append((start, base_df["Date"].iloc[-1]))

    gold_fig = go.Figure()
    oil_fig = go.Figure()

    for start, end in bands:
        label = f"{start.year}-{end.year}"

        gold_window = gold_df[
            (gold_df["Date"] >= start) &
            (gold_df["Date"] <= end)
        ]["GVZCLS"].dropna()

        oil_window = oil_df[
            (oil_df["Date"] >= start) &
            (oil_df["Date"] <= end)
        ]["oil_vol"].dropna()

        if len(gold_window) > 0:
            gold_fig.add_trace(go.Box(
                y=gold_window,
                name=label,
                marker_color=color,
                boxmean=True,
                boxpoints="outliers",
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "Gold Vol: %{y:.2f}<extra></extra>"
                )
            ))

        if len(oil_window) > 0:
            oil_fig.add_trace(go.Box(
                y=oil_window,
                name=label,
                marker_color=color,
                boxmean=True,
                boxpoints="outliers",
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "Oil Vol: %{y:.2f}%<extra></extra>"
                )
            ))

    gold_fig.update_layout(
        title=dict(text=f"Gold Volatility by {regime} Episode", x=0.02, font=dict(size=15)),
        template="plotly_white",
        height=390,
        margin=dict(l=55, r=20, t=60, b=70),
        xaxis_title=f"{regime} Episode",
        yaxis_title="GVZCLS",
        showlegend=False
    )

    oil_fig.update_layout(
        title=dict(text=f"Oil Realized Volatility by {regime} Episode", x=0.02, font=dict(size=15)),
        template="plotly_white",
        height=390,
        margin=dict(l=55, r=20, t=60, b=70),
        xaxis_title=f"{regime} Episode",
        yaxis_title="Oil Vol (%)",
        showlegend=False
    )

    return gold_fig, oil_fig

def make_labor_regime_scatter(df, selected_regime):
    dff = df.copy()

    dff["Date"] = pd.to_datetime(dff["Date"])
    dff["PAYEMS_YOY"] = dff["PAYEMS"].pct_change(12) * 100
    dff["WAGE_YOY"] = dff["AHETPI"].pct_change(12) * 100
    dff["SIZE"] = np.clip(dff["PAYEMS_YOY"], -5, 5).abs()

    dff = dff[dff["REGIME"] == selected_regime].copy()
    dff = dff.dropna(subset=["JTSJOL", "WAGE_YOY", "PAYEMS_YOY"])

    color = REGIME_COLORS[selected_regime]

    fig = px.scatter(
        dff,
        x="JTSJOL",
        y="WAGE_YOY",
        size="SIZE",
        color_discrete_sequence=[color],
        hover_data={
            "Date": True,
            "JTSJOL": ":,.0f",
            "WAGE_YOY": ":.2f",
            "PAYEMS_YOY": ":.2f",
        },
        title=f"Labor Market Dynamics — {selected_regime}"
    )

    fig.update_layout(
        template="plotly_white",
        height=430,
        margin=dict(l=55, r=20, t=60, b=50),
        xaxis_title="Job Openings (JTSJOL)",
        yaxis_title="Wage Growth YoY (%)",
        showlegend=False
    )

    return fig

#--------------------SECTION 1 ----------------------------------------#
#----------------------------------------------------------------------#


#--------------------SECTION 2 ----------------------------------------#
#----------------------------------------------------------------------#

#building recession depth and duration heatmap
def recession_depth(episodes_df):  

    n = len(REGIME_COLORS)
    custom_rg = [
        [i / (n - 1), color]
        for i, color in enumerate(REGIME_COLORS.values())
        ]
    
    def hex_to_rgba(hex_color, alpha=0.85):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    custom_rg_faded = [
        [pos, hex_to_rgba(color, alpha=0.65)]
        for pos, color in custom_rg
    ]
    rec = episodes_df[episodes_df["regime"] == "Recession"].copy()
    rec["label"] = rec["start"].dt.strftime("%Y")

    metric_cols = {
        "Peak CPI (%)": "peak_cpi",
        "Trough Real FF (%)": "trough_real_ff",
        "Peak Unemployment (%)": "peak_unemp",
        "Trough Spread (%)": "trough_spread",
        "Duration (Months)": "duration_months"
    }

    heatmap_df = rec.set_index("label")[list(metric_cols.values())].T
    heatmap_df.index = list(metric_cols.keys())

    severity_df = heatmap_df.copy()

    #flipping signs of metrics that flow the other way in severity
    severity_df.loc["Peak CPI (%)"] = heatmap_df.loc["Peak CPI (%)"]
    severity_df.loc["Trough Real FF (%)"] = -heatmap_df.loc["Trough Real FF (%)"]
    severity_df.loc["Peak Unemployment (%)"] = heatmap_df.loc["Peak Unemployment (%)"]
    severity_df.loc["Trough Spread (%)"] = -heatmap_df.loc["Trough Spread (%)"]
    severity_df.loc["Duration (Months)"] = heatmap_df.loc["Duration (Months)"]

    #normalizing all metrics to use 1 scale
    norm_df = severity_df.apply(
        lambda row: (row - row.mean()) / row.std() if row.std() != 0 else row * 0,
        axis=1
    )

    fig = go.Figure(go.Heatmap(
        z=norm_df.values.tolist(),
        x=norm_df.columns.tolist(),
        y=norm_df.index.tolist(),
        colorscale=custom_rg_faded,
        text=[[f"{norm_df.iloc[i,j]:.1f}%" if pd.notna(norm_df.iloc[i,j]) else "" 
        for j in range(norm_df.shape[1])] 
        for i in range(norm_df.shape[0])],
        customdata=heatmap_df.values.tolist(),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Recession: %{x}<br>"
            "Raw Value: %{customdata:.2f}<br>"
            "Normalized Score: %{z:.2f}"
            "<extra></extra>"
        ),
        texttemplate="%{text}",
        textfont=dict(size=9, color="black"),

    ))

    fig.update_layout(
        title=dict(text="Recession Depth and Duration Indicators - Scored and Normalized", font=dict(size=15), x=0),
        margin=dict(t=80),
        yaxis=dict(autorange="reversed", showgrid=False),
        xaxis=dict(showgrid=False),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    return fig

#diffusion plot 
def recession_diffusion(episodes_df):

    rec = episodes_df[episodes_df["regime"] == "Recession"].copy()
    rec["label"] = rec["start"].dt.strftime("%Y")

    bar_colors = ["#ff0d0d"if v >= 50 else "#ff8e15" if v >= 25 else "#69b34c"
                for v in rec["diffusion_score"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rec["label"],
        y=rec["diffusion_score"],
        marker_color=bar_colors,
        opacity=0.65,
        width=0.5,
        text=[f"{v:.1f}%" for v in rec["diffusion_score"]],
        textposition="outside",
        textfont=dict(size=10, color="#1a1a1a", family="Arial Black"),
        showlegend=False
    ))

    fig.add_hline(
        y=25, line=dict(color="#e67e22", width=1.2, dash="dash"),
        opacity=0.7,
        annotation_text="Moderate (25%)",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#e67e22")
    )
    fig.add_hline(
        y=50, line=dict(color="#c0392b", width=1.2, dash="dash"),
        opacity=0.7,
        annotation_text="Severe (50%)",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#c0392b")
    )

    fig.update_layout(
        title=dict(
            text="DIFFUSION — % of Indicators Simultaneously Extreme",
            font=dict(size=13, color="#1a1a1a"),
            x=0,
            pad=dict(b=20)
        ),
        xaxis=dict(
            title="Recession Start Year",
            title_font=dict(size=11, color="#555"),
            showgrid=False,
            type="category"
        ),
        yaxis=dict(
            title="Diffusion Score (%)",
            title_font=dict(size=11, color="#555"),
            range=[0, 100],
            gridcolor="#cccccc",
            gridwidth=0.3,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=80, l=55, r=20, b=50),
        bargap=0.4,
        showlegend=False
    )

    return fig


#--------------------SECTION 2 ----------------------------------------#
#----------------------------------------------------------------------#


#--------------------SECTION 3 ----------------------------------------#
#----------------------------------------------------------------------#

def make_signal_scatter_plot(lead_summary_recession):
    plot_df = lead_summary_recession.copy()
    if plot_df["hit_rate"].dtype == "object":
        plot_df["hit_rate"] = (
            plot_df["hit_rate"]
            .str.replace("%", "", regex=False)
            .astype(float) / 100
        )
    elif plot_df["hit_rate"].max() > 1:
        plot_df["hit_rate"] = plot_df["hit_rate"] / 100

    label_map = {
        "DGS10": "10yr Yield",
        "T5YIE": "5yr Breakeven",
        "T10YIE": "10yr Breakeven",
        "T10Y2Y": "10Y-2Y Spread",
        "OIL_YOY": "Oil Price (YoY %)",
        "DTWEXBGS_ZSCORE": "USD Index (Rolling Z-Score)",
        "DFII10": "Real Yield (DFII10)"
    }

    plot_df["label"] = (
        plot_df["signal"]
        .map(label_map)
        .fillna(plot_df["signal"])
    )

    x_cut = 18
    y_cut = 0.50

    fig = px.scatter(
        plot_df,
        x="avg_lead_months",
        y="hit_rate",
        size="hits",
        size_max=34,
        hover_data={
            "signal": True,
            "avg_lead_months": ":.1f",
            "median_lead_months": ":.1f",
            "std_lead": ":.1f",
            "hit_rate": ":.1%",
            "hits": True,
            "n_recession_transitions": True,
        },
        title="Signal Quality: Lead Time vs Reliability",
    )

    fig.update_traces(
        marker=dict(
            color="#636EFA",
            opacity=0.88,
            line=dict(width=1, color="white")
        )
    )

    fig.add_hline(
        y=y_cut,
        line_dash="dash",
        line_color="#999999"
    )

    fig.add_vline(
        x=x_cut,
        line_dash="dash",
        line_color="#999999"
    )

    label_offsets = {
        "T10Y2Y": (0, 28),
        "OIL_YOY": (0, -30),
        "DGS10": (10, 20),
        "T5YIE": (0, 20),
        "T10YIE": (-60, 5),
        "DTWEXBGS_ZSCORE": (60, 15),
        "DFII10": (0, 28),
    }

    for _, row in plot_df.iterrows():

        dx, dy = label_offsets.get(row["signal"], (0, 18))

        fig.add_annotation(
            x=row["avg_lead_months"],
            y=row["hit_rate"],
            text=row["label"],
            showarrow=False,
            xshift=dx,
            yshift=dy,
            font=dict(
                size=12,
                color="#1f3b63"
            ),
            bgcolor="rgba(255,255,255,0.78)",
            bordercolor="rgba(255,255,255,0)",
        )

    x_min = plot_df["avg_lead_months"].min() - 1
    x_max = plot_df["avg_lead_months"].max() + 1

    fig.add_annotation(
        x=x_min,
        y=1.02,
        text="Late but Reliable",
        showarrow=False,
        xanchor="left",
        bgcolor="white",
        bordercolor="#cccccc"
    )

    fig.add_annotation(
        x=x_max,
        y=1.02,
        text="Early & Reliable",
        showarrow=False,
        xanchor="right",
        bgcolor="white",
        bordercolor="#cccccc"
    )

    fig.add_annotation(
        x=x_min,
        y=0.03,
        text="Late & Unreliable",
        showarrow=False,
        xanchor="left",
        bgcolor="white",
        bordercolor="#cccccc"
    )

    fig.add_annotation(
        x=x_max,
        y=0.03,
        text="Early but Noisy",
        showarrow=False,
        xanchor="right",
        bgcolor="white",
        bordercolor="#cccccc"
    )

    fig.update_layout(
        height=560,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        font=dict(
            family="Inter, Arial",
            size=14,
            color="#1f3b63"
        ),
        title=dict(
            x=0.5,
            font=dict(size=22)
        ),
    )

    fig.update_xaxes(
        title="Average Lead Time Before Recession (Months)",
        gridcolor="#e9eef5",
        range=[
            plot_df["avg_lead_months"].min() - 2,
            plot_df["avg_lead_months"].max() + 2
        ]
    )

    fig.update_yaxes(
        title="Recession Hit Rate",
        gridcolor="#e9eef5",
        tickformat=".0%",
        range=[0, 1.05]
    )

    return fig

#--------------------SECTION 3 ----------------------------------------#
#----------------------------------------------------------------------#