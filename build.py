#!/usr/bin/env python3
"""Daily Brief builder.

Builds one EPUB per digest for each series in config.json.
Digests are temporary working files (git-ignored); after a build only the
EPUBs and feeds are kept. The catalog summary is stored inside each EPUB.
  daily     digests/daily/YYYY-MM-DD.json    -> editions/daily/daily-brief-YYYY-MM-DD.epub
  earnings  digests/earnings/YYYY-MM-DD.json -> editions/earnings/earnings-brief-YYYY-MM-DD.epub
then regenerates the OPDS catalog and index.html:
  opds.xml            navigation root: one folder per series
  opds/<series>.xml   acquisition feed for that series (newest first)
Standard library only, so it runs anywhere.

Usage:
    python3 build.py                              # build every digest that has no EPUB yet (all series)
    python3 build.py 2026-10-28                   # (re)build one daily date
    python3 build.py --series earnings 2026-11-06 # (re)build one earnings date
    python3 build.py --all                        # rebuild everything

Digest JSON schema:
{
  "date": "2026-10-28",
  "edition_title": "Daily Brief",            # optional
  "sections": [
    {"title": "World Business: Tech",
     "items": [
        {"headline": "...", "summary": "...", "source": "Reuters",
         "url": "https://...",
         "figures": ["Revenue $2.31bn (+96% y/y) vs $2.2bn est.", "..."]}  # optional bullet list
     ]}
  ]
}
"""
import datetime as dt
import html
import json
import os
import re
import sys
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text()) if (ROOT / "config.json").exists() else {}
BASE_URL = CONFIG.get("base_url", "").rstrip("/")
KEEP = int(CONFIG.get("keep_editions", 14))
KEEP_DAYS = CONFIG.get("keep_days")  # if set, delete editions dated more than this many days before today (SGT)
TITLE = CONFIG.get("title", "Daily Brief")
AUTHOR = CONFIG.get("author", "Claude")
LOCAL_TZ = dt.timezone(dt.timedelta(hours=8))  # Singapore

DEFAULT_SERIES = [
    {"key": "daily", "title": TITLE, "digests": "digests/daily", "editions": "editions/daily", "prefix": "daily-brief",
     "blurb": "Daily news briefing", "unit": "stories"},
    {"key": "earnings", "title": "Earnings Brief", "digests": "digests/earnings", "editions": "editions/earnings",
     "prefix": "earnings-brief", "blurb": "Earnings results and what changed", "unit": "items"},
]


class Series:
    def __init__(self, d):
        self.key = d["key"]
        self.title = d["title"]
        self.digests = ROOT / d["digests"]
        self.editions = ROOT / d["editions"]
        self.editions_rel = d["editions"].strip("/")
        self.prefix = d["prefix"]
        self.blurb = d.get("blurb", "")
        self.unit = d.get("unit", "stories")
        # daily keeps its original ids so already-downloaded books are not duplicated
        self.uid_ns = "daily-brief" if self.key == "daily" else self.key

    def epubs(self, reverse=False):
        return sorted(self.editions.glob(f"{self.prefix}-*.epub"), reverse=reverse)

    def epub_for(self, date_str):
        return self.editions / f"{self.prefix}-{date_str}.epub"


SERIES = [Series(d) for d in CONFIG.get("series", DEFAULT_SERIES)]
SERIES_BY_KEY = {s.key: s for s in SERIES}

CSS = """
body { font-family: serif; line-height: 1.4; margin: 0 0.3em; }
h1 { font-size: 1.35em; margin: 0.4em 0 0.6em; }
h2 { font-size: 1.05em; margin: 1.1em 0 0.25em; line-height: 1.25; }
p { margin: 0 0 0.4em; text-align: left; }
p.src { font-size: 0.8em; font-style: italic; margin-bottom: 0.9em; }
p.meta { font-size: 0.85em; }
ol.toc { padding-left: 1.2em; }
ol.toc li { margin-bottom: 0.4em; }
ul { padding-left: 1.2em; margin: 0.1em 0 0.4em; }
ul li { margin-bottom: 0.15em; }
hr { border: 0; border-top: 1px solid #000; margin: 0.8em 0; }
"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def xhtml(title, body):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><title>{esc(title)}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
{body}
</body>
</html>
"""


