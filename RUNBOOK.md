# Daily Brief — run instructions (followed by the 7:30am SGT scheduled task)

Each run produces up to TWO editions, both published to the same OPDS catalog, where they appear as folders:
- **Daily Brief** (news) → `editions/daily/daily-brief-YYYY-MM-DD.epub`
- **Tech Earnings** (post-earnings debrief) → `editions/tech-earnings/tech-earnings-YYYY-MM-DD.epub`

Source digests (`digests/daily/`, `digests/earnings/`) are temporary working files. They are git-ignored and never committed: only EPUBs and feeds go in the repo.

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

## 2. Tech Earnings — editorial spec
A general post-earnings debrief on technology companies. There is no watchlist and nothing personalised.
Window: tech results released in the ~24 hours to 7:30am SGT (US after-close and pre-market, plus Asia/Europe that day).

Scope: global tech, including semis and AI hardware, software and cloud, internet/ad tech/e-commerce/platforms, consumer hardware, and big Asian tech (TSMC, Samsung, SK Hynix, Sony, SoftBank, Tencent, Alibaba, Sea, Grab and similar). Leave out non-tech companies.

Sections, in this order (drop empty ones):
1. **Chips and AI hardware**
2. **Software and cloud**
3. **Internet and ad tech**
4. **Asia tech**

Pick by market significance: large caps and the biggest post-earnings moves. 4–10 items in season. **On days with no material tech results (off-season, most weekends), skip the edition.** Do not publish an empty or padded one.

Item format:
- `headline`: the result plus the market reaction, e.g. "Atlassian beats estimates but falls ~17% on its slower growth outlook".
- `summary`: 2–3 sentences in your own words: what drove it, what changed in guidance, why the stock moved.
- `figures`: 3–5 short bullets: revenue and EPS vs consensus, the forward guide vs consensus, one key KPI. Name the consensus source when it's ambiguous.
- `source` and `url` as for the Daily Brief. Company press releases and transcripts are fine sources. Use Reuters, CNBC or Bloomberg for consensus and the stock reaction.
- Top-level `summary`: one line shown in the e-reader catalog (the biggest winners and losers).
- Top-level `edition_title`: "Tech Earnings".

Rules: same sourcing, copyright and no-memory rules as the Daily Brief. Do not cite third-party fair-value/DCF numbers. Not investment advice.

## 3. TLDR Pre-Market — consolidated newsletter edition (separate 5pm SGT run)
Output: `editions/tldr/tldr-premarket-YYYY-MM-DD.epub` (Singapore date of the run), shown as the "TLDR Pre-Market" folder. Digest: `digests/tldr/YYYY-MM-DD.json` (git-ignored).

Input: every TLDR newsletter in Sherwin's Gmail (sender `dan@tldrnewsletter.com`; TLDR, TLDR AI, IT, Hardware, Fintech, Data, Design, Marketing, plus any others he subscribes to) received since the previous run (~5pm SGT the day before). Search `from:tldrnewsletter.com newer_than:2d`, keep messages whose date falls in the window, and read each with get_thread (PLAIN_TEXT). Skip signup/confirmation emails. TLDR issues usually land 7–11:30pm SGT, so the 5pm edition normally carries the previous evening's issues. If there are none in the window (weekends, holidays), skip the edition.

Editorial rules:
- Consolidate, don't concatenate: merge the same story across newsletters into one item and list every newsletter it came from in `source` (e.g. "TLDR AI, TLDR IT · TechCrunch").
- Drop all sponsored items (marked "(Sponsor)"), TLDR self-promotion, referral/job blurbs, webinars and ads posing as tools.
- Sections, in this order (drop empty ones): Market movers (listed companies, funding/valuations, deals, earnings, capex — what matters before the US open); AI; Big tech, hardware and science; Fintech and commerce; Dev, data and IT; Marketing and design.
- Each item: one-line headline, 1–2 sentence summary in your own words (do not copy TLDR's text), `source` as above, and `url` = the original article link from the newsletter's link list with `utm_*` parameters removed (keep `links.tldrnewsletter.com` short links as they are).
- Top-level `summary`: one line of the 3–4 biggest market-relevant items. Keep the Anthropic disclosure in `note` when Anthropic appears.

Build: `python3 -I build.py --series tldr YYYY-MM-DD`, validate the EPUB and feeds with lxml, commit and push ("TLDR Pre-Market YYYY-MM-DD", `git add -A editions opds opds.xml index.html`), then SendUserFile the EPUB.

## Research tips
- Use WebSearch with mode "extended", WITHOUT allowed_domains (the domain filter is rejected). Put the date and outlet in the query, e.g. "Japan news October 28 2026 Reuters".
- Reuters/CNA/BBC pages often can't be fetched directly; syndicated Reuters copies (Yahoo Finance, Investing.com, MarketScreener, The Star) are fine — attribute to Reuters.
- Earnings: start with "stocks making the biggest moves after hours [date]" (CNBC) and "tech earnings [date] after the bell", then search each name for "[company] Q[n] 2026 results guidance".
- When two sources disagree on a number, prefer the company release, then Reuters/CNBC; drop the figure if still unclear.

## Build and publish
1. Write `digests/daily/YYYY-MM-DD.json` using the schema in build.py's docstring. To avoid repeating yesterday's stories, read yesterday's EPUB (unzip `editions/daily/…` and skim the .xhtml).
2. If there is a Tech Earnings edition, write `digests/earnings/YYYY-MM-DD.json` (same schema, plus optional `figures` per item).
3. `python3 -I build.py YYYY-MM-DD` builds the daily EPUB, and `python3 -I build.py --series earnings YYYY-MM-DD` builds the Tech Earnings EPUB. Each one deletes editions dated more than 3 calendar days before today, SGT (`keep_days` in config.json; e.g. on the 10th it keeps the 7th–10th), and regenerates `opds.xml` (folder root), `opds/daily.xml`, `opds/earnings.xml` and `index.html`.
4. Check: unzip each new EPUB and parse every .xhtml/.opf/.ncx with lxml. Also parse `opds.xml` and `opds/*.xml`. Fix any errors.
5. Commit and push to main (including the deletions of pruned EPUBs, e.g. `git add -A editions`) of github.com/surewinlim-cloud/Daily-brief (message: "Daily Brief YYYY-MM-DD", adding "+ Tech Earnings" when published). `digests/` is git-ignored, so it is never committed.
6. Send the EPUBs to the user with SendUserFile as a backup. Include one line naming the 2–3 biggest stories and, if there is a Tech Earnings edition, one line on its biggest mover.
