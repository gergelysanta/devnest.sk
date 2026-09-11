#!/usr/bin/env python3
"""
Keep everything that repeats on devnest.sk in one place.

The site has no build step: every file in the repository is exactly what the
web server hands out. That is deliberate, but it means the header exists on
every page, and every copy drifts. So this script owns the parts that repeat
and writes them into the files, between comment markers. Anything outside the
markers belongs to the page and is never touched.

Every page has two regions, one at each end:

    <!doctype html>
    <html lang="en">
    <!-- chrome:top -->
        <head>, <body>, the header, and the opening of the page's layout
    <!-- /chrome:top -->
        … the page's own content …
    <!-- chrome:bottom -->
        the end of the layout, the footer and the script
    <!-- /chrome:bottom -->
    </html>

What the layout adds depends on the page (see LAYOUTS). A page of a manual
also gets its sidebar, its group, its title and its previous and next links,
all from the manual's table of contents in MANUALS.

A page can ask for a component anywhere in its own content. The marker names
the component and can carry arguments. A marker must start its line:

    <!-- chrome:store-badge -->            <!-- /chrome:store-badge -->
    <!-- chrome:doc-cards dates/ first-scan/ -->  <!-- /chrome:doc-cards -->

The stylesheets have one kind of region, the dark colours for a visitor whose
system is dark (see build_dark_system). sitemap.xml is written whole.

    python3 tools/chrome.py            # rewrite everything
    python3 tools/chrome.py --check    # exit 1 if a file is out of date

To add a page, add it to PAGES. To add a page to a manual, add it to MANUALS.
"""

import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SITE = "DevNest"
COMPANY = "DevNest s.r.o."
TAGLINE = "Mac software from Slovakia"
ORIGIN = "https://devnest.sk"

# --------------------------------------------------------------------------
# The apps
# --------------------------------------------------------------------------

# In the order they appear in the header menu, on the home page and in the
# footer. `state` picks the colour of the dot beside the name: green shipping,
# amber beta, grey still being built. `summary` is the line in the header menu,
# `card` the text of the app's card on the home page. `icon_dark` is optional.
# `store` is the App Store link; the page's own badges and the header's copy
# of them all come from it (see the store-badge component).
APPS = [
    {
        "id": "tracktiv",
        "name": "Tracktiv",
        "url": "/apps/tracktiv/",
        "icon": "/assets/img/apps/tracktiv/icon-256.png",
        "state": "beta",
        "state_label": "Beta · TestFlight",
        "summary": "Writes your working day down for you.",
        "card": "A time tracker for people who keep three projects going at once. It "
                "records the working day while the day happens and hands it back at the "
                "end of it — no timers, no account, nothing leaves the Mac.",
    },
    {
        "id": "assetscout",
        "name": "AssetScout",
        "url": "/apps/assetscout/",
        "icon": "/assets/img/apps/assetscout/icon.svg",
        "icon_dark": "/assets/img/apps/assetscout/icon-dark.svg",
        "state": "shipping",
        "state_label": "App Store",
        "summary": "Finds the file when you know the date, not the folder.",
        "card": "Point it at a folder or a whole drive and it lays out every picture, "
                "video, recording and document on it, in the order they were made. For "
                "when you know the date but not the folder.",
        # TODO: swap in the real product URL once the listing is live.
        "store": "https://apps.apple.com/app/assetscout",
    },
]

APP = {app["id"]: app for app in APPS}

# DevNest's own pages. `header` also puts the link in the header's row; the
# mobile menu and the footer list all of them. `footer` is the footer's
# wording, where it differs from `label`.
COMPANY_PAGES = [
    {"url": "/company/", "label": "Company", "footer": "About DevNest", "header": True},
    {"url": "/support/", "label": "Support", "header": True},
    {"url": "/privacy/", "label": "Privacy policy"},
]

# --------------------------------------------------------------------------
# The manuals
# --------------------------------------------------------------------------

