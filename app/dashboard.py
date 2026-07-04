"""Static HTML trend dashboard: small multiples, one panel per metric.

Each metric has its own scale (a ratio, Hz, drift z-score, rate) so this is
small multiples rather than one dual-axis chart. Each panel is a single series
(no legend needed — the title names it), with a shaded band showing this
person's own baseline (mean +/- 1 std) and the flagged day marked with the
reserved "critical" status color, never a repurposed series hue. Palette and
mark specs follow the project's dataviz skill reference palette.
"""

PANEL_W = 560
PANEL_H = 160
PAD_L, PAD_R, PAD_T, PAD_B = 46, 16, 16, 28
PLOT_W = PANEL_W - PAD_L - PAD_R
PLOT_H = PANEL_H - PAD_T - PAD_B

SERIES_BLUE = "#2a78d6"
CRITICAL = "#d03b3b"
WARNING = "#fab219"


def _x(i, n):
    if n <= 1:
        return PAD_L + PLOT_W / 2
    return PAD_L + (i / (n - 1)) * PLOT_W


def _y(value, vmin, vmax):
    if vmax == vmin:
        return PAD_T + PLOT_H / 2
    t = (value - vmin) / (vmax - vmin)
    return PAD_T + (1 - t) * PLOT_H


def _fmt(v, decimals=2):
    if v is None:
        return "-"
    return f"{v:.{decimals}f}"


