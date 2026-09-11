#!/usr/bin/env python3
"""
Keep the shared chrome — <head>, the header and the footer — identical on every
page of devnest.sk.

The site has no build step: every file in the repository is exactly what the web
server hands out. That is deliberate, but it means the header exists on every
page, and every copy drifts. This script owns those regions instead. Each page
marks them:

    <!-- chrome:head -->  … generated …  <!-- /chrome:head -->
    <!-- chrome:nav -->   … generated …  <!-- /chrome:nav -->
    <!-- chrome:footer -->… generated …  <!-- /chrome:footer -->

A page of the manual marks a fourth, the list of its own pages:

    <!-- chrome:docsnav -->… generated …  <!-- /chrome:docsnav -->

Everything between a pair of markers is rewritten from the templates below.
Anything outside them is the page's own and is never touched.

    python3 tools/chrome.py            # rewrite every page
    python3 tools/chrome.py --check    # exit 1 if a page is out of date

Add a page by adding it to PAGES, or, for a page of the manual, to DOCS.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SITE = "DevNest"
COMPANY = "DevNest s.r.o."
TAGLINE = "Mac software from Slovakia"
EMAIL = "contact@devnest.sk"
ORIGIN = "https://devnest.sk"

# The apps, in the order they appear in the header menu and on the home page.
# `state` picks the colour of the dot beside the name: green shipping, amber
# beta, grey still being built.
APPS = [
    {
        "id": "tracktiv",
        "name": "Tracktiv",
        "url": "/apps/tracktiv/",
        "icon": "/assets/img/apps/tracktiv/icon-256.png",
        "state": "beta",
        "state_label": "In beta",
        "summary": "Writes your working day down for you.",
    },
    {
        "id": "assetscout",
        "name": "AssetScout",
        "url": "/apps/assetscout/",
        "icon": "/assets/img/apps/assetscout/icon.svg",
        "state": "shipping",
        "state_label": "On the Mac App Store",
        "summary": "Finds the file when you know the date, not the folder.",
    },
]

# The manual for an app, in reading order. `group` opens a new heading in the
# sidebar; the pages under it keep it until the next one. The sidebar is
# generated from this list, so a page added here appears in the book
# everywhere at once — the same reason the header lives in this file.
DOCS_APP = "assetscout"
DOCS_ROOT = "/apps/assetscout/docs/"
DOCS = [
    {"slug": "", "title": "Welcome to AssetScout",
     "blurb": "What AssetScout is for, what it does to your files, and where to start reading."},
    {"slug": "first-scan/", "title": "Your first scan",
     "blurb": "From an empty window to a grid of results, in the order it happens."},
    {"slug": "dates/", "title": "Where the dates come from",
     "blurb": "Capture date, file dates, and why a photograph copied last week still lands "
              "in the month it was taken."},

    {"slug": "scanning/choosing/", "title": "Choosing what to scan", "group": "Scanning",
     "blurb": "The scan menu, dragging folders onto the window, and the locations macOS "
              "hides inside the Library."},
    {"slug": "scanning/collecting/", "title": "What a scan collects",
     "blurb": "How a file's type is decided, the five groups, and which of them a new "
              "scan starts with."},
    {"slug": "scanning/skipping/", "title": "What a scan leaves out",
     "blurb": "Application containers, the derived data inside a photo library, and files "
              "whose type nothing could name."},
    {"slug": "scanning/progress/", "title": "Following and stopping a scan",
     "blurb": "The two steps of a scan, what the progress bar means in each, and what "
              "stopping keeps."},

    {"slug": "window/groups/", "title": "Months and groups", "group": "The window",
     "blurb": "How the grid is divided, folding a month away, and choosing which date "
              "the division is built from."},
    {"slug": "window/selecting/", "title": "Selecting items",
     "blurb": "Click, shift, command, rubber band, select all, and finding your selection "
              "again after scrolling."},
    {"slug": "window/filter/", "title": "Filtering by type",
     "blurb": "The filter popover, groups and individual types, and how it differs from "
              "the setting of the same name."},
    {"slug": "window/search/", "title": "Searching by name",
     "blurb": "What the search field looks at, what it ignores, and how it works together "
              "with the filter."},
    {"slug": "window/labels/", "title": "What is written under a thumbnail",
     "blurb": "Dates or file names, and the mark on an item whose date is only a guess."},

    {"slug": "inspector/file-info/", "title": "File info and the map", "group": "The inspector",
     "blurb": "The section every file has, and the map above it."},
    {"slug": "inspector/photographs/", "title": "Photographs and EXIF",
     "blurb": "The four EXIF sections, the numbers written out as words, and the tags the "
              "app has never seen."},
    {"slug": "inspector/media/", "title": "Video, audio, text and documents",
     "blurb": "What each of the other four kinds of file reports about itself."},

    {"slug": "files/looking/", "title": "Looking at a file", "group": "Working with files",
     "blurb": "Quick Look, opening the file in its own application, and finding it in "
              "the Finder."},
    {"slug": "files/rotating/", "title": "Rotating and flipping",
     "blurb": "A quarter turn written to the file on disk, what it costs, and what it does "
              "to the month the file sits in."},
    {"slug": "files/moving/", "title": "The trash, and dragging files out",
     "blurb": "Moving files to the trash, and moving or copying them into the Finder by "
              "dragging."},

    {"slug": "reference/settings/", "title": "Settings", "group": "Reference",
     "blurb": "Both panes, switch by switch, with what each one is set to before you "
              "touch it."},
    {"slug": "reference/shortcuts/", "title": "Keyboard shortcuts",
     "blurb": "Every shortcut the app has, and the two the mouse has."},
    {"slug": "reference/messages/", "title": "Messages, and what they mean",
     "blurb": "Every message AssetScout can put on screen, why it appears, and what to "
              "do about it."},
    {"slug": "reference/privacy/", "title": "The sandbox and your files",
     "blurb": "What the app is allowed to read, how that permission is kept, and what "
              "leaves your Mac."},
]

# path → the page's own metadata. `app` skins the page and names it in the
# header; leave it out for the company pages.
PAGES = {
    "index.html": {
        "url": "/",
        "title": "DevNest — Mac software from Slovakia",
        "description": "DevNest s.r.o. is an independent software studio in Slovakia. "
                       "We build native macOS apps that are small, quiet, and keep "
                       "your data on your own machine.",
    },
    "apps/tracktiv/index.html": {
        "url": "/apps/tracktiv/",
        "app": "tracktiv",
        "title": "Tracktiv — the Mac time tracker that writes the day down for you · DevNest",
        "description": "Tracktiv records your working day on its own and hands it back at "
                       "the end of it: what you worked on, how long each project took, "
                       "where the breaks were. No timers, no account, nothing leaves your Mac.",
    },
    "apps/assetscout/index.html": {
        "url": "/apps/assetscout/",
        "app": "assetscout",
        "title": "AssetScout — find the file when you know the date · DevNest",
        "description": "AssetScout walks a folder and lays out every picture, video, "
                       "recording and document it finds in the order they were made, "
                       "grouped by month. Sandboxed, for macOS 14.4 and newer.",
    },
    "company/index.html": {
        "url": "/company/",
        "title": "Company · DevNest s.r.o.",
        "description": "DevNest s.r.o. is a software company in Slovakia building native "
                       "macOS software. Who we are and how we work.",
    },
    "support/index.html": {
        "url": "/support/",
        "title": "Support · DevNest",
        "description": "How to reach DevNest: bug reports, feature requests, questions "
                       "about Tracktiv or AssetScout.",
    },
    "privacy/index.html": {
        "url": "/privacy/",
        "title": "Privacy policy · DevNest",
        "description": "What DevNest apps store, where they store it, and why none of it "
                       "reaches us.",
    },
    "404.html": {
        "url": "/404.html",
        "title": "Page not found · DevNest",
        "description": "That page is not here.",
        "noindex": True,
    },
}

# The manual's pages are pages like any other, and their metadata follows from
# DOCS rather than being written out again here.
for _page in DOCS:
    PAGES[("apps/assetscout/docs/%sindex.html" % _page["slug"])] = {
        "url": DOCS_ROOT + _page["slug"],
        "app": DOCS_APP,
        "docs": True,
        "title": "%s — AssetScout manual · DevNest" % _page["title"],
        "description": _page["blurb"],
    }

# --------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------

HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{origin}{url}">{robots}

<meta property="og:type" content="website">
<meta property="og:site_name" content="{site}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{origin}{url}">
<meta property="og:image" content="{origin}/assets/img/brand/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{origin}/assets/img/brand/og.png">

<link rel="icon" href="/assets/img/brand/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/img/brand/icon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/img/brand/icon-180.png">

<!-- Every page sets its text in this file, so it is fetched together with the
     stylesheet instead of after it. Then the text rarely shows up in the
     system font first and switches a moment later. -->
<link rel="preload" href="/assets/fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>

<link rel="stylesheet" href="/assets/css/site.css">
<link rel="stylesheet" href="/assets/css/themes.css">

<!-- The stored appearance is applied before the first paint, so a visitor who
     chose dark never sees a white flash on the way in. -->
<script>
(function () {{
    try {{
        var stored = localStorage.getItem("appearance");
        if (stored === "light" || stored === "dark") {{
            document.documentElement.setAttribute("data-appearance", stored);
        }}
    }} catch (e) {{ /* private browsing: fall back to the system setting */ }}
    document.documentElement.classList.add("js");
}})();
</script>"""