# One manual per app, at the app's URL + "docs/", its pages in reading order.
# `group` opens a new heading in the sidebar, and the pages after it keep it
# until the next one. The pages before the first group have no heading in the
# sidebar; the small label above their title says `intro` instead. `blurb` is
# the page's meta description, and the text of its card where the app page
# links to it (see the doc-cards component).
#
# Adding a page here puts it in the sidebar of every page of the manual, and
# re-links the previous and next buttons of its neighbours.
MANUALS = {
    "assetscout": {
        "intro": "Getting started",
        "pages": [
            {"slug": "", "title": "Welcome to AssetScout",
             "blurb": "What AssetScout is for, what it does to your files, and where to start "
                      "reading."},
            {"slug": "first-scan/", "title": "Your first scan",
             "blurb": "From an empty window to a grid of results, in the order it happens."},
            {"slug": "dates/", "title": "Where the dates come from",
             "blurb": "Capture date, file dates, and why a photograph copied last week still "
                      "lands in the month it was taken."},

            {"slug": "scanning/choosing/", "title": "Choosing what to scan", "group": "Scanning",
             "blurb": "The scan menu, dragging folders onto the window, and the locations macOS "
                      "hides inside the Library."},
            {"slug": "scanning/collecting/", "title": "What a scan collects",
             "blurb": "How a file's type is decided, the five groups, and which of them a new "
                      "scan starts with."},
            {"slug": "scanning/skipping/", "title": "What a scan leaves out",
             "blurb": "Application containers, the derived data inside a photo library, and "
                      "files whose type nothing could name."},
            {"slug": "scanning/progress/", "title": "Following and stopping a scan",
             "blurb": "The two steps of a scan, what the progress bar means in each, and what "
                      "stopping keeps."},

            {"slug": "window/groups/", "title": "Months and groups", "group": "The window",
             "blurb": "How the grid is divided, folding a month away, and choosing which date "
                      "the division is built from."},
            {"slug": "window/selecting/", "title": "Selecting items",
             "blurb": "Click, shift, command, rubber band, select all, and finding your "
                      "selection again after scrolling."},
            {"slug": "window/filter/", "title": "Filtering by type",
             "blurb": "The filter popover, groups and individual types, and how it differs "
                      "from the setting of the same name."},
            {"slug": "window/search/", "title": "Searching by name",
             "blurb": "What the search field looks at, what it ignores, and how it works "
                      "together with the filter."},
            {"slug": "window/labels/", "title": "What is written under a thumbnail",
             "blurb": "Dates or file names, and the mark on an item whose date is only a "
                      "guess."},

            {"slug": "inspector/file-info/", "title": "File info and the map",
             "group": "The inspector",
             "blurb": "The section every file has, and the map above it."},
            {"slug": "inspector/photographs/", "title": "Photographs and EXIF",
             "blurb": "The four EXIF sections, the numbers written out as words, and the tags "
                      "the app has never seen."},
            {"slug": "inspector/media/", "title": "Video, audio, text and documents",
             "blurb": "What each of the other four kinds of file reports about itself."},

            {"slug": "files/looking/", "title": "Looking at a file", "group": "Working with files",
             "blurb": "Quick Look, opening the file in its own application, and finding it in "
                      "the Finder."},
            {"slug": "files/rotating/", "title": "Rotating and flipping",
             "blurb": "A quarter turn written to the file on disk, what it costs, and what it "
                      "does to the month the file sits in."},
            {"slug": "files/moving/", "title": "The trash, and dragging files out",
             "blurb": "Moving files to the trash, and moving or copying them into the Finder "
                      "by dragging."},

            {"slug": "reference/settings/", "title": "Settings", "group": "Reference",
             "blurb": "Both panes, switch by switch, with what each one is set to before you "
                      "touch it."},
            {"slug": "reference/shortcuts/", "title": "Keyboard shortcuts",
             "blurb": "Every shortcut the app has, and the two the mouse has."},
            {"slug": "reference/messages/", "title": "Messages, and what they mean",
             "blurb": "Every message AssetScout can put on screen, why it appears, and what "
                      "to do about it."},
            {"slug": "reference/privacy/", "title": "The sandbox and your files",
             "blurb": "What the app is allowed to read, how that permission is kept, and what "
                      "leaves your Mac."},
        ],
    },
}

# --------------------------------------------------------------------------
# The pages
# --------------------------------------------------------------------------

