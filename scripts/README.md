# How this profile is built

Everything on the profile is **self-contained animated SVG** — no third-party
stats services, no GitHub token, no JavaScript. GitHub strips `<script>` and
sanitizes inline CSS from READMEs, but it *does* render SVGs embedded via
`<img>` and plays their SMIL / CSS-keyframe animations. So all motion lives
inside the SVG files; the README just places them.

## The pieces

| File | Made by | Refresh |
|------|---------|---------|
| `../ascii.svg` | `prep_photo.py` → `make_ascii_svg.py` | manual (when the photo changes) |
| `../info-card.svg` | `make_info_card.py` | manual (when details change) |
| `../contrib-heatmap.svg` | `fetch_contributions.py` → `render_heatmap_svg.py` | **daily**, via GitHub Actions |
| `../data/contributions.json` | `fetch_contributions.py` | daily |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt          # portrait libs are heavy; see note
```

The daily workflow only needs `requests` + `beautifulsoup4`. The portrait
pipeline (`pillow`, `numpy`, `opencv`, `rembg`) runs **locally only**, when you
change your photo.

## Regenerate the portrait (new photo)

```bash
python scripts/prep_photo.py path/to/photo.jpg   # rembg cutout + CLAHE + white composite + crop
python scripts/make_ascii_svg.py                 # -> ascii.svg
```

`prep_photo.py` writes a local `source-prepped.png` (git-ignored — the public
artifact is `ascii.svg`). iPhone `.heic` photos work if `pillow-heif` is
installed.

## Regenerate the info card

Edit `ROWS` / `TITLE` in `make_info_card.py`, then:

```bash
python scripts/make_info_card.py                 # -> info-card.svg
```

## Regenerate the heatmap by hand

```bash
python scripts/fetch_contributions.py            # scrape -> data/contributions.json
python scripts/render_heatmap_svg.py             # -> contrib-heatmap.svg
```

The GitHub Action `.github/workflows/update-profile-art.yml` does exactly this
on a daily cron and commits the result with `[skip ci]`.

## Local preview

Any generator honours `STATIC=1` to emit a frozen (non-animated) frame — handy
for eyeballing in Quick Look or a static screenshot:

```bash
STATIC=1 python scripts/render_heatmap_svg.py
```