# The logo carries the company name itself, so nothing else needs to spell it
# out beside it. Two files because the wordmark is dark-on-transparent and
# needs a light-on-transparent twin for a dark page — same swap mechanism as
# the appearance-aware screenshots: see data-dark-source in site.js.
LOGO = """<picture class="brand__logo">
                <source data-dark-source media="(prefers-color-scheme: dark)"
                        srcset="/assets/img/brand/DevNestLogoDark.svg">
                <img src="/assets/img/brand/DevNestLogo.svg" alt="DevNest" width="115" height="46">
            </picture>"""

MENU_ROW = """            <a class="menu__row{current}" href="{url}">
                <img class="menu__icon" src="{icon}" alt="" width="30" height="30" loading="lazy">
                <span class="menu__text">
                    <span class="menu__name">{name}<em class="dot dot--{state}"></em></span>
                    <span class="menu__sub">{summary}</span>
                </span>
            </a>"""

NAV = """<header class="nav" data-nav>
    <div class="wrap wrap--wide nav__inner">

        <a class="brand" href="/">
            {logo}{product}
        </a>

        <nav class="nav__links" aria-label="Main">
            <div class="menu" data-menu>
                <button class="menu__btn{apps_current}" type="button" aria-expanded="false" aria-controls="apps-menu">
                    Apps<span class="chev" aria-hidden="true"></span>
                </button>
                <div class="menu__panel" id="apps-menu" hidden>
{menu_rows}
                </div>
            </div>
            <a href="/company/"{company_current}>Company</a>
            <a href="/support/"{support_current}>Support</a>
        </nav>

        <button class="iconbtn appearance" type="button" data-appearance-toggle aria-label="Switch appearance">
            <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
                <circle cx="12" cy="12" r="4.2"></circle>
                <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"></path>
            </svg>
            <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M20 14.2A8.2 8.2 0 0 1 9.8 4 8.2 8.2 0 1 0 20 14.2z"></path>
            </svg>
            <svg class="icon-system" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="3.2" y="4.5" width="17.6" height="12" rx="2"></rect>
                <path d="M8.4 20h7.2M12 16.5v3.5"></path>
            </svg>
        </button>

        <button class="iconbtn burger" type="button" data-nav-toggle aria-expanded="false" aria-controls="nav-sheet" aria-label="Menu">
            <span aria-hidden="true"></span><span aria-hidden="true"></span>
        </button>
    </div>

    <div class="sheet" id="nav-sheet" data-nav-sheet hidden>
        <div class="wrap sheet__inner">
            <p class="sheet__head">Apps</p>
{menu_rows}
            <p class="sheet__head">DevNest</p>
            <a class="sheet__link" href="/company/">Company</a>
            <a class="sheet__link" href="/support/">Support</a>
            <a class="sheet__link" href="/privacy/">Privacy policy</a>
        </div>
    </div>
</header>"""