def pretty_date(d):
    return d.strftime("%A, %d %B %Y").replace(" 0", " ")


def catalog_summary(series, data):
    secs = [s for s in data["sections"] if s.get("items")]
    return data.get("summary") or (
        f"{sum(len(s['items']) for s in secs)} {series.unit}: " + ", ".join(s["title"] for s in secs))


def epub_summary(ep: Path) -> str:
    """Read the catalog summary stored in the EPUB's OPF (dc:description)."""
    import re
    try:
        with zipfile.ZipFile(ep) as z:
            opf = z.read("OEBPS/content.opf").decode("utf-8")
        m = re.search(r"<dc:description>(.*?)</dc:description>", opf, re.S)
        return html.unescape(m.group(1)) if m else ""
    except Exception:
        return ""


def build_epub(series: Series, digest_path: Path) -> Path:
    data = json.loads(digest_path.read_text(encoding="utf-8"))
    date = dt.date.fromisoformat(data["date"])
    sections = [s for s in data["sections"] if s.get("items")]
    stitle = data.get("edition_title", series.title)
    book_title = f"{stitle} — {date.strftime('%d %b %Y')}"
    book_id = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, series.uid_ns + '/' + data['date'])}"
    modified = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    files = {}  # name -> content
    # Cover / contents page
    toc_items = "\n".join(
        f'<li><a href="s{i:02d}.xhtml">{esc(s["title"])}</a> ({len(s["items"])})</li>'
        for i, s in enumerate(sections, 1)
    )
    total = sum(len(s["items"]) for s in sections)
    files["cover.xhtml"] = xhtml(book_title, f"""
<h1>{esc(stitle)}</h1>
<p class="meta">{esc(pretty_date(date))}<br/>{total} {series.unit} · {len(sections)} sections</p>
<hr/>
<ol class="toc">
{toc_items}
</ol>
<hr/>
<p class="src">{esc(data.get('note', 'Summaries written by Claude from reputable outlets. Source named under each story.'))}</p>
""")

    for i, s in enumerate(sections, 1):
        parts = [f'<h1>{esc(s["title"])}</h1>']
        for item in s["items"]:
            parts.append(f'<h2>{esc(item["headline"])}</h2>')
            for para in str(item.get("summary", "")).split("\n"):
                if para.strip():
                    parts.append(f"<p>{esc(para.strip())}</p>")
            figs = [f for f in item.get("figures", []) if str(f).strip()]
            if figs:
                parts.append("<ul>" + "".join(f"<li>{esc(f)}</li>" for f in figs) + "</ul>")
            src = esc(item.get("source", ""))
            if item.get("url"):
                src = f'{src} · {esc(item["url"])}' if src else esc(item["url"])
            if src:
                parts.append(f'<p class="src">{src}</p>')
        files[f"s{i:02d}.xhtml"] = xhtml(s["title"], "\n".join(parts))

    files["style.css"] = CSS.strip() + "\n"

    # Navigation (EPUB3) + NCX (EPUB2 readers)
    nav_li = "\n".join(
        f'<li><a href="s{i:02d}.xhtml">{esc(s["title"])}</a></li>' for i, s in enumerate(sections, 1)
    )
    files["nav.xhtml"] = xhtml("Contents", f"""
<nav epub:type="toc" id="toc"><h1>Contents</h1>
<ol>
<li><a href="cover.xhtml">Front page</a></li>
{nav_li}
</ol></nav>
""")
    nav_points = [("cover.xhtml", "Front page")] + [
        (f"s{i:02d}.xhtml", s["title"]) for i, s in enumerate(sections, 1)
    ]
    ncx_points = "\n".join(
        f'<navPoint id="np{n}" playOrder="{n}"><navLabel><text>{esc(t)}</text></navLabel>'
        f'<content src="{h}"/></navPoint>'
        for n, (h, t) in enumerate(nav_points, 1)
    )
    files["toc.ncx"] = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="{book_id}"/><meta name="dtb:depth" content="1"/>