def render_panel(title, unit, dates, values, mean=None, std=None, threshold=None, flagged_date=None, decimals=2):
    n = len(values)
    present = [v for v in values if v is not None]
    vmin = min(present) if present else 0
    vmax = max(present) if present else 1
    if mean is not None and std is not None:
        vmin = min(vmin, mean - std)
        vmax = max(vmax, mean + std)
    if threshold is not None:
        vmax = max(vmax, threshold)
    span = vmax - vmin or 1
    vmin -= span * 0.1
    vmax += span * 0.1

    svg_parts = [f'<svg viewBox="0 0 {PANEL_W} {PANEL_H}" width="100%" height="{PANEL_H}" role="img" aria-label="{title} over time">']

    # gridlines (hairline, recessive)
    for frac in (0, 0.5, 1):
        gy = PAD_T + frac * PLOT_H
        gval = vmax - frac * (vmax - vmin)
        svg_parts.append(f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{PANEL_W - PAD_R}" y2="{gy:.1f}" class="grid"/>')
        svg_parts.append(f'<text x="{PAD_L - 6}" y="{gy + 3:.1f}" class="axis-label" text-anchor="end">{_fmt(gval, decimals)}</text>')

    # baseline band (this person's own mean +/- 1 std)
    if mean is not None and std is not None:
        y_top = _y(mean + std, vmin, vmax)
        y_bot = _y(mean - std, vmin, vmax)
        svg_parts.append(f'<rect x="{PAD_L}" y="{y_top:.1f}" width="{PLOT_W}" height="{(y_bot - y_top):.1f}" fill="{SERIES_BLUE}" opacity="0.10"/>')
        y_mean = _y(mean, vmin, vmax)
        svg_parts.append(f'<line x1="{PAD_L}" y1="{y_mean:.1f}" x2="{PANEL_W - PAD_R}" y2="{y_mean:.1f}" stroke="{SERIES_BLUE}" stroke-width="1" stroke-dasharray="3,3" opacity="0.5"/>')

    # threshold line (e.g. composite drift flag threshold)
    if threshold is not None:
        y_th = _y(threshold, vmin, vmax)
        svg_parts.append(f'<line x1="{PAD_L}" y1="{y_th:.1f}" x2="{PANEL_W - PAD_R}" y2="{y_th:.1f}" stroke="{WARNING}" stroke-width="1.5" stroke-dasharray="5,3"/>')
        svg_parts.append(f'<text x="{PANEL_W - PAD_R}" y="{y_th - 4:.1f}" class="axis-label" text-anchor="end" fill="{WARNING}">flag threshold</text>')

    # the line itself, 2px, only through known points
    points = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(points) >= 2:
        d = " ".join(f'{"M" if k == 0 else "L"}{_x(i, n):.1f},{_y(v, vmin, vmax):.1f}' for k, (i, v) in enumerate(points))
        svg_parts.append(f'<path d="{d}" fill="none" stroke="{SERIES_BLUE}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    for i, v in points:
        svg_parts.append(f'<circle cx="{_x(i, n):.1f}" cy="{_y(v, vmin, vmax):.1f}" r="3" fill="{SERIES_BLUE}"/>')

    # flagged day marker (reserved status color, direct label — this is the one point that needs a label)
    if flagged_date and flagged_date in dates:
        fi = dates.index(flagged_date)
        fv = values[fi]
        if fv is not None:
            fx, fy = _x(fi, n), _y(fv, vmin, vmax)
            svg_parts.append(
                f'<path d="M{fx:.1f},{fy - 7:.1f} L{fx + 7:.1f},{fy:.1f} L{fx:.1f},{fy + 7:.1f} L{fx - 7:.1f},{fy:.1f} Z" fill="{CRITICAL}"/>'
            )
            svg_parts.append(f'<text x="{fx:.1f}" y="{fy - 12:.1f}" class="flag-label" text-anchor="middle">flagged</text>')

    # x-axis: first/last date only, to keep it recessive
    if n:
        svg_parts.append(f'<text x="{PAD_L}" y="{PANEL_H - 6}" class="axis-label" text-anchor="start">{dates[0]}</text>')
        svg_parts.append(f'<text x="{PANEL_W - PAD_R}" y="{PANEL_H - 6}" class="axis-label" text-anchor="end">{dates[-1]}</text>')

    svg_parts.append("</svg>")
    svg = "\n".join(svg_parts)

    return f"""<div class="panel">
      <div class="panel-title">{title} <span class="unit">{unit}</span></div>
      {svg}
    </div>"""


def _table_row(date, features, flagged):
    cells = "".join(f"<td>{_fmt(features.get(k))}</td>" for k in ("pause_ratio", "speech_rate_wps", "pitch_std_hz", "filler_rate"))
    flag_cell = '<td><span class="flag-pill">flagged</span></td>' if flagged else "<td></td>"
    return f"<tr><td>{date}</td>{cells}{flag_cell}</tr>"


def render_dashboard(profile, records, analysis, flagged_date=None):
    dates = [r["date"] for r in records]
    pause = [r["features"].get("pause_ratio") for r in records]
    rate = [r["features"].get("speech_rate_wps") for r in records]
    pitch_std = [r["features"].get("pitch_std_hz") for r in records]

    pf = analysis["per_feature"]
    composite_series = []
    # per-day composite isn't recomputed retrospectively here (that needs a
    # rolling baseline per day) — we chart the single most recent composite
    # drift value against a flat baseline of 0 plus the flag threshold.
    from .analyze import COMPOSITE_DRIFT_THRESHOLD

    panels = [
        render_panel("Pause ratio", "(silence / total time)", dates, pause, mean=pf["pause_ratio"]["baseline_mean"], std=pf["pause_ratio"]["baseline_std"], flagged_date=flagged_date, decimals=3),
        render_panel("Speech rate", "(words / speaking second)", dates, rate, mean=pf["speech_rate_wps"]["baseline_mean"], std=pf["speech_rate_wps"]["baseline_std"], flagged_date=flagged_date, decimals=2),
        render_panel("Pitch variance", "(Hz, prosody)", dates, pitch_std, mean=pf["pitch_std_hz"]["baseline_mean"], std=pf["pitch_std_hz"]["baseline_std"], flagged_date=flagged_date, decimals=1),
    ]

    table_rows = "\n".join(_table_row(r["date"], r["features"], r["date"] == flagged_date) for r in records)

    status_color = CRITICAL if analysis["flagged"] else "#0ca30c"
    status_text = "Flagged this check-in" if analysis["flagged"] else "Within normal range"

    return f"""<!doctype html>
<html data-theme="auto">
<head>
<meta charset="utf-8">
<title>voice-checkin — {profile}</title>
<style>
  :root {{
    --surface-1: #fcfcfb; --page: #f9f9f7; --text-primary: #0b0b0b;
    --text-secondary: #52514e; --muted: #898781; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --surface-1: #1a1a19; --page: #0d0d0d; --text-primary: #ffffff; --text-secondary: #c3c2b7; --muted: #898781; --grid: #2c2c2a; --border: rgba(255,255,255,0.10); }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 32px; background: var(--page); color: var(--text-primary); font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  .subtitle {{ color: var(--text-secondary); font-size: 13px; margin-bottom: 20px; }}
  .status-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }}
  .status-dot {{ width: 12px; height: 12px; border-radius: 50%; background: {status_color}; }}
  .status-text {{ font-size: 15px; font-weight: 600; }}
  .message {{ color: var(--text-secondary); font-size: 13px; margin-top: 2px; }}
  .grid-panels {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 16px; }}
  .panel {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }}
  .panel-title {{ font-size: 13px; font-weight: 600; margin-bottom: 4px; }}
  .unit {{ font-weight: 400; color: var(--text-secondary); font-size: 12px; }}
  .grid {{ stroke: var(--grid); stroke-width: 1; }}
  .axis-label {{ fill: var(--muted); font-size: 10px; }}
  .flag-label {{ fill: {CRITICAL}; font-size: 10px; font-weight: 600; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 28px; font-size: 13px; background: var(--surface-1); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--grid); }}
  th {{ color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.03em; }}
  .flag-pill {{ background: rgba(208,59,59,0.15); color: {CRITICAL}; font-size: 11px; padding: 2px 8px; border-radius: 999px; }}
  h2 {{ font-size: 14px; margin: 28px 0 4px; }}
</style>
</head>
<body>
  <h1>Voice check-in — {profile}</h1>
  <div class="subtitle">Personal baseline drift, not a population norm or a diagnosis.</div>

  <div class="status-row">
    <div class="status-dot"></div>
    <div>
      <div class="status-text">{status_text}</div>
      <div class="message">{analysis["message"]}</div>
    </div>
  </div>

  <div class="grid-panels">
    {"".join(panels)}
  </div>

  <h2>Data table</h2>
  <table>
    <thead><tr><th>Date</th><th>Pause ratio</th><th>Speech rate</th><th>Pitch std (Hz)</th><th>Flag</th></tr></thead>
    <tbody>{table_rows}</tbody>
  </table>
</body>
</html>"""
