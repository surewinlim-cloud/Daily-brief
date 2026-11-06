# Daily Brief — run instructions (followed by the 7:30am SGT scheduled task)

Each run produces TWO editions, both published to the same OPDS catalog, where they appear as folders:
- **Daily Brief** (news) — `digests/daily/YYYY-MM-DD.json` → `editions/daily/daily-brief-YYYY-MM-DD.epub`
- **Earnings Brief** — `digests/earnings/YYYY-MM-DD.json` → `editions/earnings/earnings-brief-YYYY-MM-DD.epub`

Do the Daily Brief first; it must never be delayed by the earnings work.

## 1. Daily Brief — editorial spec
Ten sections, five stories each (50 total), in this order:
1. World Business: Tech
2. World Business: Finance & Markets
3. Singapore (current affairs)
4. Southeast Asia
5. Japan
6. South Korea
7. Australia
8. United States
9. China
10. India

Rules:
- Cover roughly the last 24 hours (since ~7am SGT the previous day). Prefer stories not already in yesterday's digest.
- Sources: reputable outlets only — Reuters, BBC, CNA, AP, The Straits Times, CNBC, Bloomberg, FT, Nikkei, Japan Times, Korea Herald/Yonhap, ABC (Australia), The Hindu, SCMP, Al Jazeera. Avoid blogs, aggregators and AI content farms.
- No sports, ever.
- Each story: headline (one line), summary of 1–3 sentences in your own words (no copying; quotes under 15 words, at most one per source), source name(s), and a URL you actually retrieved.
- Facts and figures must come from what you retrieved, never memory. If a section is thin, use fewer stories rather than padding.
- Keep the disclosure line in "note" if Anthropic appears in the news.

## 2. Earnings Brief — editorial spec
Window: results released in the ~24 hours to 7:30am SGT (US after-close and pre-market, plus Asia/Europe that day).

Sections, in this order (drop empty ones):
1. **Your holdings** — the watchlist in `config.json` → `earnings_watchlist`. For each holding that reported: a full item (see format below). Always end with one "Coming up" item listing the watchlist's next report dates (confirmed vs estimated) and any guidance they gave for that quarter. If none reported, say so in the first item's headline and preview the next one.
2. **US tech and AI**
3. **US consumer** (or other US sectors that had big movers)
4. **Asia** — Singapore banks/REITs/blue chips, Japan, Korea, China/HK, Australia when they report.
5. Optionally **Europe** in heavy weeks.

Pick by market significance: large caps and the biggest post-earnings moves. 8–12 items in season; on quiet days (off-season, weekends) 2–5 items is fine. **If nothing material reported and no holding reports within 7 days, skip the Earnings Brief that day** (do not publish an empty edition).

Item format:
- `headline`: the result plus the market reaction, e.g. "Atlassian beats estimates but falls ~17% on its slower growth outlook".
- `summary`: 2–3 sentences in your own words — what drove it, what changed in guidance, why the stock moved.
- `figures`: 3–5 short bullets — revenue and EPS vs consensus, the forward guide vs consensus, one key KPI. Name the consensus source when it's ambiguous.
- `source` and `url` as for the Daily Brief. Company press releases and transcripts are fine sources; Reuters/CNBC/Bloomberg for consensus and reaction.
- Optional top-level `summary` string: one line shown in the e-reader catalog (biggest movers plus the next holding to report).

Rules: same sourcing, copyright and no-memory rules as the Daily Brief. Do not cite third-party fair-value/DCF numbers. If a valuation comment is needed, base it on the company's own reported figures and guidance. Not investment advice.

## Research tips
- Use WebSearch with mode "extended", WITHOUT allowed_domains (the domain filter is rejected). Put the date and outlet in the query, e.g. "Japan news October 28 2026 Reuters".
- Reuters/CNA/BBC pages often can't be fetched directly; syndicated Reuters copies (Yahoo Finance, Investing.com, MarketScreener, The Star) are fine — attribute to Reuters.
- Earnings: start with "stocks making the biggest moves after hours [date]" (CNBC) and "earnings [date] after the bell", then search each name for "[company] Q[n] 2026 results guidance". Check each watchlist ticker's next date ("[ticker] earnings date").
- When two sources disagree on a number, prefer the company release, then Reuters/CNBC; drop the figure if still unclear.

## Build and publish
1. Write `digests/daily/YYYY-MM-DD.json` (schema in build.py; copy the shape of the previous day's file).
2. Write `digests/earnings/YYYY-MM-DD.json` (same schema plus optional `figures` per item; copy the previous earnings file).
3. `python3 -I build.py YYYY-MM-DD` builds the daily EPUB; `python3 -I build.py --series earnings YYYY-MM-DD` builds the earnings EPUB. Each prunes to the last 14 and regenerates `opds.xml` (folder root), `opds/daily.xml`, `opds/earnings.xml` and `index.html`.
4. Check: unzip each new EPUB and parse every .xhtml/.opf/.ncx with lxml; also parse `opds.xml` and `opds/*.xml`. Fix any errors.
5. Commit and push to main of github.com/surewinlim-cloud/Daily-brief (message: "Daily Brief YYYY-MM-DD" — add "+ Earnings" when published).
6. Send both EPUBs to the user with SendUserFile as a backup, with one line naming the 2–3 biggest stories and one line on the biggest earnings mover (or the next holding to report).