<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>
<docTitle><text>{esc(book_title)}</text></docTitle>
<navMap>
{ncx_points}
</navMap>
</ncx>
"""

    content_docs = ["cover.xhtml"] + [f"s{i:02d}.xhtml" for i in range(1, len(sections) + 1)]
    manifest = "\n".join(
        [f'<item id="{n.replace(".", "_")}" href="{n}" media-type="application/xhtml+xml"/>' for n in content_docs]
        + [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '<item id="css" href="style.css" media-type="text/css"/>',
        ]
    )
    spine = "\n".join(f'<itemref idref="{n.replace(".", "_")}"/>' for n in content_docs)
    files["content.opf"] = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{book_id}</dc:identifier>
<dc:title>{esc(book_title)}</dc:title>
<dc:creator>{esc(AUTHOR)}</dc:creator>
<dc:language>en</dc:language>
<dc:date>{date.isoformat()}</dc:date>
<dc:publisher>{esc(stitle)}</dc:publisher>
<dc:description>{esc(catalog_summary(series, data))}</dc:description>
<meta property="dcterms:modified">{modified}</meta>
</metadata>
<manifest>
{manifest}
</manifest>
<spine toc="ncx">
{spine}
</spine>
</package>
"""

    series.editions.mkdir(parents=True, exist_ok=True)
    out = series.epub_for(date.isoformat())
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            "</rootfiles></container>\n",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        for name, content in files.items():
            z.writestr(f"OEBPS/{name}", content, compress_type=zipfile.ZIP_DEFLATED)
    print(f"built {out.relative_to(ROOT)} ({total} {series.unit})")
    return out


def url(path):
    return f"{BASE_URL}/{path}" if BASE_URL else path


def prune(series: Series):
    eps = series.epubs()
    if KEEP_DAYS is not None:
        cutoff = dt.datetime.now(LOCAL_TZ).date() - dt.timedelta(days=int(KEEP_DAYS))
        doomed = []
        for ep in eps:
            m = re.search(r"\d{4}-\d{2}-\d{2}", ep.name)
            if m and dt.date.fromisoformat(m.group(0)) < cutoff:
                doomed.append(ep)
    else:
        doomed = eps[:-KEEP] if len(eps) > KEEP else []
    for old in doomed:
        old.unlink()
        print(f"pruned {old.relative_to(ROOT)}")


NAV = "application/atom+xml;profile=opds-catalog;kind=navigation"
ACQ = "application/atom+xml;profile=opds-catalog;kind=acquisition"
FEED_HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom" '
             'xmlns:dc="http://purl.org/dc/terms/" xmlns:opds="http://opds-spec.org/2010/catalog">')


