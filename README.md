# devnest.sk

The DevNest s.r.o. website: the company, and the two macOS apps it makes —
Tracktiv and AssetScout.

Everything in this repository is the site. There is **no build step, no bundler
and no framework** — plain HTML, two stylesheets and one script. Any static host
serves the folder as it is.

## Layout

```
index.html              The company: who we are, both apps, how we work
apps/tracktiv/          Tracktiv, not finished yet — a short teaser for now
apps/assetscout/        AssetScout, the current product
apps/assetscout/docs/   Its manual — 22 pages, generated skeleton, hand-written prose
company/                DevNest s.r.o. and the imprint
support/                How to reach us and how to report a bug
privacy/                What the apps store, and what this site measures
404.html
assets/css/site.css     Tokens, the header, the sections, the components
assets/css/themes.css   Per-app colour skins, and the drawn scenes
assets/js/site.js       Appearance switch, reveals, menus, parallax, counters, drift
assets/img/             App icons and screenshots
assets/img/icons.svg    Every icon used inside the text, drawn once
assets/fonts/           Instrument Sans and IBM Plex Mono, with their licences
tools/chrome.py         Writes every part that repeats: see "One place for everything"
tools/shot.swift        Photographs a section of the site without a browser window
tools/og.swift          Redraws assets/img/brand/og.png, the link preview card
drafts/                 Written but not shown yet: the full Tracktiv page. Not uploaded
```

## Looking at it locally

Asset paths are absolute (`/assets/…`), so the site has to be **served**, not
opened from the Finder:

```bash
python3 -m http.server 8765 --directory .
```

Then open <http://localhost:8765>. `.claude/launch.json` starts the same server
from an editor that reads it.

## Deploying

The site runs on Cloudflare Pages, built from this repo's `main` branch.
Cloudflare has no way to ignore files, so `tools/build-dist.sh` copies only
the public pages and assets into `dist/` — `drafts/`, `tools/`, `README.md`,
`CLAUDE.md` and `.claude/` are left out. Pages runs it as the build command
and serves `dist` as the output directory.

## One place for everything that repeats

Every part that appears on more than one page is written once, and changing it
there changes it on every page. Most of it lives in `tools/chrome.py`, which
writes it into the files between comment markers. The files stay complete, so
the host still serves them as they are.

```bash
python3 tools/chrome.py          # rewrite every file
python3 tools/chrome.py --check  # exit 1 if a file is out of date
```

| To change …                                             | edit …                                   |
| ------------------------------------------------------- | ---------------------------------------- |
| `<head>`, the header, the footer                        | `HEAD`, `NAV`, `FOOTER` in `chrome.py`   |
| an app's name, icon, dot, menu line or home-page card   | `APPS` in `chrome.py`                    |
| an app's App Store link, on every badge                 | `store` in `APPS`                        |
| the company links in the header, the sheet, the footer  | `COMPANY_PAGES` in `chrome.py`           |
| a manual's pages, titles, groups and order              | `MANUALS` in `chrome.py`                 |
| a page's title and description                          | `PAGES` (a manual page: `MANUALS`)       |
| how a component looks                                   | `assets/css/site.css`                    |
| an app's colours, the drawn scenes                      | `assets/css/themes.css`                  |
| an icon                                                 | `assets/img/icons.svg`                   |
| what a component does                                   | `assets/js/site.js`                      |

Every page has two regions, one at each end. Everything between them is the
page's own and is never touched:

```html
<!doctype html>
<html lang="en">
<!-- chrome:top -->
<!-- /chrome:top -->
    … the page's own content …
<!-- chrome:bottom -->
<!-- /chrome:bottom -->
</html>
```

`top` holds `<head>`, the `<body>` tag with the app's skin, the header, and the
opening of the page's layout. `bottom` closes the layout and holds the footer.
The layout is `page` (the home page and the app pages), `prose` (the company
pages) or `docs` (a page of a manual).

A page can also ask for a component inside its own content. The marker must
start its line, and the script fills it in:

```html
<!-- chrome:store-badge -->             <!-- /chrome:store-badge -->
<!-- chrome:app-cards -->               <!-- /chrome:app-cards -->
```

`store-badge` is Apple's badge linked to the page's app, or to the app the
marker names. `app-cards` is a card per app.

An icon is pointed at, not copied. Its size and line weight come from the CSS
of the place it sits in:

```html
<svg aria-hidden="true"><use href="/assets/img/icons.svg#arrow"></use></svg>
```

## Adding a page

1. Create the file with the two region pairs from above, and the page's own
   content between them.
2. Add it to `PAGES` in `tools/chrome.py` with its URL, title and description,
   `"layout"` if it is not a `page`, and `"app": "<id>"` if it belongs to one of
   the apps. That skins it and puts the app's name beside DevNest in the header.
3. Run `python3 tools/chrome.py`. That also puts the page in `sitemap.xml`.

A page of a **manual** is added to `MANUALS` instead. That one entry gives it its
title, its description, its place in the sidebar, the group label above its
title and its previous and next links. Inserting a page in the middle of the
book re-links its neighbours by itself. The page file holds only what comes
after the `<h1>`: the lead paragraph and the text. The "On this page" column is
built by `site.js` from the page's own `<h2>`s and needs no markup at all.

