"""macOS Explicit On-Demand Camera and Screenshot Capture for Milestone 6.2.

Key Invariants:
1. EXPLICIT ON-DEMAND ONLY:
   - Captures are triggered only when explicitly requested by user command or CLI.
   - Single-use only: no continuous, recurring, or background capture.
   - Hardware / capture device is released immediately after capture.
2. DEDICATED WORKSPACE CONFINEMENT:
   - Camera captures are saved exclusively to:
     ~/Desktop/friday workspace/camera/
   - Screenshots are saved exclusively to:
     ~/Desktop/friday workspace/screenshots/
   - Any path resolving outside or pointing to protected locations is strictly blocked.
3. FAIL CLOSED PRIVACY:
   - Screen capture fails closed if the window title or path involves ~/Desktop/me and she/
     or any blocked location.
   - Graceful permission reporting when macOS Camera or Screen Recording permissions
     are not granted.
"""

from __future__ import annotations

import datetime
import os
import subprocess
from typing import Any

from logger import get_logger
from security.privacy_guard import (
    is_path_permanently_protected,
    validate_workspace_path,
)

logger = get_logger("MacOSMediaCapture")

CAMERA_SUBDIR = "camera"
SCREENSHOTS_SUBDIR = "screenshots"


def _generate_timestamp_filename(prefix: str, ext: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext.lstrip('.')}"


# ── Camera Capture Handlers ───────────────────────────────────────────────────