# path → the page's own metadata. `app` skins the page in the app's colour and
# puts the app's name beside DevNest in the header; leave it out for the
# company pages. `layout` is a key of LAYOUTS, "page" if left out. `nav_cta`
# repeats the app's store badge and manual link in the header, once the
# page's own have scrolled away. The pages of a manual are not listed here:
# they follow from MANUALS, and are put right after their app's page.
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
        "nav_cta": True,
        "title": "AssetScout — find the file when you know the date · DevNest",
        "description": "AssetScout walks a folder and lays out every picture, video, "
                       "recording and document it finds in the order they were made, "
                       "grouped by month. Sandboxed, for macOS 14.4 and newer.",
    },
    "company/index.html": {
        "url": "/company/",
        "layout": "prose",
        "title": "Company · DevNest s.r.o.",
        "description": "DevNest s.r.o. is a software company in Slovakia building native "
                       "macOS software. Who we are and how we work.",
    },
    "support/index.html": {
        "url": "/support/",
        "layout": "prose",
        "title": "Support · DevNest",
        "description": "How to reach DevNest: bug reports, feature requests, questions "
                       "about Tracktiv or AssetScout.",
    },
    "privacy/index.html": {
        "url": "/privacy/",
        "layout": "prose",
        "title": "Privacy policy · DevNest",
        "description": "What DevNest apps store, where they store it, and why none of it "
                       "reaches us.",
    },
    "404.html": {
        "url": "/404.html",
        "layout": "prose",
        "title": "Page not found · DevNest",
        "description": "That page is not here.",
        "noindex": True,
    },
}


def manual_root(app):
    return app["url"] + "docs/"


def manual_pages(app_id):
    """The pages of one manual, with the metadata PAGES would hold for them."""
    app, manual = APP[app_id], MANUALS[app_id]
    group = manual["intro"]
    pages = {}
    for index, page in enumerate(manual["pages"]):
        group = page.get("group", group)
        url = manual_root(app) + page["slug"]
        pages[url.lstrip("/") + "index.html"] = {
            "url": url,
            "app": app_id,
            "layout": "docs",
            "title": "%s — %s manual · %s" % (page["title"], app["name"], SITE),
            "description": page["blurb"],
            "index": index,
            "group": group,
        }
    return pages


def all_pages():
    """PAGES, with each manual inserted right after its app's page. This is
    also the order of sitemap.xml."""
    pages = {}
    for path, meta in PAGES.items():
        pages[path] = meta
        app_id = meta.get("app")
        if app_id in MANUALS and meta["url"] == APP[app_id]["url"]:
            pages.update(manual_pages(app_id))
    return pages


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def indent(text, prefix):
    """Indent every line that has text on it. Empty lines stay empty."""
    return "\n".join(prefix + line if line else line for line in text.split("\n"))


def wrap(text, prefix):
    """Running text, broken into lines of at most 92 characters."""
    return textwrap.fill(text, width=92, initial_indent=prefix, subsequent_indent=prefix)


def icon(name):
    """An icon from assets/img/icons.svg. Its size and stroke width come from
    the CSS of the place it sits in."""
    return ('<svg aria-hidden="true"><use href="/assets/img/icons.svg#%s"></use></svg>' % name)


def app_icon(app, cls, size, lazy=False):
    """An app's icon. With a dark version of its own it is a <picture>, and the
    browser picks the file that matches the appearance (see data-dark-source
    in site.js). The class goes on the outermost element either way."""
    loading = ' loading="lazy"' if lazy else ""
    if "icon_dark" not in app:
        return '<img class="%s" src="%s" alt="" width="%d" height="%d"%s>' % (
            cls, app["icon"], size, size, loading)
    return ('<picture class="%s">\n'
            '    <source data-dark-source media="(prefers-color-scheme: dark)"\n'
            '            srcset="%s">\n'
            '    <img src="%s" alt="" width="%d" height="%d"%s>\n'
            '</picture>') % (cls, app["icon_dark"], app["icon"], size, size, loading)


# --------------------------------------------------------------------------
# <head>
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


def build_head(meta):
    return HEAD.format(
        title=meta["title"],
        description=meta["description"],
        origin=ORIGIN,
        url=meta["url"],
        site=SITE,
        robots='\n<meta name="robots" content="noindex">' if meta.get("noindex") else "",
    )


