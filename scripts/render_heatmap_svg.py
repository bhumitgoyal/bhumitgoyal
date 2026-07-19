#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 contribution heatmap SVG.

Boxes reveal once on a diagonal slide-down (CSS keyframes, no looping) then
freeze. The SVG carries its own dark terminal panel so it looks identical on
GitHub's light and dark themes. Honours prefers-reduced-motion.

    python scripts/render_heatmap_svg.py           # animated
    STATIC=1 python scripts/render_heatmap_svg.py  # frozen frame (local preview)
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

# none -> brightest; level 5 is a neon top end reserved for peak days
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

# --- layout (user units; README scales the whole thing) ---
PAD_L = 42      # room for weekday labels
PAD_T = 34      # room for month labels
STEP = 15       # cell pitch
BOX = 11        # cell size
RX = 2.5
GRID_H = STEP * 7
FONT = "'SF Mono','JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

INK = "#e6edf3"
MUTE = "#7d8590"
PANEL = "#0d1117"
BORDER = "#21262d"
ACCENT = "#39d353"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_of(day: dict, best_count: int) -> int:
    if day["count"] <= 0:
        return 0
    if best_count > 0 and day["count"] == best_count:
        return 5
    return max(1, min(4, day["level"]))


def month_labels(days: list[dict]) -> list[tuple[int, str]]:
    """(week_index, label) for each column where the month first appears."""
    out: list[tuple[int, str]] = []
    seen_week = -1
    last_month = None
    for d in days:
        if d["week"] is None:
            continue
        m = int(d["date"][5:7])
        if m != last_month and d["week"] != seen_week:
            out.append((d["week"], MONTHS[m - 1]))
            last_month = m
            seen_week = d["week"]
    # drop a label if it would collide with the very next one (< 3 cols apart)
    pruned: list[tuple[int, str]] = []
    for wk, lab in out:
        if pruned and wk - pruned[-1][0] < 3:
            continue
        pruned.append((wk, lab))
    return pruned


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    data = json.loads(DATA.read_text())
    days = data["days"]
    stats = data["stats"]
    best_count = stats["best_day"]["count"]
    n_weeks = max((d["week"] for d in days if d["week"] is not None), default=52) + 1

    width = PAD_L + n_weeks * STEP + 14
    grid_bottom = PAD_T + GRID_H
    height = grid_bottom + 58

    max_delay = 0.0
    cells: list[str] = []
    for d in days:
        wk, dow = d["week"], d["dow"]
        if wk is None or dow is None:
            continue
        x = PAD_L + wk * STEP
        y = PAD_T + dow * STEP
        lvl = level_of(d, best_count)
        fill = PALETTE[lvl]
        delay = (wk + dow) * 0.016
        max_delay = max(max_delay, delay)
        style = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
        cls = "" if STATIC else ' class="cell"'
        title = f'{d["count"]} on {d["date"]}' if d["count"] else f'0 on {d["date"]}'
        cells.append(
            f'<rect{cls}{style} x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
            f'rx="{RX}" fill="{fill}"><title>{title}</title></rect>'
        )

    # weekday labels (Mon/Wed/Fri, GitHub style)
    wk_labels = []
    for dow, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD_T + dow * STEP + BOX - 1
        wk_labels.append(
            f'<text x="{PAD_L - 8}" y="{y}" text-anchor="end" '
            f'class="lab">{lab}</text>'
        )

    # month labels
    mo_labels = []
    for wk, lab in month_labels(days):
        x = PAD_L + wk * STEP
        mo_labels.append(f'<text x="{x}" y="{PAD_T - 10}" class="lab">{lab}</text>')

    # legend: Less [] [] [] [] [] More
    leg_x = width - 14 - (6 * STEP) - 74
    legend = [f'<text x="{leg_x - 8}" y="{grid_bottom + 20}" text-anchor="end" class="lab">Less</text>']
    for i, col in enumerate(PALETTE):
        lx = leg_x + i * (BOX + 5)
        legend.append(
            f'<rect x="{lx}" y="{grid_bottom + 11}" width="{BOX}" height="{BOX}" '
            f'rx="{RX}" fill="{col}"/>'
        )
    legend.append(
        f'<text x="{leg_x + 6 * (BOX + 5) + 3}" y="{grid_bottom + 20}" class="lab">More</text>'
    )

    total = stats["total"]
    footer = (
        f'<text x="{PAD_L}" y="{grid_bottom + 20}" class="foot">'
        f'<tspan class="foot-n">{total:,}</tspan> contributions in the last year'
        f'</text>'
        f'<text x="{PAD_L}" y="{grid_bottom + 40}" class="sub">'
        f'longest streak <tspan class="foot-n">{stats["longest_streak"]}</tspan> days'
        f'  ·  current <tspan class="foot-n">{stats["current_streak"]}</tspan>'
        f'  ·  best day <tspan class="foot-n">{best_count}</tspan>'
        f'  ·  {stats["active_days"]} active days</text>'
    )

    anim_css = "" if STATIC else f"""
    .cell {{
      opacity: 1;
      transform-box: fill-box;
      transform-origin: center;
      animation: pop .42s ease-out both;
    }}
    @keyframes pop {{
      0%   {{ opacity: 0; transform: translateY(-9px) scale(.55); }}
      70%  {{ opacity: 1; transform: translateY(2px) scale(1.05); }}
      100% {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .cell {{ animation: none; opacity: 1; transform: none; }}
    }}"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution graph">
  <style>
    text {{ font-family: {FONT}; }}
    .lab  {{ fill: {MUTE}; font-size: 10px; }}
    .foot {{ fill: {INK}; font-size: 12px; }}
    .foot-n {{ fill: {ACCENT}; font-weight: 600; }}
    .sub  {{ fill: {MUTE}; font-size: 11px; }}{anim_css}
  </style>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>
  <g>{''.join(mo_labels)}{''.join(wk_labels)}</g>
  <g>{''.join(cells)}</g>
  <g>{''.join(legend)}</g>
  {footer}
</svg>
"""


def main() -> int:
    OUT.write_text(build())
    mode = "static" if STATIC else "animated"
    print(f"Wrote {OUT.relative_to(ROOT)} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
