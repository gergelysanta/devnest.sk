import AppKit

// Draws the link preview card, assets/img/brand/og.png, at the 1200×630 most
// scrapers expect. The mark is the same geometry as the favicon and the inline
// SVG in tools/chrome.py; the colours are the site's light tokens.
//
//   swiftc -O tools/og.swift -o /tmp/og && /tmp/og assets/img/brand/og.png

let out = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "og.png"
let W = 1200, H = 630

let cs = CGColorSpaceCreateDeviceRGB()
let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8, bytesPerRow: 0,
                    space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!

func rgb(_ r: Double, _ g: Double, _ b: Double) -> CGColor {
    CGColor(red: r / 255, green: g / 255, blue: b / 255, alpha: 1)
}
let bg     = rgb(244, 245, 247)   // --bg
let ink    = rgb(14, 19, 25)      // --ink
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

// The mark, drawn in a 32-point square scaled up and placed on the left.
func drawMark(at origin: CGPoint, size: CGFloat) {
    let s = size / 32
    ctx.saveGState()
    ctx.translateBy(x: origin.x, y: origin.y + size)
    ctx.scaleBy(x: s, y: -s)

    ctx.addPath(CGPath(roundedRect: CGRect(x: 1, y: 1, width: 30, height: 30),
                       cornerWidth: 8, cornerHeight: 8, transform: nil))
    ctx.setFillColor(accent)
    ctx.fillPath()

    ctx.setStrokeColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.setLineCap(.round)
    ctx.setLineWidth(2.2)
    ctx.addArc(center: CGPoint(x: 16, y: 16), radius: 8.4, startAngle: .pi, endAngle: 0, clockwise: true)
    ctx.strokePath()
    ctx.setAlpha(0.6)
    ctx.addArc(center: CGPoint(x: 16, y: 16.8), radius: 5.4, startAngle: .pi, endAngle: 0, clockwise: true)
    ctx.strokePath()
    ctx.setAlpha(1)
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fillEllipse(in: CGRect(x: 13, y: 11.8, width: 6, height: 6))
    ctx.restoreGState()
}

drawMark(at: CGPoint(x: 96, y: 400), size: 116)

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

draw("DevNest", at: CGPoint(x: 96, y: 268), size: 108, weight: .bold, color: ink, tracking: -4)
draw("Mac software from Slovakia", at: CGPoint(x: 100, y: 208), size: 36, weight: .regular, color: muted)
draw("TRACKTIV   ·   PHOTOMINER   ·   MEDIASCOUT",
     at: CGPoint(x: 100, y: 118), size: 22, weight: .medium, color: accent, tracking: 3)

let rep = NSBitmapImageRep(cgImage: ctx.makeImage()!)
rep.size = NSSize(width: W, height: H)
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
print("wrote \(out)")