# --------------------------------------------------------------------------
# The header
# --------------------------------------------------------------------------

# The logo carries the company name itself, so nothing else needs to spell it
# out beside it. Two files because the wordmark is dark-on-transparent and
# needs a light-on-transparent twin for a dark page — same swap mechanism as
# the appearance-aware screenshots: see data-dark-source in site.js.
LOGO = """<picture class="brand__logo">
    <source data-dark-source media="(prefers-color-scheme: dark)"
            srcset="/assets/img/brand/DevNestLogoDark.svg">
    <img src="/assets/img/brand/DevNestLogo.svg" alt="DevNest" width="115" height="46">
</picture>"""

# One app in the header menu. The same row is used in the mobile sheet.
MENU_ROW = """<a class="menu__row{current}" href="{url}">
{app_icon}
    <span class="menu__text">
        <span class="menu__name">{name}<em class="dot dot--{state}"></em></span>
        <span class="menu__sub">{summary}</span>
    </span>
</a>"""

NAV = """<header class="nav" data-nav>
    <div class="wrap wrap--wide nav__inner">

        <a class="brand" href="/">
{logo}{product}
        </a>{cta}

        <nav class="nav__links" aria-label="Main">
            <div class="menu" data-menu>
                <button class="menu__btn{apps_current}" type="button" aria-expanded="false" aria-controls="apps-menu">
                    Apps<span class="chev" aria-hidden="true"></span>
                </button>
                <div class="menu__panel" id="apps-menu" hidden>
{panel_rows}
                </div>
            </div>
{header_links}
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
{sheet_rows}
            <p class="sheet__head">{site}</p>
{sheet_links}
        </div>
    </div>
</header>"""

# The page's two buttons, repeated in the header. They stay hidden until
# site.js sees that no store badge of the page itself is on screen. Apple
# asks for one badge per layout, so the header copy never shows next to one.
NAV_CTA = """<div class="nav__cta" data-nav-cta>
{badge}{manual}
</div>"""


def build_nav(meta):
    app_id = meta.get("app")
    rows = "\n".join(
        MENU_ROW.format(current=" is-current" if app["id"] == app_id else "",
                        app_icon=indent(app_icon(app, "appicon menu__icon", 30, lazy=True), "    "),
                        **app)
        for app in APPS
    )
    product = cta = ""
    if app_id:
        app = APP[app_id]
        product = ('\n            <span class="brand__sep" aria-hidden="true">/</span>'
                   '\n            <span class="brand__product">%s</span>' % app["name"])
        if meta.get("nav_cta"):
            manual = ""
            if app_id in MANUALS:
                manual = ('\n    <a class="btn btn--ghost" href="%s">Read the manual</a>'
                          % manual_root(app))
            cta = "\n\n" + indent(NAV_CTA.format(badge=indent(build_store_badge(meta, []), "    "),
                                                 manual=manual), "        ")

    def current(page):
        return meta["url"].startswith(page["url"])

    header_links = "\n".join(
        '            <a href="%s"%s>%s</a>' % (
            page["url"], ' class="is-current"' if current(page) else "", page["label"])
        for page in COMPANY_PAGES if page.get("header")
    )
    sheet_links = "\n".join(
        '            <a class="sheet__link" href="%s">%s</a>' % (page["url"], page["label"])
        for page in COMPANY_PAGES
    )
    return NAV.format(
        logo=indent(LOGO, "            "),
        product=product,
        cta=cta,
        panel_rows=indent(rows, "                    "),
        sheet_rows=indent(rows, "            "),
        apps_current=" is-current" if app_id else "",
        header_links=header_links,
        sheet_links=sheet_links,
        site=SITE,
    )


# --------------------------------------------------------------------------
# The footer
# --------------------------------------------------------------------------

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
{company_links}
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


def build_footer(meta):
    item = '                        <li><a href="%s">%s</a></li>'
    return FOOTER.format(
        logo=indent(LOGO, "                    "),
        tagline=TAGLINE,
        company=COMPANY,
        app_links="\n".join(item % (app["url"], app["name"]) for app in APPS),
        company_links="\n".join(item % (page["url"], page.get("footer", page["label"]))
                                for page in COMPANY_PAGES),
    )


