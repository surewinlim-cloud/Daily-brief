# Daily Brief

A daily world-business and Asia-Pacific news briefing plus an earnings brief, written by Claude and published as EPUBs with an OPDS catalog so e-readers (Xteink X4 with CrossPoint, KOReader, etc.) can download each morning's editions.

- **OPDS catalog (add this on your e-reader):** https://surewinlim-cloud.github.io/Daily-brief/opds.xml
  It opens as folders: **Daily Brief** and **Earnings Brief**.
- **Web page:** https://surewinlim-cloud.github.io/Daily-brief/

## How it works
| Series | Digest | EPUB | Feed |
| --- | --- | --- | --- |
| Daily Brief | `digests/daily/YYYY-MM-DD.json` | `editions/daily/daily-brief-YYYY-MM-DD.epub` | `opds/daily.xml` |
| Earnings Brief | `digests/earnings/YYYY-MM-DD.json` | `editions/earnings/earnings-brief-YYYY-MM-DD.epub` | `opds/earnings.xml` |

`opds.xml` is the navigation root that links to each series feed. Series are defined in `config.json` (`series`), and the earnings watchlist is in `earnings_watchlist`. To add a new folder, add a series entry and a digests directory.
The build uses the Python standard library only. It keeps the 14 most recent editions per series.

Content rules and the daily procedure are in [RUNBOOK.md](RUNBOOK.md).

## Setup (one time)
Settings → Pages → Source: "Deploy from a branch", Branch: `main`, folder `/ (root)`.
