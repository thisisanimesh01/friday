import Foundation
import AppKit

struct WindowInfo: Codable {
    let window_id: Int
    let owner_name: String
    let owner_pid: Int
    let title: String
    let x: Double
    let y: Double
    let width: Double
    let height: Double
    let layer: Int
    let is_on_screen: Bool
    let display_index: Int
}

struct ScreenInfo: Codable {
    let index: Int
    let is_primary: Bool
    let width: Double
    let height: Double
    let visible_x: Double
    let visible_y: Double
    let visible_width: Double
    let visible_height: Double
}

struct DesktopContext: Codable {
    let status: String
    let frontmost_app_name: String
    let frontmost_bundle_id: String
    let frontmost_pid: Int
    let active_window_title: String
    let active_window_bounds: [String: Double]
    let active_window_display: Int
    let is_fullscreen: Bool
    let is_minimized: Bool
    let screens: [ScreenInfo]
    let visible_windows: [WindowInfo]
    let timestamp_utc: String
}

// 1. Screens Discovery
var screensList: [ScreenInfo] = []
for (idx, sc) in NSScreen.screens.enumerated() {
    screensList.append(ScreenInfo(
        index: idx,
        is_primary: (idx == 0),
        width: Double(sc.frame.width),
        height: Double(sc.frame.height),
        visible_x: Double(sc.visibleFrame.origin.x),
        visible_y: Double(sc.visibleFrame.origin.y),
        visible_width: Double(sc.visibleFrame.width),
        visible_height: Double(sc.visibleFrame.height)
    ))
}

func getDisplayIndex(x: Double, y: Double, w: Double, h: Double) -> Int {
    let midX = x + (w / 2.0)
    let midY = y + (h / 2.0)
    for (idx, sc) in NSScreen.screens.enumerated() {
        let f = sc.frame
        if midX >= Double(f.origin.x) && midX <= Double(f.origin.x + f.width) {
            return idx
        }
    }
    return 0
}

// 2. Frontmost Application
let frontApp = NSWorkspace.shared.frontmostApplication
let frontName = frontApp?.localizedName ?? "Unknown"
let frontBundle = frontApp?.bundleIdentifier ?? "Unknown"
let frontPid = Int(frontApp?.processIdentifier ?? 0)

var winList: [WindowInfo] = []
var activeWinTitle = ""
var activeWinBounds: [String: Double] = ["x": 0, "y": 0, "width": 0, "height": 0]
var activeWinDisplay = 0
var isFullscreen = false
var isMinimized = false

// 3. Quartz Window List Inspection
if let rawList = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] {
    for raw in rawList {
        let winId = raw[kCGWindowNumber as String] as? Int ?? 0
        let owner = raw[kCGWindowOwnerName as String] as? String ?? ""
        let pid = raw[kCGWindowOwnerPID as String] as? Int ?? 0
        let title = raw[kCGWindowName as String] as? String ?? ""
        let layer = raw[kCGWindowLayer as String] as? Int ?? 0
        let isShared = raw[kCGWindowIsOnscreen as String] as? Bool ?? true

        var x = 0.0, y = 0.0, w = 0.0, h = 0.0
        if let bDict = raw[kCGWindowBounds as String] as? [String: Any] {
            x = (bDict["X"] as? NSNumber)?.doubleValue ?? 0.0
            y = (bDict["Y"] as? NSNumber)?.doubleValue ?? 0.0
            w = (bDict["Width"] as? NSNumber)?.doubleValue ?? 0.0
            h = (bDict["Height"] as? NSNumber)?.doubleValue ?? 0.0
        }

        // Layer 0 corresponds to normal application windows
        if layer == 0 && w > 10 && h > 10 {
            let dispIdx = getDisplayIndex(x: x, y: y, w: w, h: h)
            let winObj = WindowInfo(
                window_id: winId,
                owner_name: owner,
                owner_pid: pid,
                title: title,
                x: x,
                y: y,
                width: w,
                height: h,
                layer: layer,
                is_on_screen: isShared,
                display_index: dispIdx
            )
            winList.append(winObj)

            if owner == frontName && activeWinTitle.isEmpty {
                activeWinTitle = title
                activeWinBounds = ["x": x, "y": y, "width": w, "height": h]
                activeWinDisplay = dispIdx

                // Detect fullscreen if window dimensions match primary or target screen
                if let targetScreen = NSScreen.screens.first(where: {
                    abs(Double($0.frame.width) - w) < 2.0 && abs(Double($0.frame.height) - h) < 2.0
                }) {
                    isFullscreen = true
                }
            }
        }
    }
}

// 4. Fallback Active Window Title using AppleScript if Quartz window title is empty
if activeWinTitle.isEmpty && !frontName.isEmpty {
    let scriptSrc = "tell application \"System Events\" to tell process \"\(frontName)\" to get name of front window"
    if let appleScript = NSAppleScript(source: scriptSrc) {
        var errorDict: NSDictionary?
        let output = appleScript.executeAndReturnError(&errorDict)
        if errorDict == nil, let stringVal = output.stringValue, !stringVal.isEmpty {
            activeWinTitle = stringVal
        }
    }
}

let formatter = ISO8601DateFormatter()
let timestamp = formatter.string(from: Date())

let ctx = DesktopContext(
    status: "success",
    frontmost_app_name: frontName,
    frontmost_bundle_id: frontBundle,
    frontmost_pid: frontPid,
    active_window_title: activeWinTitle,
    active_window_bounds: activeWinBounds,
    active_window_display: activeWinDisplay,
    is_fullscreen: isFullscreen,
    is_minimized: isMinimized,
    screens: screensList,
    visible_windows: winList,
    timestamp_utc: timestamp
)

let encoder = JSONEncoder()
encoder.outputFormatting = .prettyPrinted
if let data = try? encoder.encode(ctx), let out = String(data: data, encoding: .utf8) {
    print(out)
}