A **new app's manual** is a new entry in `MANUALS`, keyed by the app's id. Its
pages live under the app's URL + `docs/`, and the footer links to it from every
page of the site. The app's page links to it itself: in the hero and in its own
documentation section. `"nav_cta": True` is separate from the manual; it repeats
the page's store badge in the header once the page's own has scrolled away.

## Dark colours

Write a dark value once, in the `:root[data-appearance="dark"]` rule. That rule
serves a visitor who picked dark with the button in the header. A visitor who
picked nothing, on a dark system, needs the same values inside a
`prefers-color-scheme` media query. A CSS rule cannot say both at once, so
`tools/chrome.py` writes that second copy into the `/* chrome:dark-system */`
region after the rule. A new app's skin needs such a region after its dark
rule; the script stops with an error if it is missing.

## Screenshots

Every screenshot is a real window from a real Mac, captured at Retina scale, so
its pixels are twice the points it was drawn at. **A screenshot must be shown at
half its pixel width or the app's own type goes soft** — that is what `--w` on
the wrapper is for:

```html
<div class="shot shot--detail" style="--w: 279px">   <!-- the image is 558px wide -->
```

**A screenshot is never put in a frame.** It carries its own macOS shadow on a
transparent ground and sits straight on the page — no border, no mat, no second
shadow. That is what `shot--free` is for:

```html
<div class="shot shot--free" style="--w: 1095px">
```

Capture whole windows **with the shadow still round them**, the way
`screencapture -w` leaves it. A piece cut out of a window has no shadow of its
own, so give it one when you crop; `tools/` has no script for this, but the
recipe is a blurred copy of the crop's own alpha, offset downwards — a wide soft
layer and a tight dark one.

`shot--window`, `shot--detail` and the `.mat` behind them are the older way, for
captures taken without a shadow. Tracktiv still uses them, which is also why the
mat stays light in both appearances: those windows were photographed light.

**Every screenshot exists twice**, light and dark, and the page shows the one
that matches. It is a `<picture>`, so the browser fetches one file and not both:

```html
<picture>
    <source data-dark-source media="(prefers-color-scheme: dark)"
            srcset="/assets/img/apps/assetscout/window-dark.webp">
    <img src="/assets/img/apps/assetscout/window.webp" alt="…"
         width="2190" height="1730">
</picture>
```

The media query knows about the system setting and nothing about the button in
the header, so `site.js` rewrites it — `all` or `not all` — when the visitor
overrules the system. `data-dark-source` is how it finds them.

A crop must be **the same rectangle in both captures**, or the figure jumps when
the appearance changes. Cut them in one pass, from one script.

To photograph a section of the site itself, without a browser window in the way:

```bash
swiftc -O tools/shot.swift -o /tmp/shot
/tmp/shot http://127.0.0.1:8765/apps/tracktiv/ 1400 950 /tmp/out.png "#projects" dark
```

The link preview, `assets/img/brand/og.png`, is drawn from the same logo and the
same colours:

```bash
swiftc -O tools/og.swift -o /tmp/og && /tmp/og assets/img/brand/og.png
```

## The design, in short

- **The frame is DevNest, the colour is the app.** `site.css` owns the header,
  the spacing and every component; `themes.css` only re-declares colour tokens
  per app. The header is therefore identical on every page, in every skin.
- **Type:** Instrument Sans for anything readable, IBM Plex Mono for anything
  that is data — a time, a label, a caption. Numbers are tabular throughout.
- **Appearance:** the page follows the visitor's system setting until they pick a
  side with the button in the header, and the choice is remembered.
- **Motion** is scroll-triggered: blocks fade up (`.reveal`), a list arrives one
  item at a time (`.stagger`), a screenshot comes up from further away
  (`.reveal--rise`) and drifts a little as it goes by (`.settle`), an underline
  draws itself (`.underline`), the day strip wipes in, the ring fills and the
  numbers count. All of it stops under `prefers-reduced-motion`.

## Before it goes live

Four things are still open:

1. **The TestFlight link.** The beta buttons on the full Tracktiv page point at
   `mailto:support@devnest.sk`. Swap in the public TestFlight URL — it appears
   twice, in the hero and in `#beta`. That page waits in `drafts/` for now.
2. **The screenshots contain real data.** The older Tracktiv captures, used by
   the page in `drafts/`, show tracked time with real client and project names
   in it. The teaser's `window.webp` pair names only our own projects. AssetScout's
   captures were retaken on sample media, and the inspector prints the path
   under a made-up `/Users/johndoe`. Check both sets before publishing, and
   retake anything that should not be public.
3. **The App Store link.** Every AssetScout badge points at
   `https://apps.apple.com/app/assetscout`, which is a guess. Swap in the real
   product URL: it is `store` in `APPS` in `tools/chrome.py`, marked `TODO`.
   Then run the script.
4. **Four figures the manual has no picture for**: the scan control while a scan
   runs, the two settings panes, and the *Show Skipped Files* sheet. Each needs a
   light and a dark capture of the same window.

The privacy policy describes what the apps and this site actually do, but it has
not been read by a lawyer.

## Deploying

Upload the contents of this folder to the web root, except `drafts/`. Nothing needs PHP, a database
or a runtime. On Cloudflare Pages: framework preset *None*, no build command,
build output directory `/`.

## License

© DevNest s.r.o. All rights reserved.