# --------------------------------------------------------------------------
# The manual: its sidebar, and previous and next at the foot of a page
# --------------------------------------------------------------------------

DOCSNAV = """<nav class="docside" data-docside aria-label="Manual">
    <button class="docside__btn" type="button" aria-expanded="false" aria-controls="docside-list">
        Manual<span class="chev" aria-hidden="true"></span>
    </button>
    <div class="docside__list" id="docside-list">
{rows}
    </div>
</nav>"""


def build_docsnav(meta):
    """The list of pages, grouped. Each group's links are wrapped so the rail
    down their left is one border rather than one per link."""
    app = APP[meta["app"]]
    rows, group = [], []

    def flush():
        if group:
            rows.append('        <div class="docside__items">')
            rows.extend(group)
            rows.append("        </div>")
            group.clear()

    for page in MANUALS[app["id"]]["pages"]:
        if "group" in page:
            flush()
            rows.append('        <p class="docside__group">%s</p>' % page["group"])
        url = manual_root(app) + page["slug"]
        current = ' aria-current="page"' if url == meta["url"] else ""
        group.append('            <a href="%s"%s>%s</a>' % (url, current, page["title"]))
    flush()
    return DOCSNAV.format(rows="\n".join(rows))


DOCFOOT = """    <a class="docfoot{modifier}" href="{url}">
        <span>{kind}</span><b>{title}</b>
    </a>"""


def build_docsfeet(meta):
    """Previous and next, taken from the order of the manual. Adding a page in
    the middle of the book re-links its neighbours by itself."""
    app = APP[meta["app"]]
    pages, index = MANUALS[app["id"]]["pages"], meta["index"]
    feet = []
    if index > 0:
        page = pages[index - 1]
        feet.append(DOCFOOT.format(modifier="", kind="Previous",
                                   url=manual_root(app) + page["slug"], title=page["title"]))
    if index < len(pages) - 1:
        page = pages[index + 1]
        feet.append(DOCFOOT.format(modifier=" docfoot--next", kind="Next",
                                   url=manual_root(app) + page["slug"], title=page["title"]))
    return '<nav class="docfeet" aria-label="Manual pages">\n%s\n</nav>' % "\n".join(feet)


# --------------------------------------------------------------------------
# Layouts: what the page's own content sits inside
# --------------------------------------------------------------------------

def docs_open(meta):
    page = MANUALS[meta["app"]]["pages"][meta["index"]]
    return ('<main id="main">\n<div class="wrap wrap--wide docs">\n\n%s\n\n'
            '<article class="doc">\n'
            '    <span class="doc__kind">%s</span>\n'
            '    <h1>%s</h1>') % (build_docsnav(meta), meta["group"], page["title"])


def docs_close(meta):
    # The "On this page" column is filled in by site.js from the page's own
    # <h2>s, so it can never disagree with them.
    return ('%s\n</article>\n\n'
            '<aside class="docmap" data-docmap hidden>\n'
            '    <p class="docmap__head">On this page</p>\n'
            '</aside>\n\n'
            '</div>\n</main>') % build_docsfeet(meta)


# layout → (opening, closing). The page's own content goes between the two.
LAYOUTS = {
    # The home page and the app pages: sections, each with its own wrap.
    "page": (lambda meta: '<main id="main">',
             lambda meta: '</main>'),
    # The company pages: one column of running text.
    "prose": (lambda meta: '<main id="main" class="page">\n    <div class="wrap prose">',
              lambda meta: '    </div>\n</main>'),
    # A page of a manual: the sidebar, the page, and "On this page".
    "docs": (docs_open, docs_close),
}


def build_top(meta, args):
    body = '<body data-app="%s">' % meta["app"] if meta.get("app") else "<body>"
    opening, _ = LAYOUTS[meta.get("layout", "page")]
    return "\n\n".join([
        "<head>\n%s\n</head>" % build_head(meta),
        body + '\n<a class="skip-link" href="#main">Skip to content</a>',
        build_nav(meta),
        opening(meta),
    ])


def build_bottom(meta, args):
    _, closing = LAYOUTS[meta.get("layout", "page")]
    return "\n\n".join([
        closing(meta),
        build_footer(meta),
        '<script src="/assets/js/site.js" defer></script>\n</body>',
    ])


