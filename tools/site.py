#!/usr/bin/env python3
"""Rebekka's vocab site: add a lesson page, rebuild the home page.

  python3 tools/site.py add <page.html> --date 2026-11-21 --slug p124-125-travel --vocab vocab.json
  python3 tools/site.py build

`add` copies a built vocab page to lessons/<date>-<slug>/index.html, gives it a link back
to the home page, records it in lessons.json and rebuilds index.html. Adding a page with
the same date and slug again replaces it (same link). `build` only rebuilds index.html.
"""
import argparse
import datetime as dt
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LESSONS = ROOT / "lessons.json"
STUDENT = "Rebekka"
SUBTITLE = "Palestinian Arabic, with audio for every word"

BACK_CSS = (".home-link{display:inline-flex;align-items:center;gap:6px;margin-bottom:10px;font-size:.95rem;"
            "font-weight:700;color:var(--ink-2);text-decoration:none}"
            ".home-link:hover{color:var(--ink);text-decoration:underline}")
BACK_LINK = '<a class="home-link" href="../../">&larr; All of %s&rsquo;s lessons</a>' % STUDENT


def load():
    if LESSONS.exists():
        return json.loads(LESSONS.read_text(encoding="utf-8"))
    return {"student": STUDENT, "lessons": []}


def save(data):
    LESSONS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_back_link(page):
    if "home-link" in page:
        return page
    page = page.replace('<h1 id="title">', BACK_LINK + '<h1 id="title">', 1)
    page = page.replace("</style>", BACK_CSS + "\n</style>", 1)
    if "home-link" not in page:
        sys.exit("couldn't place the back link: the page has no <h1 id=\"title\">")
    return page


def cmd_add(a):
    src = pathlib.Path(a.page)
    date = dt.date.fromisoformat(a.date)
    slug = re.sub(r"[^a-z0-9-]+", "-", a.slug.lower()).strip("-")
    folder = "lessons/%s-%s/" % (date.isoformat(), slug)
    out = ROOT / folder / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(add_back_link(src.read_text(encoding="utf-8")), encoding="utf-8")

    vocab = json.loads(pathlib.Path(a.vocab).read_text(encoding="utf-8"))
    rows = [r for s in vocab["sections"] for r in s["rows"]]
    entry = {
        "date": date.isoformat(),
        "title": a.title or vocab.get("title", slug),
        "path": folder,
        "words": len(rows),
        "preview": [r["tr"] for r in rows],
    }
    data = load()
    data["lessons"] = [l for l in data["lessons"] if l["path"] != folder] + [entry]
    save(data)
    build()
    print("added", folder, "(%d words)" % len(rows))


def fmt_day(d):
    return d.strftime("%A"), str(d.day), d.strftime("%B %Y")


def build():
    data = load()
    lessons = sorted(data["lessons"], key=lambda l: (l["date"], l["path"]), reverse=True)
    total = sum(l["words"] for l in lessons)

    months, out = [], []
    by_date = {}
    for l in lessons:
        by_date.setdefault(l["date"], []).append(l)
    newest = lessons[0] if lessons else None
    for date in sorted(by_date, reverse=True):
        d = dt.date.fromisoformat(date)
        weekday, day, month = fmt_day(d)
        if not months or months[-1] != month:
            if months:
                out.append("</section>")
            months.append(month)
            out.append('<section class="month"><h2>%s</h2>' % html.escape(month))
        cards = []
        for l in by_date[date]:
            prev = l["preview"]
            chips = "".join('<span class="chip">%s</span>' % html.escape(w) for w in prev[:6])
            more = '<span class="more">+%d more</span>' % (len(prev) - 6) if len(prev) > 6 else ""
            badge = '<span class="new">Latest</span>' if l is newest else ""
            cards.append(
                '<a class="card" href="%s">'
                '<div class="card-top"><h3>%s</h3>%s<span class="count">%d words</span>'
                '<svg class="go" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
                '<div class="chips">%s%s</div></a>'
                % (html.escape(l["path"]), html.escape(l["title"]), badge, l["words"], chips, more))
        out.append(
            '<div class="day" id="d%s"><div class="date"><span class="dnum">%s</span><span class="wday">%s</span></div>'
            '<div class="cards">%s</div></div>' % (date, day, weekday[:3], "".join(cards)))
    if months:
        out.append("</section>")
    body = "\n".join(out) or '<p class="empty">No lessons yet.</p>'
    meta = "%d words in %d lesson%s" % (total, len(lessons), "" if len(lessons) == 1 else "s")

    page = TEMPLATE.replace("__STUDENT__", html.escape(STUDENT)).replace("__SUB__", html.escape(SUBTITLE))
    page = page.replace("__META__", meta).replace("__BODY__", body)
    (ROOT / "index.html").write_text(page, encoding="utf-8")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__STUDENT__: Arabic vocabulary</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;700;800&display=swap">
