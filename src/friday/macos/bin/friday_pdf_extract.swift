import Foundation
import PDFKit
import CoreGraphics
import ImageIO

struct PageInfo: Codable {
    let page_number: Int
    let text: String
    let has_native_text: Bool
    let width: Double
    let height: Double
    let rendered_image_path: String?
}

struct PDFExtractResult: Codable {
    let status: String
    let page_count: Int
    let pages: [PageInfo]
    let total_native_text_length: Int
    let error: String?
}

func emitError(_ msg: String) -> Never {
    let err = PDFExtractResult(status: "error", page_count: 0, pages: [], total_native_text_length: 0, error: msg)
    if let d = try? JSONEncoder().encode(err), let s = String(data: d, encoding: .utf8) {
        print(s)
    }
    exit(1)
}

guard CommandLine.arguments.count > 1 else {
    emitError("missing_pdf_path")
}

let pdfPath = CommandLine.arguments[1]
let renderImages = CommandLine.arguments.count > 2 && CommandLine.arguments[2] == "--render-images"
let renderOutDir = CommandLine.arguments.count > 3 ? CommandLine.arguments[3] : "/tmp"

let url = URL(fileURLWithPath: pdfPath)
guard let doc = PDFDocument(url: url) else {
    emitError("cannot_open_pdf")
}

let count = doc.pageCount
guard count > 0 else {
    emitError("empty_pdf_document")
}

var pages: [PageInfo] = []
var totalLen = 0

for i in 0..<count {
    guard let page = doc.page(at: i) else { continue }
    let bounds = page.bounds(for: .mediaBox)
    let w = Double(bounds.width)
    let h = Double(bounds.height)
    let text = (page.string ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    let hasText = text.count > 10
    totalLen += text.count

    var renderedPath: String? = nil
    if renderImages || !hasText {
        // Render page at 2.0x scale for Vision OCR
        let outImg = "\(renderOutDir)/pdf_page_\(i)_\(UUID().uuidString.prefix(6)).png"
        let scale = 2.0
        let pxW = Int(w * scale)
        let pxH = Int(h * scale)

        if pxW > 0 && pxH > 0 {
            let colorSpace = CGColorSpaceCreateDeviceRGB()
            if let ctx = CGContext(data: nil, width: pxW, height: pxH, bitsPerComponent: 8, bytesPerRow: pxW * 4, space: colorSpace, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) {
                ctx.setFillColor(CGColor(red: 1.0, green: 1.0, blue: 1.0, alpha: 1.0))
                ctx.fill(CGRect(x: 0, y: 0, width: pxW, height: pxH))
                ctx.saveGState()
                ctx.scaleBy(x: scale, y: scale)
                page.draw(with: .mediaBox, to: ctx)
                ctx.restoreGState()

                if let img = ctx.makeImage() {
                    let outUrl = URL(fileURLWithPath: outImg) as CFURL
                    if let dest = CGImageDestinationCreateWithURL(outUrl, "public.png" as CFString, 1, nil) {
                        CGImageDestinationAddImage(dest, img, nil)
                        if CGImageDestinationFinalize(dest) {
                            renderedPath = outImg
                        }
                    }
                }
            }
        }
    }

    pages.append(PageInfo(
        page_number: i + 1,
        text: text,
        has_native_text: hasText,
        width: w,
        height: h,
        rendered_image_path: renderedPath
    ))
}

let result = PDFExtractResult(
    status: "success",
    page_count: count,
    pages: pages,
    total_native_text_length: totalLen,
    error: nil
)

let encoder = JSONEncoder()
encoder.outputFormatting = .prettyPrinted
if let d = try? encoder.encode(result), let s = String(data: d, encoding: .utf8) {
    print(s)
}