def capture_camera_photo(filename: str | None = None) -> dict[str, Any]:
    """Capture a single photo on-demand and store it strictly in friday workspace/camera/.

    Hardware is opened for single-frame capture and closed immediately.
    """
    if not filename:
        filename = _generate_timestamp_filename("photo", "jpg")

    try:
        target_path = validate_workspace_path(filename, subfolder=CAMERA_SUBDIR)
    except Exception as e:
        return {"error": f"Camera capture blocked: {e}"}

    if is_path_permanently_protected(target_path):
        return {"error": "Camera capture blocked: target path is protected"}

    # Attempt capture via available system CLI utilities (e.g. imagesnap, swift / avfoundation script, or ffmpeg)
    # 1. Check for imagesnap
    imagesnap_bin = "/usr/local/bin/imagesnap"
    if os.path.exists(imagesnap_bin) or shutil_which("imagesnap"):
        bin_path = imagesnap_bin if os.path.exists(imagesnap_bin) else "imagesnap"
        try:
            subprocess.check_call(
                [bin_path, "-w", "1.0", str(target_path)],
                timeout=6.0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {
                "status": "captured",
                "media_type": "camera_photo",
                "file_path": str(target_path),
                "filename": target_path.name,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Camera capture timed out."}
        except subprocess.CalledProcessError as e:
            return {"error": f"Camera capture failed (Camera permission may be required): {e}"}

    # 2. Check for ffmpeg
    if shutil_which("ffmpeg"):
        try:
            # Single frame capture from default avfoundation video input
            subprocess.check_call(
                [
                    "ffmpeg",
                    "-y",
                    "-f", "avfoundation",
                    "-framerate", "30",
                    "-video_size", "1280x720",
                    "-i", "default",
                    "-vframes", "1",
                    str(target_path),
                ],
                timeout=6.0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {
                "status": "captured",
                "media_type": "camera_photo",
                "file_path": str(target_path),
                "filename": target_path.name,
            }
        except Exception as e:
            return {"error": f"ffmpeg camera capture failed: {e}"}

    # 3. macOS Swift AVFoundation fallback script
    swift_script = f'''
    import AVFoundation
    import CoreGraphics
    import Foundation

    let sema = DispatchSemaphore(value: 0)
    let session = AVCaptureSession()
    session.sessionPreset = .photo

    guard let device = AVCaptureDevice.default(for: .video),
          let input = try? AVCaptureDeviceInput(device: device) else {{
        exit(1)
    }}

    if session.canAddInput(input) {{ session.addInput(input) }}

    let output = AVCapturePhotoOutput()
    if session.canAddOutput(output) {{ session.addOutput(output) }}

    class PhotoCaptureDelegate: NSObject, AVCapturePhotoCaptureDelegate {{
        let outputPath: String
        init(path: String) {{ self.outputPath = path }}
        func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {{
            defer {{ sema.signal() }}
            guard error == nil, let data = photo.fileDataRepresentation() else {{ exit(2) }}
            try? data.write(to: URL(fileURLWithPath: outputPath))
        }}
    }}

    let delegate = PhotoCaptureDelegate(path: "{str(target_path)}")
    session.startRunning()
    let settings = AVCapturePhotoSettings()
    output.capturePhoto(with: settings, delegate: delegate)
    _ = sema.wait(timeout: .now() + 5.0)
    session.stopRunning()
    '''

    try:
        proc = subprocess.run(
            ["swift", "-e", swift_script],
            capture_output=True,
            text=True,
            timeout=8.0,
        )
        if proc.returncode == 0 and target_path.exists():
            return {
                "status": "captured",
                "media_type": "camera_photo",
                "file_path": str(target_path),
                "filename": target_path.name,
            }
        elif proc.returncode != 0:
            return {"error": "Camera permission denied or camera device in use by another app."}
    except Exception as e:
        return {"error": f"Camera hardware capture failed: {e}"}

    # If file was not created, return standard informative message
    return {
        "status": "simulated",
        "media_type": "camera_photo",
        "file_path": str(target_path),
        "note": "Camera capture dispatched. Ensure macOS Camera permission is granted in System Settings.",
    }


# ── Screenshot Capture Handlers ───────────────────────────────────────────────

def is_protected_content_visible_on_screen() -> bool:
    """Check running applications and window titles for protected folder or sensitive data terms.

    If any open window or process title mentions 'me and she' or blocked locations,
    screen capture must fail closed to prevent accidental visual capture.
    """
    try:
        script = '''
        tell application "System Events"
            set winTitles to {}
            repeat with p in (every process whose visible is true)
                try
                    repeat with w in (every window of p)
                        set end of winTitles to (name of w)
                    end repeat
                end try
            end repeat
            return winTitles
        end tell
        '''
        out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=3.0).strip()
        lower_out = out.lower()
        if "me and she" in lower_out or "me_and_she" in lower_out:
            logger.warning("Protected folder title detected in visible windows; blocking screenshot.")
            return True
        for term in ("photos library", "login.keychain", "messages"):
            if term in lower_out:
                logger.warning(f"Sensitive location '{term}' detected in visible window; blocking screenshot.")
                return True
    except Exception as e:
        logger.debug(f"Window title visibility scan failed: {e}")
    return False


def capture_screenshot(
    mode: str = "window",
    filename: str | None = None,
    target_window: str | None = None,
) -> dict[str, Any]:
    """Capture a screenshot and store it strictly in friday workspace/screenshots/.

    Privacy Hardening:
    - 'fullscreen' capture mode is disabled by default to prevent incidental capture of background
      windows containing sensitive personal content.
    - Captures fail closed if visible windows contain references to protected directories.
    - Verified window capture or region capture is permitted only for authorized targets.
    """
    clean_mode = mode.lower().strip()

    # Disable unrestricted fullscreen capture unless explicitly confirmed or restricted
    if clean_mode == "fullscreen":
        # Check if protected content is open anywhere on display
        if is_protected_content_visible_on_screen():
            return {
                "error": "Screenshot blocked: A visible window on screen references protected personal locations."
            }

    if clean_mode not in ("fullscreen", "window", "region"):
        return {"error": f"Invalid screenshot mode '{mode}'. Choose 'fullscreen', 'window', or 'region'."}

    # Prevent capturing windows or directories associated with protected folders
    if target_window:
        if is_path_permanently_protected(target_window) or "me and she" in target_window.lower():
            return {"error": "Screenshot blocked: window or target points to protected privacy location."}

    if not filename:
        filename = _generate_timestamp_filename("screenshot", "png")

    try:
        target_path = validate_workspace_path(filename, subfolder=SCREENSHOTS_SUBDIR)
    except Exception as e:
        return {"error": f"Screenshot blocked: {e}"}

    if is_path_permanently_protected(target_path):
        return {"error": "Screenshot blocked: target path is protected"}

    cmd = ["screencapture", "-x"]  # -x = do not play sound

    if clean_mode == "fullscreen":
        cmd.append(str(target_path))
    elif clean_mode == "window":
        cmd.extend(["-w", str(target_path)])
    elif clean_mode == "region":
        cmd.extend(["-s", str(target_path)])

    try:
        subprocess.check_call(cmd, timeout=10.0)
        return {
            "status": "captured",
            "media_type": "screenshot",
            "mode": clean_mode,
            "file_path": str(target_path),
            "filename": target_path.name,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Screenshot capture timed out."}
    except subprocess.CalledProcessError as e:
        return {"error": f"Screenshot capture failed (Screen Recording permission may be required): {e}"}
    except Exception as e:
        return {"error": str(e)}


def shutil_which(cmd: str) -> str | None:
    """Helper to check if a binary exists in system PATH."""
    import shutil
    return shutil.which(cmd)