# --------------------------------------------------------------------------
# Components a page can ask for in its own content
# --------------------------------------------------------------------------

def build_store_badge(meta, args):
    """Apple's Mac App Store badge, linked to the app's listing. The page's
    own app, or the app named in the marker."""
    app = APP[args[0] if args else meta["app"]]
    return ('<a class="store-badge" href="%s" target="_blank" rel="noopener">\n'
            '    <img src="/assets/img/badges/download-on-the-mac-app-store.svg"\n'
            '         alt="Download on the Mac App Store" width="156" height="40">\n'
            '</a>') % app["store"]


APPCARD = """<a class="appcard reveal" href="{url}" data-app="{id}"{delay}>
    <div class="appcard__top">
{app_icon}
        <div>
            <div class="appcard__name">{name}</div>
            <div class="appcard__state"><em class="dot dot--{state}"></em>{state_label}</div>
        </div>
    </div>
    <p class="appcard__body">
{card_text}
    </p>
    <span class="appcard__go">
        Look at {name}
        {arrow}
    </span>
</a>"""


def build_app_cards(meta, args):
    """A card for every app, for the home page. Each card arrives 80ms after
    the one before it."""
    return "\n\n".join(
        APPCARD.format(delay=' style="--delay: %dms"' % (80 * i) if i else "",
                       app_icon=indent(app_icon(app, "appicon appcard__icon", 46), "        "),
                       card_text=wrap(app["card"], "        "),
                       arrow=icon("arrow"),
                       **app)
        for i, app in enumerate(APPS)
    )


DOCCARD = """<a class="card" href="{url}">
    <h4>{title}</h4>
    <p>{blurb}</p>
</a>"""


def build_doc_cards(meta, args):
    """A card for each named page of the page's app's manual, in the order
    the marker names them. The title and the text are the page's own, from
    MANUALS."""
    app = APP[meta["app"]]
    pages = {page["slug"]: page for page in MANUALS[app["id"]]["pages"]}
    cards = []
    for slug in args:
        if slug not in pages:
            raise SystemExit("doc-cards: %s has no page %s" % (app["name"], slug))
        page = pages[slug]
        cards.append(DOCCARD.format(url=manual_root(app) + slug, title=page["title"],
                                    blurb=wrap(page["blurb"], "   ").lstrip()))
    return "\n".join(cards)


# Every region a page may hold. "top" and "bottom" must be on every page,
# once; the rest wherever the page wants them.
COMPONENTS = {
    "top": build_top,
    "bottom": build_bottom,
    "store-badge": build_store_badge,
    "app-cards": build_app_cards,
    "doc-cards": build_doc_cards,
}

REGION = re.compile(
    r"^(?P<indent>[ \t]*)<!-- chrome:(?P<name>[\w-]+)(?P<args>(?: [^>]*?)?) -->\n"
    r".*?"
    r"^(?P=indent)<!-- /chrome:(?P=name) -->",
    re.DOTALL | re.MULTILINE,
)


def rewrite_page(text, meta):
    found = []

    def replace(match):
        name, args = match.group("name"), match.group("args")
        if name not in COMPONENTS:
            raise SystemExit("%s: there is no component called %s" % (meta["url"], name))
        found.append(name)
        prefix = match.group("indent")
        block = COMPONENTS[name](meta, args.split())
        return "%s<!-- chrome:%s%s -->\n%s\n%s<!-- /chrome:%s -->" % (
            prefix, name, args, indent(block, prefix), prefix, name)

    text = REGION.sub(replace, text)
    for name in ("top", "bottom"):
        if found.count(name) != 1:
            raise SystemExit("%s: needs one chrome:%s region, has %d"
                             % (meta["url"], name, found.count(name)))
    return text


# --------------------------------------------------------------------------
# The stylesheets: dark colours for a visitor whose system is dark
# --------------------------------------------------------------------------

