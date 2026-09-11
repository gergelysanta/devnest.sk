/* ==========================================================================
   devnest.sk
   Plain ES2019, no framework and no build step. A handful of small jobs:
   the appearance switch, the header, the apps menu, the manual's sidebar and
   its "On this page", the scroll reveals, the numbers that count up, the
   pointer parallax on the home stage, and the drift of a figure as it goes
   by.
   ========================================================================== */

(function () {
    "use strict";

    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

    function each(list, fn) { Array.prototype.forEach.call(list, fn); }

    /* ----------------------------------------------------------------------
       Helpers the jobs below share
       ---------------------------------------------------------------------- */

    /* Runs fn now, and again at most once per frame while the page scrolls.
       With withResize it also runs when the window changes size. */
    function onScroll(fn, withResize) {
        var queued = false;
        window.addEventListener("scroll", function () {
            if (queued) return;
            queued = true;
            window.requestAnimationFrame(function () {
                queued = false;
                fn();
            });
        }, { passive: true });
        if (withResize) window.addEventListener("resize", fn);
        fn();
    }

    /* Calls fn(element) once for each element, the first time it comes into
       view. The caller checks that IntersectionObserver exists. */
    function onFirstSight(items, options, fn) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                observer.unobserve(entry.target);
                fn(entry.target);
            });
        }, options);
        each(items, function (el) { observer.observe(el); });
    }

    /* Opens or closes a menu, a sheet or a list: the class is for the CSS,
       and aria-expanded tells a screen reader what the button did. */
    function setOpen(box, button, state) {
        box.classList.toggle("is-open", state);
        button.setAttribute("aria-expanded", state ? "true" : "false");
    }

    /* Calls write(element, box, viewportHeight) for every element of the
       selector that is on screen or near it, as the page scrolls. Both kinds
       of drift at the end of this file are built on it. */
    function driftEach(selector, write) {
        var items = document.querySelectorAll(selector);
        if (!items.length || reduced) return;

        onScroll(function () {
            var height = window.innerHeight;
            each(items, function (el) {
                var box = el.getBoundingClientRect();
                if (box.bottom < -200 || box.top > height + 200) return;
                write(el, box, height);
            });
        }, true);
    }

    /* ----------------------------------------------------------------------
       Appearance

       Three states cycle on click: light, dark, system. System is the
       absence of the data-appearance attribute — the page then follows
       prefers-color-scheme, same as a first-time visitor. The first paint
       is already handled by the inline script in <head>; this only wires
       the button and remembers the answer.
       ---------------------------------------------------------------------- */

    function setupAppearance() {
        var root = document.documentElement;
        var buttons = document.querySelectorAll("[data-appearance-toggle]");

        function current() {
            var set = root.getAttribute("data-appearance");
            return set === "light" || set === "dark" ? set : "system";
        }

        function next(state) {
            if (state === "light") return "dark";
            if (state === "dark") return "system";
            return "light";
        }

        function label() {
            var text = "Switch to " + next(current()) + " appearance";
            each(buttons, function (b) {
                b.setAttribute("aria-label", text);
                b.setAttribute("title", text);
            });
        }

        /* The screenshots come in two versions, and which one the browser
           fetches is decided by the media query on the <source> — which knows
           about the system setting and nothing about this button. When the
           visitor overrules the system, the query is rewritten to a plain yes
           or no; picking "system" again hands it back.

           Only the override costs a second fetch, and only for the pictures
           already on screen. Leaving both files in the page instead would cost
           it every time, for everyone. */
        function retuneFigures() {
            var state = current();
            var query = state === "system" ? "(prefers-color-scheme: dark)"
                      : state === "dark"   ? "all"
                      :                      "not all";
            each(document.querySelectorAll("[data-dark-source]"), function (source) {
                source.media = query;
            });
        }

        each(buttons, function (b) {
            b.addEventListener("click", function () {
                var state = next(current());
                if (state === "system") {
                    root.removeAttribute("data-appearance");
                    try { localStorage.removeItem("appearance"); } catch (e) { /* private browsing */ }
                } else {
                    root.setAttribute("data-appearance", state);
                    try { localStorage.setItem("appearance", state); } catch (e) { /* private browsing */ }
                }
                label();
                retuneFigures();
            });
        });

        label();
        if (current() !== "system") retuneFigures();
    }

    /* ----------------------------------------------------------------------
       Header: a hairline once the page has moved
       ---------------------------------------------------------------------- */

    function setupNav() {
        var nav = document.querySelector("[data-nav]");
        if (!nav) return;

        onScroll(function () {
            nav.classList.toggle("is-stuck", window.scrollY > 6);
        });
    }

    /* ----------------------------------------------------------------------
       Header: the page's own buttons, once they have scrolled away

       A product page repeats its store badge and its second button in the
       header (NAV_CTA in tools/chrome.py). The copy shows only when no store
       badge of the page itself is on screen, and the first one is above the
       window. Apple asks for one badge per layout, so the header copy steps
       aside again when the closing section's badge comes into view.
       ---------------------------------------------------------------------- */

    function setupNavCta() {
        var nav = document.querySelector("[data-nav]");
        var cta = document.querySelector("[data-nav-cta]");
        if (!nav || !cta || !("IntersectionObserver" in window)) return;

        var badges = Array.prototype.filter.call(
            document.querySelectorAll(".store-badge"),
            function (badge) { return !cta.contains(badge); }
        );
        if (!badges.length) return;

        var visible = new Set();
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) visible.add(entry.target);
                else visible.delete(entry.target);
            });
            var past = badges[0].getBoundingClientRect().bottom < nav.offsetHeight;
            nav.classList.toggle("has-cta", visible.size === 0 && past);
            /* The top margin is the header's height, so a badge that has gone
               under the header already counts as off screen. */
        }, { rootMargin: "-" + nav.offsetHeight + "px 0px 0px 0px", threshold: 0 });

        badges.forEach(function (badge) { observer.observe(badge); });
    }

    /* ----------------------------------------------------------------------
       The apps menu

       Opens on hover for a pointer and on click for everything else, and the
       close-on-hover-out is delayed a little so the diagonal move from the
       button to the third row does not lose the menu on the way.
       ---------------------------------------------------------------------- */

    function setupMenu() {
        var menu = document.querySelector("[data-menu]");
        if (!menu) return;

        var button = menu.querySelector(".menu__btn");
        var panel = menu.querySelector(".menu__panel");
        var timer = null;

        /* The panel is marked hidden in the markup so that it stays closed
           without JavaScript. From here on it is CSS that opens and closes it. */
        panel.hidden = false;

        function open(state) {
            window.clearTimeout(timer);
            setOpen(menu, button, state);
        }

        button.addEventListener("click", function (e) {
            e.preventDefault();
            open(!menu.classList.contains("is-open"));
        });

        if (finePointer) {
            menu.addEventListener("mouseenter", function () { open(true); });
            menu.addEventListener("mouseleave", function () {
                window.clearTimeout(timer);
                timer = window.setTimeout(function () { open(false); }, 180);
            });
        }

        document.addEventListener("click", function (e) {
            if (!menu.contains(e.target)) open(false);
        });
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") { open(false); button.blur(); }
        });
        menu.addEventListener("focusout", function () {
            window.setTimeout(function () {
                if (!menu.contains(document.activeElement)) open(false);
            }, 0);
        });
    }

    /* ----------------------------------------------------------------------
       The mobile sheet
       ---------------------------------------------------------------------- */

    function setupSheet() {
        var button = document.querySelector("[data-nav-toggle]");
        var sheet = document.querySelector("[data-nav-sheet]");
        if (!button || !sheet) return;

        sheet.hidden = false;

        function open(state) {
            setOpen(sheet, button, state);
            document.body.style.overflow = state ? "hidden" : "";
        }

        button.addEventListener("click", function () {
            open(!sheet.classList.contains("is-open"));
        });
        each(sheet.querySelectorAll("a"), function (a) {
            a.addEventListener("click", function () { open(false); });
        });

        /* The sheet belongs to the narrow layout. Once the window is wide
           enough for the header's own links, the CSS hides the button, and an
           open sheet closes with it. Asking the button, instead of repeating
           the width of the CSS breakpoint here, keeps that width in one place. */
        window.addEventListener("resize", function () {
            if (sheet.classList.contains("is-open") && getComputedStyle(button).display === "none") {
                open(false);
            }
        });
    }

    /* ----------------------------------------------------------------------
       The manual's list of pages

       Wide enough, the list is simply there and the button is not shown. On a
       narrow screen the button folds it away, and it starts folded — the page
       the reader came for should be the first thing under the header.
       ---------------------------------------------------------------------- */

    function setupDocnav() {
        var nav = document.querySelector("[data-docside]");
        if (!nav) return;

        var button = nav.querySelector(".docside__btn");
        if (!button) return;

        button.addEventListener("click", function () {
            setOpen(nav, button, !nav.classList.contains("is-open"));
        });
    }

    /* ----------------------------------------------------------------------
       On this page

       The right-hand column of a manual page is built here rather than
       written into the markup, so it cannot disagree with the headings it
       lists. Every <h2> gets an id made from its text — unless it has one
       already, which is what a hand-written anchor is for — and the entry for
       the heading the reader is level with is marked.
       ---------------------------------------------------------------------- */

    function setupDocmap() {
        var map = document.querySelector("[data-docmap]");
        var article = document.querySelector(".doc");
        if (!map || !article) return;

        var headings = article.querySelectorAll("h2");
        if (headings.length < 2) return;   /* a list of one is not a list */

        var list = document.createElement("ul");
        var links = [];

        each(headings, function (heading) {
            if (!heading.id) {
                heading.id = heading.textContent
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, "-")
                    .replace(/^-|-$/g, "");
            }
            var item = document.createElement("li");
            var link = document.createElement("a");
            link.href = "#" + heading.id;
            link.textContent = heading.textContent;
            item.appendChild(link);
            list.appendChild(item);
            links.push(link);
        });

        map.appendChild(list);
        map.hidden = false;

        onScroll(function () {
            /* The heading in force is the last one that has gone past the top
               of the reading area, not the one nearest the middle: that is the
               one whose text the reader is under. */
            var line = 120;
            var here = 0;
            each(headings, function (heading, i) {
                if (heading.getBoundingClientRect().top <= line) here = i;
            });
            links.forEach(function (link, i) {
                link.classList.toggle("is-here", i === here);
            });
        });
    }

    /* ----------------------------------------------------------------------
       Scroll reveals

       One trigger drives three things: the fade-up of a block, the fill of a
       ring, and the wipe of a screenshot.
       ---------------------------------------------------------------------- */

    function setupReveal() {
        /* A staggered list numbers its own children, so the markup only has
           to say .stagger and the CSS reads the index out of --i. */
        each(document.querySelectorAll(".stagger"), function (list) {
            each(list.children, function (child, i) {
                child.style.setProperty("--i", String(i));
            });
        });

        var items = document.querySelectorAll(".reveal, .ring, .wipe, .stagger");
        if (!items.length) return;

        if (reduced || !("IntersectionObserver" in window)) {
            each(items, function (el) { el.classList.add("is-in"); });
            return;
        }

        /* threshold 0, not a fraction: the fraction is of the element's own
           area, so a block much taller than the window could never reach it
           and would stay invisible for good. The margin at the bottom is what
           keeps a sliver at the very edge from counting. */
        onFirstSight(items, { rootMargin: "0px 0px -8% 0px", threshold: 0 }, function (el) {
            el.classList.add("is-in");
        });
    }

    /* ----------------------------------------------------------------------
       Numbers that count up the first time they are seen

       The element carries the finished value in data-count; the text in the
       markup is the same number, so a visitor without JavaScript — or with
       reduced motion — reads it straight away.
       ---------------------------------------------------------------------- */

    function setupCounters() {
        var items = document.querySelectorAll("[data-count]");
        if (!items.length || reduced || !("IntersectionObserver" in window)) return;

        onFirstSight(items, { threshold: 0.6 }, function (el) {
            var to = parseFloat(el.getAttribute("data-count"));
            var decimals = (el.getAttribute("data-count").split(".")[1] || "").length;
            var started = null;
            var duration = 1100;

            function frame(now) {
                if (started === null) started = now;
                var t = Math.min(1, (now - started) / duration);
                var eased = 1 - Math.pow(1 - t, 3);
                el.textContent = (to * eased).toFixed(decimals);
                if (t < 1) window.requestAnimationFrame(frame);
            }
            el.textContent = (0).toFixed(decimals);
            window.requestAnimationFrame(frame);
        });
    }

    /* ----------------------------------------------------------------------
       Pointer parallax on the home stage

       --px and --py are a small offset in pixels, written on the stage and
       multiplied per window by its own --depth. Only the pointer drives it;
       on a touch screen the windows keep their idle float and nothing else.
       ---------------------------------------------------------------------- */

    function setupStage() {
        var stage = document.querySelector("[data-stage]");
        if (!stage || reduced || !finePointer) return;

        var range = 14;   /* pixels at the edge of the window, before --depth */
        var queued = false;
        var x = 0, y = 0;

        window.addEventListener("pointermove", function (e) {
            x = (e.clientX / window.innerWidth - 0.5) * -2 * range;
            y = (e.clientY / window.innerHeight - 0.5) * -2 * range;
            if (queued) return;
            queued = true;
            window.requestAnimationFrame(function () {
                queued = false;
                stage.style.setProperty("--px", x.toFixed(2));
                stage.style.setProperty("--py", y.toFixed(2));
            });
        }, { passive: true });
    }

    /* ----------------------------------------------------------------------
       Drift for anything marked .parallax

       The block moves against the scroll in proportion to how far its middle
       is from the middle of the window. data-speed is the proportion.
       ---------------------------------------------------------------------- */

    function setupParallax() {
        driftEach(".parallax", function (el, box, height) {
            var speed = parseFloat(el.getAttribute("data-speed") || "0.06");
            var shift = (box.top + box.height / 2 - height / 2) * -speed;
            el.style.setProperty("--shift", shift.toFixed(1) + "px");
        });
    }

    /* ----------------------------------------------------------------------
       Drift for anything marked .settle

       The same idea as .parallax, but measured against the element's own
       travel through the viewport rather than against the page, and clamped:
       a figure drifts at most data-range pixels from where it was laid out,
       so it never separates from the text it belongs to. The amount goes into
       --drift, in pixels, and the CSS decides what to do with it.
       ---------------------------------------------------------------------- */

    function setupSettle() {
        driftEach(".settle", function (el, box, height) {
            var range = parseFloat(el.getAttribute("data-range") || "18");
            /* -1 with the element below the fold, +1 once it is above it */
            var progress = 1 - 2 * ((box.top + box.height / 2) / height);
            el.style.setProperty("--drift", (progress * range).toFixed(1));
        });
    }

    /* ----------------------------------------------------------------------
       Footer year
       ---------------------------------------------------------------------- */

    function setupYear() {
        each(document.querySelectorAll("[data-year]"), function (el) {
            el.textContent = String(new Date().getFullYear());
        });
    }

    function boot() {
        setupAppearance();
        setupNav();
        setupNavCta();
        setupMenu();
        setupSheet();
        setupDocnav();
        setupDocmap();
        setupReveal();
        setupCounters();
        setupStage();
        setupParallax();
        setupSettle();
        setupYear();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
