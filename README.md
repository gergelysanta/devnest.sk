# devnest.sk

The DevNest s.r.o. website: the company, and the two macOS apps it makes —
Tracktiv and AssetScout.

Everything in this repository is the site. There is **no build step, no bundler
and no framework** — plain HTML, two stylesheets and one script. Any static host
serves the folder as it is.

## Layout

```
index.html              The company: who we are, both apps, how we work
apps/tracktiv/          Tracktiv, the current product — the longest page here
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
assets/fonts/           Instrument Sans and IBM Plex Mono, with their licences
tools/chrome.py         Keeps the header, the footer and the manual's sidebar in step
tools/shot.swift        Photographs a section of the site without a browser window
tools/og.swift          Redraws assets/img/brand/og.png, the link preview card
```

## Looking at it locally

Asset paths are absolute (`/assets/…`), so the site has to be **served**, not
opened from the Finder:

```bash
python3 -m http.server 8765 --directory .
```

Then open <http://localhost:8765>. `.claude/launch.json` starts the same server
from an editor that reads it.

## Editing the header or the footer

They exist once, in `tools/chrome.py`, and are written into every page between
comment markers:

```html
<!-- chrome:nav -->  … generated, do not edit by hand …  <!-- /chrome:nav -->
```

Change the template (or add a page to `PAGES`), then:

```bash
python3 tools/chrome.py          # rewrite every page
python3 tools/chrome.py --check  # exit 1 if a page is out of date
```

Everything outside the markers is the page's own and is never touched.

## Adding a page

1. Copy an existing page and keep its marker pairs.
2. Add it to `PAGES` in `tools/chrome.py` with its URL, title and description —
   and `"app": "<id>"` if it belongs to one of the apps, which skins it and puts
   the app's name beside DevNest in the header.
3. Run `python3 tools/chrome.py`.
4. Add it to `sitemap.xml`.

A page of a **manual** is added to `DOCS` instead. That one entry gives it its
metadata in `PAGES`, its place in the sidebar (`<!-- chrome:docsnav -->`) and its
previous/next links (`<!-- chrome:docsfeet -->`), so inserting a page in the
middle of the book re-links its neighbours by itself. The "On this page" column
is built by `site.js` from the page's own `<h2>`s and needs no markup at all.

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
         width="2190" height="1728">
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

1. **The TestFlight link.** The beta buttons on the Tracktiv page point at
   `mailto:support@devnest.sk`. Swap in the public TestFlight URL — it appears
   twice, in the hero and in `#beta`.
2. **The screenshots contain real data.** Tracktiv's show tracked time, with
   real client and project names in it. AssetScout's inspector figure prints the
   file path of the selected picture, and that path is a folder inside the
   developer's home directory. Check both sets before publishing, and retake
   anything that should not be public.
3. **The App Store link.** Both buttons on the AssetScout page point at
   `https://apps.apple.com/app/assetscout`, which is a guess. Swap in the real
   product URL — it is marked `TODO` in the HTML, and it appears twice.
4. **Four figures the manual has no picture for**: the scan control while a scan
   runs, the two settings panes, and the *Show Skipped Files* sheet. Each needs a
   light and a dark capture of the same window.

The privacy policy describes what the apps and this site actually do, but it has
not been read by a lawyer.

## Deploying

Upload the contents of this folder to the web root. Nothing needs PHP, a database
or a runtime. On Cloudflare Pages: framework preset *None*, no build command,
build output directory `/`.

## License

© DevNest s.r.o. All rights reserved.
