# devnest.sk — notes for Claude

Static site, no build step. Plain HTML, `assets/css/site.css` +
`assets/css/themes.css`, `assets/js/site.js`. See README.md.

**Never hand-edit anything between `<!-- chrome:… -->` markers** (in HTML) or
`/* chrome:… */` markers (in CSS). `tools/chrome.py` writes them: `<head>`, the
header, the footer, each page's layout, the manual's sidebar, title and
previous/next links, the components (`store-badge`, `app-cards`, `doc-cards`),
the system-dark CSS copies and `sitemap.xml`. Change the templates or the data
(`APPS`, `COMPANY_PAGES`, `MANUALS`, `PAGES`) in that file, then run
`python3 tools/chrome.py`. `--check` must pass before a commit.

Anything that appears on more than one page is written once. Before adding
markup that repeats, make it a component in `chrome.py`, a class in the CSS or
an icon in `assets/img/icons.svg`. Icons are `<svg aria-hidden="true"><use
href="/assets/img/icons.svg#name"></use></svg>`; their size and stroke width are
set in the CSS of the place they sit in.

`site.css` must stay product-neutral: no rule in it may name an app. Per-app
colour and per-app scenes belong in `themes.css`.

Screenshots are Retina captures. Always set `--w` on the wrapper to **half** the
image's pixel width, and give `<img>` its real `width`/`height`.

Dark values are written once, under `:root[data-appearance="dark"]`. The
`prefers-color-scheme` copy after it is generated into a
`/* chrome:dark-system */` region; a new dark rule that sets tokens needs such a
region after it.
