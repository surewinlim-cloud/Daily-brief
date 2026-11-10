# Daily Brief

A daily world-business and Asia-Pacific news briefing plus a post-earnings tech debrief, written by Claude and published as EPUBs with an OPDS catalog so e-readers (Xteink X4 with CrossPoint, KOReader, etc.) can download each morning's editions.

- **OPDS catalog (add this on your e-reader):** https://surewinlim-cloud.github.io/Daily-brief/opds.xml
  It opens as folders: **Daily Brief**, **Tech Earnings** and **TLDR Pre-Market**.
- **Web page:** https://surewinlim-cloud.github.io/Daily-brief/

## How it works
| Series | EPUBs | Feed |
| --- | --- | --- |
| Daily Brief | `editions/daily/daily-brief-YYYY-MM-DD.epub` | `opds/daily.xml` |
| Tech Earnings | `editions/tech-earnings/tech-earnings-YYYY-MM-DD.epub` | `opds/earnings.xml` |
| TLDR Pre-Market | `editions/tldr/tldr-premarket-YYYY-MM-DD.epub` | `opds/tldr.xml` |

`opds.xml` is the navigation root that links to each series feed. Series are defined in `config.json` (`series`).
Each edition is built from a JSON digest (`digests/<series>/YYYY-MM-DD.json`). Digests are temporary and git-ignored. The catalog summary is stored inside each EPUB, so the feeds can be regenerated without them.
The build uses the Python standard library only. It deletes editions dated more than 3 calendar days before today (Singapore time), set by `keep_days` in config.json.

Content rules and the daily procedure are in [RUNBOOK.md](RUNBOOK.md).

## Setup (one time)
Settings → Pages → Source: "Deploy from a branch", Branch: `main`, folder `/ (root)`.
