import AppKit
import WebKit

// Renders the site off screen, so a section can be looked at without a browser
// window in the way.
//
//   swiftc -O shot.swift -o /tmp/shot
//   /tmp/shot http://127.0.0.1:8765/ 1400 900 out.png [scrollY|#anchor] [dark]
//
// The page is loaded, given a moment to lay out, scrolled, and photographed.

let arguments = CommandLine.arguments
guard arguments.count >= 5 else {
    print("usage: shot <url> <width> <height> <out.png> [scrollY|#anchor] [dark]")
    exit(64)
}

let url = URL(string: arguments[1])!
let width = Double(arguments[2])!
let height = Double(arguments[3])!
let output = arguments[4]
let position = arguments.count > 5 ? arguments[5] : "0"
let wantsDark = arguments.count > 6 && arguments[6] == "dark"

final class Shooter: NSObject, WKNavigationDelegate {
    let webView: WKWebView
    let output: String
    let position: String
    let wantsDark: Bool

    init(frame: NSRect, output: String, position: String, wantsDark: Bool) {
        let configuration = WKWebViewConfiguration()
        // No disk cache. The default store keeps one between runs, and
        // python's http.server sends no Cache-Control, so WebKit may reuse a
        // stylesheet from an earlier run and photograph the page as it was
        // before an edit. That happened with themes.css, in September 2026.
        configuration.websiteDataStore = .nonPersistent()
        self.webView = WKWebView(frame: frame, configuration: configuration)
        self.output = output
        self.position = position
        self.wantsDark = wantsDark
        super.init()
        webView.navigationDelegate = self
        webView.appearance = NSAppearance(named: wantsDark ? .darkAqua : .aqua)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // Fonts, images and the first reveal pass all need a moment.
        let settle = Double(ProcessInfo.processInfo.environment["SHOT_SETTLE"] ?? "") ?? 1.6
        DispatchQueue.main.asyncAfter(deadline: .now() + settle) { self.scrollThenShoot() }
    }

    private func scrollThenShoot() {
        // Two things have to be dealt with before the picture is taken.
        //
        // Reveals are driven by IntersectionObserver, and a jump past a section
        // means its observer never fires — so they are all switched on by hand.
        //
        // Switching the class on only starts a transition, and this web view
        // has no window on screen to drive one: the opacity stays where it
        // began and the section photographs blank. So the transitions are
        // turned off first, which also makes the picture the settled page
        // rather than whatever frame the animation happened to be on.
        let script: String
        if position.hasPrefix("#") {
            script = """
            var settle = document.createElement('style');
            settle.textContent = '*,*::before,*::after{transition:none !important;animation:none !important}';
            document.head.appendChild(settle);
            document.querySelectorAll('.reveal, .stagger').forEach(e => e.classList.add('is-in'));
            var t = document.querySelector('\(position)');
            window.scrollTo({ top: t ? t.getBoundingClientRect().top + window.scrollY - 70 : 0, behavior: 'instant' });
            String(window.scrollY);
            """
        } else {
            script = """
            var settle = document.createElement('style');
            settle.textContent = '*,*::before,*::after{transition:none !important;animation:none !important}';
            document.head.appendChild(settle);
            document.querySelectorAll('.reveal, .stagger').forEach(e => e.classList.add('is-in'));
            window.scrollTo({ top: \(position), behavior: 'instant' });
            String(window.scrollY);
            """
        }

        webView.evaluateJavaScript(script) { result, _ in
            print("scrolled to \(result ?? "?")")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.9) { self.shoot() }
        }
    }

    private func shoot() {
        let configuration = WKSnapshotConfiguration()
        configuration.rect = webView.bounds
        webView.takeSnapshot(with: configuration) { image, error in
            guard let image,
                  let tiff = image.tiffRepresentation,
                  let rep = NSBitmapImageRep(data: tiff),
                  let png = rep.representation(using: .png, properties: [:]) else {
                print("snapshot failed: \(error?.localizedDescription ?? "unknown")")
                exit(1)
            }
            try? png.write(to: URL(fileURLWithPath: self.output))
            print("wrote \(self.output)")
            exit(0)
        }
    }
}

let application = NSApplication.shared
application.setActivationPolicy(.accessory)

let frame = NSRect(x: 0, y: 0, width: width, height: height)
let shooter = Shooter(frame: frame, output: output, position: position, wantsDark: wantsDark)

// The view has to be in a window, or WebKit never composites anything.
let window = NSWindow(contentRect: frame, styleMask: [.borderless], backing: .buffered, defer: false)
window.contentView = shooter.webView
window.appearance = NSAppearance(named: wantsDark ? .darkAqua : .aqua)
window.orderBack(nil)

shooter.webView.load(URLRequest(url: url))
application.run()
