#!/usr/bin/env python3
"""Daily Brief builder.

Turns digests/YYYY-MM-DD.json into editions/daily-brief-YYYY-MM-DD.epub,
then regenerates opds.xml (OPDS 1.2 catalog) and index.html listing the
most recent editions. Standard library only, so it runs anywhere.

Usage:
    python3 build.py                 # build every digest that has no EPUB yet
    python3 build.py 2026-10-28      # (re)build one date
    python3 build.py --all           # rebuild everything

Digest JSON schema:
{
  "date": "2026-10-28",
  "edition_title": "Daily Brief",            # optional
  "sections": [
    {"title": "World Business: Tech",
     "items": [
        {"headline": "...", "summary": "...", "source": "Reuters",
         "url": "https://..."}
     ]}
  ]
}
"""
import datetime as dt
import html
import json
import os
import sys
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIGESTS = ROOT / "digests"
EDITIONS = ROOT / "editions"
CONFIG = json.loads((ROOT / "config.json").read_text()) if (ROOT / "config.json").exists() else {}
BASE_URL = CONFIG.get("base_url", "").rstrip("/")
KEEP = int(CONFIG.get("keep_editions", 14))
TITLE = CONFIG.get("title", "Daily Brief")
AUTHOR = CONFIG.get("author", "Claude")
LOCAL_TZ = dt.timezone(dt.timedelta(hours=8))  # Singapore

CSS = """
body { font-family: serif; line-height: 1.4; margin: 0 0.3em; }
h1 { font-size: 1.35em; margin: 0.4em 0 0.6em; }
h2 { font-size: 1.05em; margin: 1.1em 0 0.25em; line-height: 1.25; }
p { margin: 0 0 0.4em; text-align: left; }
p.src { font-size: 0.8em; font-style: italic; margin-bottom: 0.9em; }
p.meta { font-size: 0.85em; }
ol.toc { padding-left: 1.2em; }
ol.toc li { margin-bottom: 0.4em; }
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


def build_epub(digest_path: Path) -> Path:
    data = json.loads(digest_path.read_text(encoding="utf-8"))
    date = dt.date.fromisoformat(data["date"])
    sections = [s for s in data["sections"] if s.get("items")]
    book_title = f"{data.get('edition_title', TITLE)} — {date.strftime('%d %b %Y')}"
    book_id = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'daily-brief/' + data['date'])}"
    modified = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    files = {}  # name -> content
    # Cover / contents page
    toc_items = "\n".join(
        f'<li><a href="s{i:02d}.xhtml">{esc(s["title"])}</a> ({len(s["items"])})</li>'
        for i, s in enumerate(sections, 1)
    )
    total = sum(len(s["items"]) for s in sections)
    files["cover.xhtml"] = xhtml(book_title, f"""
<h1>{esc(TITLE)}</h1>
<p class="meta">{esc(pretty_date(date))}<br/>{total} stories · {len(sections)} sections</p>
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
<dc:publisher>{esc(TITLE)}</dc:publisher>
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

    EDITIONS.mkdir(exist_ok=True)
    out = EDITIONS / f"daily-brief-{date.isoformat()}.epub"
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
    print(f"built {out.relative_to(ROOT)} ({total} stories)")
    return out


def url(path):
    return f"{BASE_URL}/{path}" if BASE_URL else path


def prune():
    eps = sorted(EDITIONS.glob("daily-brief-*.epub"))
    for old in eps[:-KEEP] if len(eps) > KEEP else []:
        old.unlink()
        print(f"pruned {old.name}")


def write_catalog():
    eps = sorted(EDITIONS.glob("daily-brief-*.epub"), reverse=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []
    rows = []
    for ep in eps:
        d = ep.stem.replace("daily-brief-", "")
        date = dt.date.fromisoformat(d)
        digest = DIGESTS / f"{d}.json"
        summary = ""
        if digest.exists():
            secs = json.loads(digest.read_text(encoding="utf-8"))["sections"]
            summary = f"{sum(len(s['items']) for s in secs)} stories: " + ", ".join(s["title"] for s in secs)
        title = f"{TITLE} — {date.strftime('%a %d %b %Y')}"
        updated = dt.datetime.combine(date, dt.time(7, 30), LOCAL_TZ).astimezone(dt.timezone.utc)
        entries.append(f"""  <entry>
    <title>{esc(title)}</title>
    <id>urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'daily-brief/' + d)}</id>
    <updated>{updated.strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>
    <author><name>{esc(AUTHOR)}</name></author>
    <dc:language>en</dc:language>
    <summary>{esc(summary)}</summary>
    <link rel="http://opds-spec.org/acquisition" href="{esc(url('editions/' + ep.name))}" type="application/epub+zip"/>
  </entry>""")
        rows.append(f'<li><a href="editions/{ep.name}">{esc(title)}</a></li>')

    feed = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'daily-brief/catalog')}</id>
  <title>{esc(TITLE)}</title>
  <updated>{now}</updated>
  <author><name>{esc(AUTHOR)}</name></author>
  <link rel="self" href="{esc(url('opds.xml'))}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
  <link rel="start" href="{esc(url('opds.xml'))}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
{chr(10).join(entries)}
</feed>
"""
    (ROOT / "opds.xml").write_text(feed, encoding="utf-8")
    (ROOT / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(TITLE)}</title>
<style>body{{font-family:Georgia,serif;max-width:36em;margin:2em auto;padding:0 1em;line-height:1.5}}</style></head>
<body><h1>{esc(TITLE)}</h1>
<p>Daily news briefing as EPUB. On your e-reader, add this OPDS catalog: <code>{esc(url('opds.xml'))}</code></p>
<ul>
{chr(10).join(rows)}
</ul></body></html>
""", encoding="utf-8")
    print(f"catalog: {len(eps)} editions")


def main(argv):
    targets = []
    if "--all" in argv:
        targets = sorted(DIGESTS.glob("*.json"))
    elif argv:
        targets = [DIGESTS / f"{a}.json" for a in argv]
    else:
        targets = [p for p in sorted(DIGESTS.glob("*.json"))
                   if not (EDITIONS / f"daily-brief-{p.stem}.epub").exists()]
    for t in targets:
        build_epub(t)
    prune()
    write_catalog()


if __name__ == "__main__":
    main(sys.argv[1:])