DOCSNAV = """<nav class="docside" data-docside aria-label="Manual">
    <button class="docside__btn" type="button" aria-expanded="false" aria-controls="docside-list">
        Manual<span class="chev" aria-hidden="true"></span>
    </button>
    <div class="docside__list" id="docside-list">
{rows}
    </div>
</nav>"""

FOOTER = """<footer class="footer">
    <div class="wrap wrap--wide">
        <div class="footer__grid">
            <div class="footer__brand">
                <a class="brand" href="/">
                    {logo}
                </a>
                <p class="footer__line">{tagline}</p>
            </div>

            <div class="footer__links">
                <div>
                    <h5>Apps</h5>
                    <ul>
{app_links}
                    </ul>
                </div>

                <div>
                    <h5>Company</h5>
                    <ul>
                        <li><a href="/company/">About DevNest</a></li>
                        <li><a href="/support/">Support</a></li>
                        <li><a href="/privacy/">Privacy policy</a></li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer__bottom">
            <span>© <span data-year>2026</span> {company}</span>
            <span class="mono">Made on a Mac, for the Mac.</span>
        </div>
    </div>
</footer>"""


def build_head(meta):
    return HEAD.format(
        title=meta["title"],
        description=meta["description"],
        origin=ORIGIN,
        url=meta["url"],
        site=SITE,
        robots='\n<meta name="robots" content="noindex">' if meta.get("noindex") else "",
    )


