# Drafts

Content that is written but not shown yet. Nothing in `tools/chrome.py` points
here, no page links here, and the folder is not uploaded (see "Deploying" in the
main README).

## Tracktiv

Tracktiv is not finished, so its page is only a teaser for now. What it
replaced waits here:

- `tracktiv/index.html` is the full product page. Its chrome regions are from
  the day it was moved here, so they are out of date.
- `home-tracktiv-section.html` is the section about Tracktiv that sat on the
  home page, right after the app cards and before "How we work".

To bring them back:

1. Move `tracktiv/index.html` back to `apps/tracktiv/index.html`, over the
   teaser.
2. Paste `home-tracktiv-section.html` back into `index.html`, after the
   `#apps` section.
3. In `tools/chrome.py`, set Tracktiv's `state`, `state_label`, `summary` and
   `card` in `APPS`, and its `title` and `description` in `PAGES`, back to the
   beta texts. `git log -p tools/chrome.py` has the old wording.
4. Run `python3 tools/chrome.py`.
