import Foundation
import Vision
import CoreGraphics
import ImageIO

struct OCRBox: Codable {
    let text: String
    let confidence: Float
    let x: Double
    let y: Double
    let width: Double
    let height: Double
}

struct OCRResult: Codable {
    let status: String
    let engine: String
    let languages: [String]
    let image_width: Int
    let image_height: Int
    let text: String
    let elements: [OCRBox]
    let error: String?
}

func emitError(_ message: String) -> Never {
    let err = OCRResult(
        status: "error",
        engine: "apple_vision",
        languages: [],
        image_width: 0,
        image_height: 0,
        text: "",
        elements: [],
        error: message
    )
    if let data = try? JSONEncoder().encode(err), let str = String(data: data, encoding: .utf8) {
        print(str)
    }
    exit(1)
}

guard CommandLine.arguments.count > 1 else {
    emitError("missing_image_path")
}

let imagePath = CommandLine.arguments[1]

// Mode query: --list-languages
if imagePath == "--list-languages" {
    if #available(macOS 11.0, *) {
        let request = VNRecognizeTextRequest()
        let langs = (try? request.supportedRecognitionLanguages()) ?? []
        let revs = VNRecognizeTextRequest.supportedRevisions.map { "\($0)" }
        let out: [String: Any] = [
            "status": "success",
            "engine": "apple_vision",
            "supported_languages": langs,
            "supported_revisions": revs
        ]
        if let data = try? JSONSerialization.data(withJSONObject: out, options: [.prettyPrinted]),
           let str = String(data: data, encoding: .utf8) {
            print(str)
            exit(0)
        }
    }
    emitError("unsupported_os_version")
}

let fileUrl = URL(fileURLWithPath: imagePath)

guard let imageSource = CGImageSourceCreateWithURL(fileUrl as CFURL, nil) else {
    emitError("cannot_open_image_source")
}

guard let cgImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
    emitError("corrupted_or_unsupported_image")
}

let width = cgImage.width
let height = cgImage.height

guard width > 0 && height > 0 else {
    emitError("empty_image_dimensions")
}

var recognizedBoxes: [OCRBox] = []
var fullTextLines: [String] = []

let request = VNRecognizeTextRequest { req, error in
    guard let observations = req.results as? [VNRecognizedTextObservation] else { return }
    for obs in observations {
        guard let candidate = obs.topCandidates(1).first else { continue }
        let bbox = obs.boundingBox
        // Vision coordinates: origin at bottom-left normalized [0, 1].
        // Convert to standard top-left pixel coordinates.
        let pixelX = bbox.origin.x * Double(width)
        let pixelY = (1.0 - bbox.origin.y - bbox.size.height) * Double(height)
        let pixelW = bbox.size.width * Double(width)
        let pixelH = bbox.size.height * Double(height)

        recognizedBoxes.append(OCRBox(
            text: candidate.string,
            confidence: candidate.confidence,
            x: pixelX,
            y: pixelY,
            width: pixelW,
            height: pixelH
        ))
        fullTextLines.append(candidate.string)
    }
}

request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

if CommandLine.arguments.count > 2 && !CommandLine.arguments[2].isEmpty {
    let customLangs = CommandLine.arguments[2]
        .split(separator: ",")
        .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
        .filter { !$0.isEmpty }
    if !customLangs.isEmpty {
        request.recognitionLanguages = customLangs
    }
}

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
    let out = OCRResult(
        status: "success",
        engine: "apple_vision",
        languages: request.recognitionLanguages,
        image_width: width,
        image_height: height,
        text: fullTextLines.joined(separator: "\n"),
        elements: recognizedBoxes,
        error: nil
    )
    let encoder = JSONEncoder()
    encoder.outputFormatting = .prettyPrinted
    if let data = try? encoder.encode(out), let str = String(data: data, encoding: .utf8) {
        print(str)
    }
} catch {
    emitError(error.localizedDescription)
}
