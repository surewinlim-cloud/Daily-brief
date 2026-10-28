# Daily Brief — run instructions (followed by the 7:30am SGT scheduled task)

## Editorial spec
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

## Research tips
- Use WebSearch with mode "extended", WITHOUT allowed_domains (the domain filter is rejected). Put the date and outlet in the query, e.g. "Japan news October 28 2026 Reuters".
- Reuters/CNA/BBC pages often can't be fetched directly; syndicated Reuters copies (Yahoo Finance, Investing.com, MarketScreener, The Star) are fine — attribute to Reuters.

## Build and publish
1. Write `digests/YYYY-MM-DD.json` (schema in build.py; copy the shape of the previous day's file).
2. `python3 -I build.py YYYY-MM-DD` → builds the EPUB, prunes to the last 14, and regenerates opds.xml and index.html.
3. Check: unzip the EPUB and parse every .xhtml/.opf/.ncx with lxml. Fix any errors.
4. Commit and push to main of github.com/surewinlim-cloud/Daily-brief (message: "Daily Brief YYYY-MM-DD").
5. Send the EPUB to the user with SendUserFile as a backup, and add a one-line note naming the 2–3 biggest stories.