# A page is dark in two cases: the visitor chose dark with the button in the
# header, or the visitor chose nothing and the system is dark. CSS cannot say
# "this selector, or that media query" in one rule, so each dark rule needs a
# second copy inside a media query.
#
# Only the first copy is written by hand. A region right after it holds the
# second, and this script writes it:
#
#     :root[data-appearance="dark"] [data-app="tracktiv"] { --accent: #4fa3ff; }
#     /* chrome:dark-system */
#     /* /chrome:dark-system */
#
# The region copies every dark rule between the region before it and itself.
# A dark rule that sets colour tokens and has no region after it is an error,
# because on a dark system it would silently not apply.

STYLESHEETS = ["assets/css/site.css", "assets/css/themes.css"]

DARK = ':root[data-appearance="dark"]'
SYSTEM_DARK = ':root:not([data-appearance="light"])'

CSS_REGION = re.compile(r"^/\* chrome:dark-system \*/\n.*?^/\* /chrome:dark-system \*/",
                        re.DOTALL | re.MULTILINE)
DARK_RULE = re.compile(r"^(%s[^{]*)\{([^}]*)\}" % re.escape(DARK), re.MULTILINE)


def dark_token_rules(css):
    """The dark rules that set custom properties. A dark rule that only shows
    or hides something, like the appearance button's moon, needs no copy: it
    is about the button, and the button is only ever explicit."""
    return [(selector, body) for selector, body in DARK_RULE.findall(css) if "--" in body]


def build_dark_system(rules):
    lines = ["@media (prefers-color-scheme: dark) {"]
    for number, (selector, body) in enumerate(rules):
        if number:
            lines.append("")
        lines.append("    %s {" % selector.strip().replace(DARK, SYSTEM_DARK))
        lines.extend(("    " + line).rstrip() for line in body.strip("\n").split("\n"))
        lines.append("    }")
    lines.append("}")
    return "\n".join(lines)


def check_comments(css, path):
    """A "/*" inside a comment is a mistake that is easy to make and hard to
    see. The first "*/" after it closes the comment early. The text left over
    then spoils the next rule, and the browser drops that rule without a
    word. This once dropped a whole @font-face."""
    for match in re.finditer(r"/\*(.*?)\*/", css, re.DOTALL):
        if "/*" in match.group(1):
            raise SystemExit("%s:%d: a comment contains /*"
                             % (path, css.count("\n", 0, match.start()) + 1))


def rewrite_css(text, path):
    check_comments(text, path)
    parts, start = [], 0
    for match in CSS_REGION.finditer(text):
        before = text[start:match.start()]
        rules = dark_token_rules(before)
        if not rules:
            raise SystemExit("%s: a chrome:dark-system region with no dark rule above it" % path)
        parts.append(before)
        parts.append("/* chrome:dark-system */\n%s\n/* /chrome:dark-system */"
                     % build_dark_system(rules))
        start = match.end()
    rest = text[start:]
    for selector, _ in dark_token_rules(rest):
        raise SystemExit("%s: %s needs a /* chrome:dark-system */ region after it"
                         % (path, selector.strip()))
    parts.append(rest)
    return "".join(parts)


# --------------------------------------------------------------------------
# sitemap.xml
# --------------------------------------------------------------------------

def build_sitemap():
    """Every page, except the ones marked noindex. No <lastmod>: a date written
    by hand goes stale, and search engines ignore one they cannot trust."""
    rows = "\n".join(
        "    <url>\n        <loc>%s%s</loc>\n    </url>" % (ORIGIN, meta["url"])
        for meta in all_pages().values() if not meta.get("noindex")
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n'
            % rows)


# --------------------------------------------------------------------------

def main():
    check = "--check" in sys.argv
    outputs = {}
    for path, meta in all_pages().items():
        file = ROOT / path
        if not file.exists():
            raise SystemExit("missing page: %s" % path)
        outputs[path] = rewrite_page(file.read_text(), meta)
    for path in STYLESHEETS:
        outputs[path] = rewrite_css((ROOT / path).read_text(), path)
    outputs["sitemap.xml"] = build_sitemap()

    stale = []
    for path, after in outputs.items():
        file = ROOT / path
        if file.exists() and file.read_text() == after:
            continue
        stale.append(path)
        if not check:
            file.write_text(after)
            print("updated %s" % path)
    if check:
        if stale:
            print("out of date: %s" % ", ".join(stale))
            return 1
        print("everything is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
