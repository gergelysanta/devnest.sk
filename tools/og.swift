import AppKit

// Draws the link preview card, assets/img/brand/og.png, at the 1200×630 most
// scrapers expect. The logo is DevNestLogo.svg, the same file the header and
// footer use; the colours are the site's light tokens. Run from the repo
// root, so the relative path to the logo resolves:
//
//   swiftc -O tools/og.swift -o /tmp/og && /tmp/og assets/img/brand/og.png

let out = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "og.png"
let logoPath = "assets/img/brand/DevNestLogo.svg"
let W = 1200, H = 630

let cs = CGColorSpaceCreateDeviceRGB()
let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8, bytesPerRow: 0,
                    space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!

func rgb(_ r: Double, _ g: Double, _ b: Double) -> CGColor {
    CGColor(red: r / 255, green: g / 255, blue: b / 255, alpha: 1)
}
let bg     = rgb(244, 245, 247)   // --bg
let muted  = rgb(106, 116, 130)   // --muted
let accent = rgb(10, 111, 208)    // --accent

ctx.setFillColor(bg)
ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))

// The same soft accent glow the hero has, centred above the wordmark.
if let glow = CGGradient(colorsSpace: cs,
                         colors: [accent.copy(alpha: 0.16)!, accent.copy(alpha: 0)!] as CFArray,
                         locations: [0, 1]) {
    ctx.saveGState()
    ctx.drawRadialGradient(glow, startCenter: CGPoint(x: 600, y: 700), startRadius: 0,
                           endCenter: CGPoint(x: 600, y: 700), endRadius: 620, options: [])
    ctx.restoreGState()
}

// The logo already spells out the company name, so it replaces both the old
// mark and the "DevNest" wordmark text in one draw. AppKit rasterises the SVG
// itself; only the target rectangle is ours to pick. 758×302 is the file's
// own viewBox, so this keeps its aspect ratio.
guard let logo = NSImage(contentsOfFile: logoPath) else {
    fatalError("could not load \(logoPath)")
}
let logoH: CGFloat = 220
let logoW = logoH * 758 / 302
do {
    let gc = NSGraphicsContext(cgContext: ctx, flipped: false)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = gc
    logo.draw(in: CGRect(x: 92, y: 260, width: logoW, height: logoH),
              from: .zero, operation: .sourceOver, fraction: 1)
    NSGraphicsContext.restoreGraphicsState()
}

func draw(_ text: String, at point: CGPoint, size: CGFloat, weight: NSFont.Weight, color: CGColor,
          tracking: CGFloat = 0) {
    let font = NSFont.systemFont(ofSize: size, weight: weight)
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: NSColor(cgColor: color)!,
        .kern: tracking,
    ]
    let line = NSAttributedString(string: text, attributes: attributes)
    let gc = NSGraphicsContext(cgContext: ctx, flipped: false)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = gc
    line.draw(at: point)
    NSGraphicsContext.restoreGraphicsState()
}

draw("Mac software from Slovakia", at: CGPoint(x: 100, y: 208), size: 36, weight: .regular, color: muted)
draw("TRACKTIV   ·   ASSETSCOUT",
     at: CGPoint(x: 100, y: 118), size: 22, weight: .medium, color: accent, tracking: 3)

let rep = NSBitmapImageRep(cgImage: ctx.makeImage()!)
rep.size = NSSize(width: W, height: H)
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
print("wrote \(out)")