def build_nav(meta):
    app_id = meta.get("app")
    rows = "\n".join(
        MENU_ROW.format(current=" is-current" if a["id"] == app_id else "", **a) for a in APPS
    )
    product = ""
    if app_id:
        name = next(a["name"] for a in APPS if a["id"] == app_id)
        product = ('\n            <span class="brand__sep" aria-hidden="true">/</span>'
                   '\n            <span class="brand__product">%s</span>' % name)
    return NAV.format(
        logo=LOGO,
        product=product,
        menu_rows=rows,
        apps_current=" is-current" if app_id else "",
        company_current=' class="is-current"' if meta["url"].startswith("/company") else "",
        support_current=' class="is-current"' if meta["url"].startswith("/support") else "",
    )


def build_footer(meta):
    links = "\n".join(
        '                        <li><a href="%s">%s</a></li>' % (a["url"], a["name"]) for a in APPS
    )
    return FOOTER.format(logo=LOGO, tagline=TAGLINE, app_links=links,
                         email=EMAIL, company=COMPANY)


def build_docsnav(meta):
    """The list of pages, grouped. Each group's links are wrapped so the rail
    down their left is one border rather than one per link."""
    rows, group = [], []

    def flush():
        if group:
            rows.append('        <div class="docside__items">')
            rows.extend(group)
            rows.append("        </div>")
            group.clear()

    for page in DOCS:
        if "group" in page:
            flush()
            rows.append('        <p class="docside__group">%s</p>' % page["group"])
        url = DOCS_ROOT + page["slug"]
        current = ' aria-current="page"' if url == meta["url"] else ""
        group.append('            <a href="%s"%s>%s</a>' % (url, current, page["title"]))
    flush()
    return DOCSNAV.format(rows="\n".join(rows))


DOCSFEET = """<nav class="docfeet" aria-label="Manual pages">
{feet}
</nav>"""

DOCFOOT = """    <a class="docfoot{modifier}" href="{url}">
        <span>{kind}</span><b>{title}</b>
    </a>"""


def build_docsfeet(meta):
    """Previous and next, taken from the order of DOCS. Adding a page in the
    middle of the book re-links its neighbours by itself."""
    index = next(i for i, p in enumerate(DOCS) if DOCS_ROOT + p["slug"] == meta["url"])
    feet = []
    if index > 0:
        previous = DOCS[index - 1]
        feet.append(DOCFOOT.format(modifier="", kind="Previous",
                                   url=DOCS_ROOT + previous["slug"], title=previous["title"]))
    if index < len(DOCS) - 1:
        following = DOCS[index + 1]
        feet.append(DOCFOOT.format(modifier=" docfoot--next", kind="Next",
                                   url=DOCS_ROOT + following["slug"], title=following["title"]))
    return DOCSFEET.format(feet="\n".join(feet))


BUILDERS = {"head": build_head, "nav": build_nav, "footer": build_footer}
DOCS_BUILDERS = {"docsnav": build_docsnav, "docsfeet": build_docsfeet}


def rewrite(text, meta):
    builders = dict(BUILDERS)
    if meta.get("docs"):
        builders.update(DOCS_BUILDERS)
    for region, builder in builders.items():
        pattern = re.compile(
            r"(<!-- chrome:%s -->).*?(<!-- /chrome:%s -->)" % (region, region),
            re.DOTALL,
        )
        if not pattern.search(text):
            raise SystemExit("missing chrome:%s markers in %s" % (region, meta["url"]))
        block = builder(meta)
        text = pattern.sub(lambda m: m.group(1) + "\n" + block + "\n" + m.group(2), text, count=1)
    return text


def main():
    check = "--check" in sys.argv
    stale = []
    for path, meta in PAGES.items():
        file = ROOT / path
        if not file.exists():
            raise SystemExit("missing page: %s" % path)
        before = file.read_text()
        after = rewrite(before, meta)
        if before == after:
            continue
        if check:
            stale.append(path)
        else:
            file.write_text(after)
            print("updated %s" % path)
    if check and stale:
        print("out of date: %s" % ", ".join(stale))
        return 1
    if check:
        print("every page is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
