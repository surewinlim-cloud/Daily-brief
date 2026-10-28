# Daily Brief

A daily world-business and Asia-Pacific news briefing written by Claude, published as an EPUB with an OPDS catalog so e-readers (Xteink X4 Pro, KOReader, etc.) can download each morning's edition.

- **OPDS catalog (add this on your e-reader):** https://surewinlim-cloud.github.io/Daily-brief/opds.xml
- **Web page:** https://surewinlim-cloud.github.io/Daily-brief/

## How it works
`digests/YYYY-MM-DD.json` → `build.py` → `editions/daily-brief-YYYY-MM-DD.epub` + `opds.xml` + `index.html`.
The build uses the Python standard library only. It keeps the 14 most recent editions.

Content rules and the daily procedure are in [RUNBOOK.md](RUNBOOK.md).

## Setup (one time)
Settings → Pages → Source: "Deploy from a branch", Branch: `main`, folder `/ (root)`.
