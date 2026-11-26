classifier_html = """
<html><head><style>
  body { font-family: sans-serif; margin: 0; padding: 1rem; background: #fff; color: #1a1a1a; }
  .card { border: 1px solid #e5e5e5; border-radius: 12px; padding: 1rem 1.25rem; }
  .header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; }
  .title { font-size: 14px; font-weight: 500; }
  .subtitle { font-size: 11px; color: #888; }
  .rule { display: flex; align-items: stretch; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
  .rule:last-child { border-bottom: none; padding-bottom: 0; }
  .rule:first-child { padding-top: 0; }
  .swatch { width: 4px; border-radius: 2px; flex-shrink: 0; }
  .rule-body { flex: 1; display: flex; flex-direction: column; gap: 4px; }
  .regime-name { font-size: 13px; font-weight: 500; }
  .condition { font-size: 12px; font-family: monospace; color: #555; background: #f5f5f5; border-radius: 4px; padding: 3px 7px; display: inline-block; }
  .note { font-size: 11px; color: #999; margin-top: 2px; }
  .priority { font-size: 10px; font-weight: 500; color: #bbb; min-width: 20px; text-align: right; flex-shrink: 0; padding-top: 2px; }
</style></head><body>
<div class="card">
  <div class="header">
    <span class="title">How were regimes classified for this analysis?</span>
    <span class="subtitle">evaluated top → bottom, first match wins</span>
  </div>
  <div class="rule">
    <div class="priority">1</div>
    <div class="swatch" style="background:#ff0d0d;"></div>
    <div class="rule-body">
      <span class="regime-name" style="color:#cc0000;">Recession</span>
      <span class="condition">USREC == 1 &nbsp;or&nbsp; RECPROUSM156N &gt; 50</span>
      <span class="note">Official recession flag or recession probability &gt; 50%</span>
    </div>
  </div>
  <div class="rule">
    <div class="priority">2</div>
    <div class="swatch" style="background:#ff8e15;"></div>
    <div class="rule-body">
      <span class="regime-name" style="color:#c06000;">High Inflation</span>
      <span class="condition">CPI_YOY &gt; 5</span>
      <span class="note">Elevated inflation regardless of policy rate</span>
    </div>
  </div>
  <div class="rule">
    <div class="priority">3</div>
    <div class="swatch" style="background:#fab733;"></div>
    <div class="rule-body">
      <span class="regime-name" style="color:#8a6000;">Overheating</span>
      <span class="condition">CPI_YOY &gt; 2.5 &nbsp;and&nbsp; FEDFUNDS &lt; CPI_YOY</span>
      <span class="note">Inflation above target with negative real rates — policy behind the curve</span>
    </div>
  </div>
  <div class="rule">
    <div class="priority">4</div>
    <div class="swatch" style="background:#ff4e11;"></div>
    <div class="rule-body">
      <span class="regime-name" style="color:#c03000;">Deflationary Risk</span>
      <span class="condition">CPI_YOY &lt; 1 &nbsp;and&nbsp; FEDFUNDS &lt; 1</span>
      <span class="note">Very low inflation with near-zero policy rate — liquidity trap risk</span>
    </div>
  </div>
  <div class="rule">
    <div class="priority">5</div>
    <div class="swatch" style="background:#69b34c;"></div>
    <div class="rule-body">
      <span class="regime-name" style="color:#3a6e1e;">Goldilocks</span>
      <span class="condition">1 &lt;= CPI_YOY &lt;= 2.5</span>
      <span class="note">Inflation in target band — real rates implicitly positive</span>
    </div>
  </div>
  <div class="rule">
    <div class="priority">6</div>
    <div class="swatch" style="background:#acb334;"></div>
    <div class="rule-body">
      <span class="regime-name" style="color:#6a7000;">Reflation/Cooling</span>
      <span class="condition">else</span>
      <span class="note">Catch-all — CPI &gt; 2.5% with FFR ≥ CPI, or low CPI with FFR ≥ 1%</span>
    </div>
  </div>
</div>
</body></html>
"""

