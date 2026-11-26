import pandas as pd

def classify_regime(row):
    cpi   = row["CPI_YOY"]
    ffr   = row["FEDFUNDS"]
    usrec = row["USREC"]
    recpr = row["RECPROUSM156N"]

    if usrec==1 or recpr > 50:
        return "Recession"
    elif cpi > 5:
        return "High Inflation"
    elif cpi > 2.5 and ffr < cpi:
        return "Overheating"
    elif cpi < 1 and ffr < 1:
        return "Deflationary Risk"
    elif 1 <= cpi <= 2.5:
        return "Goldilocks"
    else:
        return "Reflation/Cooling"
    
def build_episodes(df):
    episodes = []
    current_regime = df["REGIME"].iloc[0]
    start_idx      = 0

    df["M2_YOY"] = df["M2SL"].pct_change(12) * 100

    for i, (date, row) in enumerate(df.iterrows()):
        if row["REGIME"] != current_regime or i == len(df) - 1:
            end_idx    = i
            episode_df = df.iloc[start_idx:end_idx]

            if len(episode_df) == 0:
                current_regime = row["REGIME"]
                start_idx      = i
                continue

            duration = len(episode_df)

            peak_cpi        = episode_df["CPI_YOY"].max()
            trough_cpi      = episode_df["CPI_YOY"].min()
            peak_real_ff    = episode_df["REAL_FEDFUNDS"].max()
            trough_real_ff  = episode_df["REAL_FEDFUNDS"].min()
            peak_oil        = episode_df["DCOILWTICO"].max()
            trough_oil      = episode_df["DCOILWTICO"].min()
            peak_unemp      = episode_df["UNRATE"].max()
            peak_10y        = episode_df["DGS10"].max()
            trough_spread   = episode_df["T10Y2Y"].min()

        
            extremes = pd.Series({
                "CPI_high"      : (episode_df["CPI_YOY"]       > 3.5).mean(),
                "CPI_low"       : (episode_df["CPI_YOY"]       < 1.0).mean(),
                "FF_negative"   : (episode_df["REAL_FEDFUNDS"] < 0  ).mean(),
                "curve_inverted": (episode_df["T10Y2Y"]        < 0  ).mean(),
                "unemp_high"    : (episode_df["UNRATE"]        > 6  ).mean(),
                "oil_high"      : (episode_df["oil_ret"]    > 0.50 ).mean(),
                "m2_high"       : (episode_df["M2_YOY"]        > 8  ).mean(),
                "breakeven_high": (episode_df["T10YIE"]        > 2.5).mean(),
            })

            diffusion_score = round(extremes.mean() * 100, 1)

            episodes.append({
                "regime"          : current_regime,
                "start"           : episode_df.index[0],
                "end"             : episode_df.index[-1],
                "duration_months" : duration,
                "duration_years"  : round(duration / 12, 1),
                "peak_cpi"        : round(peak_cpi,       2),
                "trough_cpi"      : round(trough_cpi,     2),
                "peak_real_ff"    : round(peak_real_ff,   2),
                "trough_real_ff"  : round(trough_real_ff, 2),
                "peak_oil"        : round(peak_oil,       2),
                "peak_unemp"      : round(peak_unemp,     2),
                "peak_10y"        : round(peak_10y,       2),
                "trough_spread"   : round(trough_spread,  2),
                "diffusion_score" : diffusion_score,
            })

            current_regime = row["REGIME"]
            start_idx      = i

    return pd.DataFrame(episodes)

def get_signal_date(daily_df, series, direction, threshold,
                    before_date, lookback_months=24):
    
    DAILY_SIGNALS = {
    "T10Y2Y"          : ("crosses_below", 0,    "Yield curve inverts"),
    "T10YIE"          : ("crosses_above", 2.5,  "10yr breakeven > 2.5%"),
    "T5YIE"           : ("crosses_above", 2.0,  "5yr breakeven > 2.0%"),
    "OIL_YOY"         : ("crosses_above", 50,   "Oil up >50% YoY"),
    "DTWEXBGS_ZSCORE" : ("crosses_below", -1.5, "USD 1.5σ below rolling mean"),
    "DGS10"           : ("crosses_above", 4.0,  "10yr yield > 4%"),
    "DFII10"          : ("crosses_below", 0,    "Real yield goes negative"),
}


    if series not in daily_df.columns:
        return None, None

    window_start = before_date - pd.DateOffset(months=lookback_months)
    window = daily_df.loc[window_start:before_date, series].dropna()

    if len(window) == 0:
        return None, None

    if direction == "crosses_below":
        crossed = window[window < threshold]
    else:
        crossed = window[window > threshold]

    if len(crossed) == 0:
        return None, None

    first_cross = crossed.index[0]
    value       = round(crossed.iloc[0], 3)

    return first_cross, value

def get_signal_df(final_daily_signals,transitions_df):

    DAILY_SIGNALS = {
    "T10Y2Y"          : ("crosses_below", 0,    "Yield curve inverts"),
    "T10YIE"          : ("crosses_above", 2.5,  "10yr breakeven > 2.5%"),
    "T5YIE"           : ("crosses_above", 2.0,  "5yr breakeven > 2.0%"),
    "OIL_YOY"         : ("crosses_above", 50,   "Oil up >50% YoY"),
    "DTWEXBGS_ZSCORE" : ("crosses_below", -1.5, "USD 1.5σ below rolling mean"),
    "DGS10"           : ("crosses_above", 4.0,  "10yr yield > 4%"),
    "DFII10"          : ("crosses_below", 0,    "Real yield goes negative"),
}


    results = []

    for _, trans in transitions_df.iterrows():
        from_regime     = trans["from_regime"]
        to_regime       = trans["to_regime"]
        transition_date = pd.Timestamp(trans["transition_date"])

        for series, (direction, threshold, interpretation) in DAILY_SIGNALS.items():
            signal_date, signal_value = get_signal_date(
                daily_df        = final_daily_signals,
                series          = series,
                direction       = direction,
                threshold       = threshold,
                before_date     = transition_date,
                lookback_months = 24,
            )

            if signal_date is not None:
                lead_days = (transition_date - signal_date).days
                results.append({
                    "from_regime"    : from_regime,
                    "to_regime"      : to_regime,
                    "transition_date": transition_date,
                    "signal"         : series,
                    "interpretation" : interpretation,
                    "signal_date"    : signal_date,
                    "signal_value"   : signal_value,
                    "lead_days"      : lead_days,
                    "lead_months"    : round(lead_days / 30.44, 1),
                })
            else:
                # log misses too — useful for understanding signal gaps
                results.append({
                    "from_regime"    : from_regime,
                    "to_regime"      : to_regime,
                    "transition_date": transition_date,
                    "signal"         : series,
                    "interpretation" : interpretation,
                    "signal_date"    : None,
                    "signal_value"   : None,
                    "lead_days"      : None,
                    "lead_months"    : None,
                })

    return pd.DataFrame(results)

