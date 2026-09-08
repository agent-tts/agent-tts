# Project page — "When Agents Slow Down"

Static site (no build step). Layout follows the TailRL project page: sticky section nav,
hero with authors/affiliations/buttons, teaser figure, concept sections with figures and
takeaway boxes, results, BibTeX, footer.

- `index.html` — the page (loads `static/css/style.css` and `static/images/*`).
- `static/images/` — figures rendered from the paper PDFs (`fig/*.pdf` in the Overleaf repo)
  at 220–320 dpi, plus the institution logo strip.
- `scripts/make_teaser_gif.py` — regenerates the animated teaser from the two CSV files
  in `scripts/data/`.
- `preview/index_preview.html` — self-contained copy with images and CSS inlined, for
  previewing without a server. Regenerate after edits (see below).

## Regenerate the animated teaser

```bash
python3 scripts/make_teaser_gif.py
```

## Placeholders to fill before launch

Search `index.html` for `TODO(`:
- `TODO(arXiv)`: arXiv abs URL on the Paper button (remove the `soon` class).
- `TODO(code)`: GitHub repository URL on the Code button.
- `TODO(data)`: raw-data release URL on the Data button.
- BibTeX block: arXiv identifier once assigned.

## Deploy on GitHub Pages

Push this folder as the root of a repository (e.g. `EloScaling-website`) and enable
Pages on the `main` branch. Fonts come from Google Fonts; everything else is local.

## Regenerate the preview

```bash
python3 - <<'PY'
import base64, mimetypes, re
W = "."
html = open(f"{W}/index.html").read(); css = open(f"{W}/static/css/style.css").read()
html = html.replace('<link rel="stylesheet" href="./static/css/style.css">', f"<style>{css}</style>")
html = re.sub(r'src="(\./static/images/[^"]+)"', lambda m: 'src="data:' + (mimetypes.guess_type(m.group(1))[0] or 'application/octet-stream') + ';base64,' + base64.b64encode(open(f"{W}/{m.group(1)[2:]}", "rb").read()).decode() + '"', html)
open(f"{W}/preview/index_preview.html", "w").write(html)
PY
```