def utc(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def edition_entries(series: Series):
    """Return (opds_entries, html_rows, newest_updated) for one series."""
    entries, rows, newest = [], [], None
    for ep in series.epubs(reverse=True):
        d = ep.stem.replace(series.prefix + "-", "")
        date = dt.date.fromisoformat(d)
        summary = epub_summary(ep)
        title = f"{series.title} — {date.strftime('%a %d %b %Y')}"
        updated = dt.datetime.combine(date, dt.time(7, 30), LOCAL_TZ).astimezone(dt.timezone.utc)
        newest = newest or updated
        rel = f"{series.editions_rel}/{ep.name}"
        entries.append(f"""  <entry>
    <title>{esc(title)}</title>
    <id>urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, series.uid_ns + '/' + d)}</id>
    <updated>{utc(updated)}</updated>
    <author><name>{esc(AUTHOR)}</name></author>
    <dc:language>en</dc:language>
    <summary>{esc(summary)}</summary>
    <link rel="http://opds-spec.org/acquisition" href="{esc(url(rel))}" type="application/epub+zip"/>
  </entry>""")
        rows.append(f'<li><a href="{esc(rel)}">{esc(title)}</a></li>')
    return entries, rows, newest


def write_catalog():
    now = utc(dt.datetime.now(dt.timezone.utc))
    (ROOT / "opds").mkdir(exist_ok=True)
    folders, html_sections = [], []
    for series in SERIES:
        entries, rows, newest = edition_entries(series)
        feed_rel = f"opds/{series.key}.xml"
        (ROOT / feed_rel).write_text(f"""{FEED_HEAD}
  <id>urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, series.uid_ns + '/catalog')}</id>
  <title>{esc(series.title)}</title>
  <updated>{now}</updated>
  <author><name>{esc(AUTHOR)}</name></author>
  <link rel="self" href="{esc(url(feed_rel))}" type="{ACQ}"/>
  <link rel="start" href="{esc(url('opds.xml'))}" type="{NAV}"/>
  <link rel="up" href="{esc(url('opds.xml'))}" type="{NAV}"/>
{chr(10).join(entries)}
</feed>
""", encoding="utf-8")
        latest = f"latest: {newest.astimezone(LOCAL_TZ).strftime('%a %d %b')}" if newest else "no editions yet"
        folders.append(f"""  <entry>
    <title>{esc(series.title)}</title>
    <id>urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'daily-brief/folder/' + series.key)}</id>
    <updated>{utc(newest) if newest else now}</updated>
    <content type="text">{esc(series.blurb)} — {len(entries)} editions, {esc(latest)}</content>
    <link rel="subsection" href="{esc(url(feed_rel))}" type="{ACQ}"/>
  </entry>""")
        html_sections.append(f"<h2>{esc(series.title)}</h2>\n<ul>\n{chr(10).join(rows) or '<li>No editions yet</li>'}\n</ul>")
        print(f"catalog {series.key}: {len(entries)} editions")

    (ROOT / "opds.xml").write_text(f"""{FEED_HEAD}
  <id>urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'daily-brief/root')}</id>
  <title>{esc(TITLE)}</title>
  <updated>{now}</updated>
  <author><name>{esc(AUTHOR)}</name></author>
  <link rel="self" href="{esc(url('opds.xml'))}" type="{NAV}"/>
  <link rel="start" href="{esc(url('opds.xml'))}" type="{NAV}"/>
{chr(10).join(folders)}
</feed>
""", encoding="utf-8")
    (ROOT / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(TITLE)}</title>
<style>body{{font-family:Georgia,serif;max-width:36em;margin:2em auto;padding:0 1em;line-height:1.5}}</style></head>
<body><h1>{esc(TITLE)}</h1>
<p>Briefings as EPUB, grouped into folders. On your e-reader, add this OPDS catalog: <code>{esc(url('opds.xml'))}</code></p>
{chr(10).join(html_sections)}
</body></html>
""", encoding="utf-8")


def main(argv):
    argv = list(argv)
    only = None
    if "--series" in argv:
        i = argv.index("--series")
        only = SERIES_BY_KEY[argv[i + 1]]
        del argv[i:i + 2]
    for series in SERIES:
        if only and series is not only:
            continue
        if "--all" in argv:
            targets = sorted(series.digests.glob("*.json"))
        elif argv:
            # bare dates without --series refer to the daily brief
            if only is None and series.key != "daily":
                continue
            targets = [series.digests / f"{a}.json" for a in argv]
        else:
            targets = [p for p in sorted(series.digests.glob("*.json")) if not series.epub_for(p.stem).exists()]
        for t in targets:
            build_epub(series, t)
        prune(series)
    write_catalog()


if __name__ == "__main__":
    main(sys.argv[1:])