<style>
:root{
  --paper:#F3F5F8; --surface:#FFFFFF; --ink:#172033; --ink-2:#4A5468; --muted:#7A8497;
  --line:#DDE2EA; --line-soft:#ECEFF4; --accent:#1C68A8; --accent-soft:#E8F0F8;
  --sans:"Atkinson Hyperlegible Next", "Atkinson Hyperlegible", ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}
.head-in{max-width:760px;margin:0 auto;padding:40px 24px 8px}
h1{margin:0;font-size:clamp(2.2rem,6vw,3rem);font-weight:800;letter-spacing:-.02em;line-height:1.05}
.sub{margin-top:8px;color:var(--ink-2);font-size:1.05rem}
.meta{margin-top:4px;color:var(--muted);font-size:.95rem}
main{max-width:760px;margin:0 auto;padding:22px 24px 80px}
.month{margin-bottom:30px}
.month h2{margin:0 0 12px;font-size:1.05rem;font-weight:800;color:var(--ink-2)}
.day{display:grid;grid-template-columns:56px 1fr;gap:16px;margin-bottom:14px}
.date{display:flex;flex-direction:column;align-items:center;padding-top:16px}
.dnum{font-size:1.7rem;font-weight:800;line-height:1;color:var(--accent)}
.wday{margin-top:4px;font-size:.85rem;color:var(--muted)}
.cards{display:flex;flex-direction:column;gap:10px;min-width:0}
.card{display:block;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px 18px;color:inherit;text-decoration:none;box-shadow:0 1px 2px rgba(23,32,51,.04)}
.card:hover{border-color:var(--accent)}
.card:focus-visible{outline:3px solid #2B6CDB;outline-offset:2px}
.card-top{display:flex;align-items:center;gap:10px}
.card h3{margin:0;font-size:1.2rem;font-weight:800;line-height:1.3}
.new{font-size:.8rem;font-weight:700;color:var(--accent);background:var(--accent-soft);padding:2px 9px;border-radius:999px}
.count{margin-left:auto;font-size:.9rem;color:var(--muted);white-space:nowrap}
.go{width:16px;height:16px;color:var(--muted);flex:none}
.card:hover .go{color:var(--accent)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;align-items:center}
.chip{font-size:1rem;font-weight:700;padding:3px 10px;border-radius:8px;background:var(--line-soft);color:var(--ink)}
.more{font-size:.9rem;color:var(--muted)}
.empty{color:var(--muted)}
@media (max-width:560px){
  .head-in{padding:28px 16px 4px}
  main{padding:18px 16px 60px}
  .day{grid-template-columns:40px 1fr;gap:10px}
  .dnum{font-size:1.4rem}
  .card{padding:14px}
}
</style>
</head>
<body>
<header><div class="head-in">
<h1>__STUDENT__</h1>
<div class="sub">__SUB__</div>
<div class="meta">__META__</div>
</div></header>
<main>
__BODY__
</main>
</body>
</html>
"""


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("add")
    pa.add_argument("page")
    pa.add_argument("--date", required=True)
    pa.add_argument("--slug", required=True)
    pa.add_argument("--vocab", required=True)
    pa.add_argument("--title")
    sub.add_parser("build")
    a = p.parse_args()
    cmd_add(a) if a.cmd == "add" else build()