diffusion_card_html = """
<html><head>
  <link rel="stylesheet" href="/assets/style.css">
</head><body style="margin:0;padding:1rem;">
<div class="classifier-card">
  <div class="classifier-header">
    <span class="classifier-title">How is diffusion score calculated?</span>
    <span class="classifier-subtitle">mean(8 binary flags) × 100</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#ff8e15;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">CPI high</span>
      <span class="classifier-condition">CPI_YOY &gt; 3.5%</span>
      <span class="classifier-note">Inflation elevated — fraction of episode months where true</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#378ADD;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">CPI low</span>
      <span class="classifier-condition">CPI_YOY &lt; 1.0%</span>
      <span class="classifier-note">Deflation risk</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#ff4e11;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">Negative real rates</span>
      <span class="classifier-condition">REAL_FEDFUNDS &lt; 0</span>
      <span class="classifier-note">Policy behind the curve</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#7F77DD;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">Inverted yield curve</span>
      <span class="classifier-condition">T10Y2Y &lt; 0</span>
      <span class="classifier-note">Recession signal</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#A32D2D;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">High unemployment</span>
      <span class="classifier-condition">UNRATE &gt; 6%</span>
      <span class="classifier-note">Labor market stress</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#BA7517;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">High oil</span>
      <span class="classifier-condition">DCOILWTICO YoY &gt; 50%</span>
      <span class="classifier-note">Commodity shock</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#1D9E75;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">High M2 growth</span>
      <span class="classifier-condition">M2_YOY &gt; 8%</span>
      <span class="classifier-note">Monetary excess</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#D85A30;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">High breakeven inflation</span>
      <span class="classifier-condition">T10YIE &gt; 2.5%</span>
      <span class="classifier-note">Market expects inflation</span>
    </div>
    <span style="font-size:10px;color:#bbb;font-family:monospace;">1/8</span>
  </div>
</div>
</body></html>
"""

signal_card_html = """
<html><head>
  <link rel="stylesheet" href="/assets/style.css">
</head><body style="margin:0;padding:1rem;">
<div class="classifier-card">
  <div class="classifier-header">
    <span class="classifier-title">signal generation</span>
    <span class="classifier-subtitle">24-month lookback before each regime transition</span>
  </div>

  <div style="font-family:monospace;font-size:12px;background:#f5f5f5;border-radius:6px;padding:6px 10px;margin-bottom:10px;color:#444;">
    lead_days = transition_date − first_cross_date
  </div>

  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;">
    <span style="background:#eef3ff;color:#3a5ab8;font-family:monospace;font-size:11px;border-radius:4px;padding:2px 6px;">lookback = 24 months</span>
    <span style="background:#eef3ff;color:#3a5ab8;font-family:monospace;font-size:11px;border-radius:4px;padding:2px 6px;">z-score window = 252 days</span>
    <span style="background:#eef3ff;color:#3a5ab8;font-family:monospace;font-size:11px;border-radius:4px;padding:2px 6px;">z-scored: OIL · USD · DGS10</span>
  </div>

  <div style="font-size:10px;font-weight:500;color:#bbb;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">crosses below</div>

  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#7F77DD;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">Yield curve inverts</span>
      <span class="classifier-condition">T10Y2Y &lt; 0</span>
      <span class="classifier-note">10Y−2Y spread crosses below zero</span>
    </div>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#378ADD;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">USD weakens sharply</span>
      <span class="classifier-condition">DTWEXBGS_ZSCORE &lt; −1.5σ</span>
      <span class="classifier-note">Dollar 1.5σ below 252-day rolling mean</span>
    </div>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#1D9E75;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">Real yield goes negative</span>
      <span class="classifier-condition">DFII10 &lt; 0</span>
      <span class="classifier-note">10-year TIPS yield turns negative</span>
    </div>
  </div>

  <div style="font-size:10px;font-weight:500;color:#bbb;text-transform:uppercase;letter-spacing:0.05em;margin:10px 0 6px;">crosses above</div>

  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#D85A30;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">10Y breakeven elevated</span>
      <span class="classifier-condition">T10YIE &gt; 2.5%</span>
      <span class="classifier-note">Market inflation expectations exceed target</span>
    </div>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#ff8e15;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">5Y breakeven elevated</span>
      <span class="classifier-condition">T5YIE &gt; 2.0%</span>
      <span class="classifier-note">5-year inflation expectations exceed 2%</span>
    </div>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#BA7517;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">Oil shock</span>
      <span class="classifier-condition">OIL_YOY &gt; 50%</span>
      <span class="classifier-note">Crude oil up more than 50% year-over-year</span>
    </div>
  </div>
  <div class="classifier-rule">
    <div class="classifier-priority" style="color:#A32D2D;">●</div>
    <div class="classifier-rule-body">
      <span class="classifier-regime-name" style="color:#333;">Long rates spike</span>
      <span class="classifier-condition">DGS10 &gt; 4.0%</span>
      <span class="classifier-note">10-year yield crosses above 4%</span>
    </div>
  </div>

</div>
</body></html>
"""