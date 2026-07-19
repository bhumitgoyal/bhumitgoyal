#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG.

A title bar, an underline, then colored key/value rows and the classic
neofetch color-block palette. Each line fades and slides in on a short
stagger so the panel looks like it prints next to the portrait.

    python scripts/make_info_card.py           # animated
    STATIC=1 python scripts/make_info_card.py   # frozen frame (local preview)

Edit ROWS / TITLE below when your details change, then re-run.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

TITLE = "bhumit@github"

# (key, value, key-color)
GREEN, CYAN, YELLOW, RED, PURPLE, BLUE, ORANGE = (
    "#39d353", "#56d4dd", "#e3b341", "#f85149", "#bc8cff", "#58a6ff", "#ff8c42",
)
ROWS = [
    ("Role",     "AI Engineer · Full-Stack Developer", GREEN),
    ("Now",      "Building practical AI systems & agents", CYAN),
    ("Prev",     "AI workflows @ Trademarkia (intern)", PURPLE),
    ("Edu",      "B.Tech CSE — VIT Vellore, '23–'27", BLUE),
    ("Stack",    "Python · TypeScript · Java · Go", YELLOW),
    ("Backend",  "FastAPI · Spring Boot · Firebase · Mongo", ORANGE),
    ("AI",       "LangChain · RAG · OpenAI · agentic loops", GREEN),
    ("Shipping", "github-analyze · convo-legal · academia-ai", CYAN),
    ("Focus",    "agents that know your work, not demos", RED),
    ("Status",   "online — open to high-impact eng roles", GREEN),
    ("Links",    "in/bhumitgoyal · leetcode/bhumitgoyal", BLUE),
]

FONT = "'SF Mono','JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
INK = "#e6edf3"
MUTE = "#7d8590"
PANEL = "#0d1117"
BORDER = "#21262d"
ACCENT = "#39d353"

PAD_X = 26
TOP = 30
LINE = 30          # row pitch
KEY_W = 96         # value column offset
CARD_W = 560
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]  # traffic-light window dots


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    y0 = TOP + 66            # first row baseline (below the "$ neofetch" prompt)
    rows_svg: list[str] = []
    for i, (key, val, color) in enumerate(ROWS):
        y = y0 + i * LINE
        delay = 0.18 + i * 0.075
        anim = "" if STATIC else f' class="row" style="animation-delay:{delay:.3f}s"'
        rows_svg.append(
            f'<g{anim}>'
            f'<text x="{PAD_X}" y="{y}" class="key" fill="{color}">{esc(key)}</text>'
            f'<text x="{PAD_X + KEY_W}" y="{y}" class="val">{esc(val)}</text>'
            f'</g>'
        )

    palette_y = y0 + len(ROWS) * LINE + 6
    blocks = ["#161b22", GREEN, CYAN, YELLOW, RED, PURPLE, BLUE, ORANGE]
    pal: list[str] = []
    bw = 20
    for i, c in enumerate(blocks):
        pal.append(
            f'<rect x="{PAD_X + i * (bw + 6)}" y="{palette_y}" width="{bw}" '
            f'height="12" rx="2" fill="{c}"/>'
        )
    delay_pal = 0.18 + len(ROWS) * 0.075
    pal_anim = "" if STATIC else f' class="row" style="animation-delay:{delay_pal:.3f}s"'
    palette_svg = f'<g{pal_anim}>{"".join(pal)}</g>'

    height = palette_y + 34

    # window chrome: three dots + centered title
    dots_svg = "".join(
        f'<circle cx="{PAD_X + 6 + i * 18}" cy="20" r="6" fill="{c}"/>'
        for i, c in enumerate(DOTS)
    )

    title_delay = 0.05
    title_anim = "" if STATIC else f' class="row" style="animation-delay:{title_delay}s"'

    anim_css = "" if STATIC else """
    .row {
      opacity: 1;
      animation: slidein .5s cubic-bezier(.2,.7,.2,1) both;
    }
    @keyframes slidein {
      from { opacity: 0; transform: translateX(-10px); }
      to   { opacity: 1; transform: translateX(0); }
    }
    @media (prefers-reduced-motion: reduce) {
      .row { animation: none; opacity: 1; transform: none; }
    }"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {height}" role="img" aria-label="neofetch-style info card">
  <style>
    text {{ font-family: {FONT}; }}
    .key {{ font-size: 14px; font-weight: 600; }}
    .val {{ font-size: 14px; fill: {INK}; }}
    .title {{ font-size: 14px; fill: {MUTE}; }}
    .prompt {{ font-size: 13px; fill: {ACCENT}; }}{anim_css}
  </style>
  <rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{height - 1}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>
  <line x1="0" y1="40" x2="{CARD_W}" y2="40" stroke="{BORDER}"/>
  {dots_svg}
  <text x="{CARD_W / 2}" y="25" text-anchor="middle" class="title">{esc(TITLE)} — neofetch</text>
  <g{title_anim}>
    <text x="{PAD_X}" y="{y0 - LINE}" class="prompt">$ neofetch</text>
  </g>
  {''.join(rows_svg)}
  {palette_svg}
</svg>
"""


def main() -> int:
    OUT.write_text(build())
    print(f"Wrote {OUT.relative_to(ROOT)} ({'static' if STATIC else 'animated'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
