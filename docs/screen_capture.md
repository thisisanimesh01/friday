# FRIDAY Screen Capture & Display Awareness (Milestone 7.1)

## Overview
Milestone 7.1 establishes the foundational, permission-hardened screen capture and display inspection architecture for project FRIDAY on macOS (Apple Silicon M1, 8GB RAM). 

Screen capture operates strictly under deterministic, code-level permission enforcement, mandatory single-use user authorization, fail-closed privacy screening, and exclusive output confinement within the dedicated FRIDAY workspace.

---

## Architecture & Security Invariants

```
                   User Natural Language Intent / CLI
                                   │
                                   ▼
                        route_macos_intent()
                                   │
                                   ▼
                ┌─────────────────────────────────────┐
                │ 1. PrivacyGuard Pre-Flight Scan     │──► (Fail closed if protected
                │    - Visible window titles scan     │     folder references found)
                │    - Target window path validation  │
                └─────────────────────────────────────┘
                                   │ (Pass)
                                   ▼
                ┌─────────────────────────────────────┐
                │ 2. Single-Use Authorization Check   │──► (Nonce bound to mode/target;
                │    - Fresh authorization required   │     consumed immediately)
                └─────────────────────────────────────┘
                                   │ (Valid)
                                   ▼
                ┌─────────────────────────────────────┐
                │ 3. Screen Recording TCC Check       │──► (Fails closed if denied with
                │    - Non-interactive fast probe     │     System Settings guidance)
                └─────────────────────────────────────┘
                                   │ (Authorized)
                                   ▼
                ┌─────────────────────────────────────┐
                │ 4. Native Capture Acquisition       │
                │    - Fullscreen (-D <index>)        │
                │    - Active Window (-w)             │
                │    - Region Rectangle (-R x,y,w,h)  │
                └─────────────────────────────────────┘
                                   │
                                   ▼
                ┌─────────────────────────────────────┐
                │ 5. Output Validation & Stripping    │
                │    - PNG signature & chunk check    │
                │    - Metadata chunk stripping       │
                │    - Atomic swap to permanent file  │
                └─────────────────────────────────────┘
                                   │
                                   ▼
        ~/Desktop/friday workspace/screenshots/screenshot_YYYY-MM-DD_HH-MM-SS_<nonce>.png
```

---

## Capture Modes & Capabilities

1. **Fullscreen Capture (`fullscreen`):**
   - Captures entire display monitor content.
   - Supports display targeting (`display_index=1` for main Retina display).
   - Pre-flight window title check ensures no windows mentioning protected folders or sensitive personal repositories are visible anywhere on display.
2. **Active Window Capture (`window`):**
   - Targets the active frontmost window.
   - Validates window boundary geometry and frontmost application.
   - Rejects targets associated with protected folders.
3. **Rectangular Region Capture (`region`):**
   - Captures bounding box `(x, y, width, height)`.
   - Validates coordinates and ensures positive non-zero dimensions.
   - Handles Retina coordinate scaling (`2.0x` scaling factor).

---

## Screen Recording Permission Framework

- **TCC Detection:** Fast non-interactive query detects whether Terminal/Python has been granted Screen Recording access.
- **Fail-Closed Reporting:** If access is ungranted or revoked, captures immediately fail closed and display actionable guidance:
  > `Open macOS System Settings > Privacy & Security > Screen & System Audio Recording, and enable permission for Terminal/Python.`
- **Never Requests Full Disk Access:** FRIDAY never requests Full Disk Access (`kTCCServiceSystemPolicyAllFiles`).

---

## Single-Use Authorization Model

- Every capture requires an explicit user command.
- The authorization token is bound strictly to `(mode, target_window, nonce)`.
- The token is consumed immediately upon execution to prevent replay attacks.
- Tokens expire automatically after 30 seconds.
- Saved multi-step workflows cannot inherit or schedule automated screen captures.

---

## PNG Validation & Metadata Stripping

To protect user privacy and prevent data leakage:
- Pure Python zero-dependency parser verifies PNG signature (`\x89PNG\r\n\x1a\n`) and mandatory `IHDR` / `IEND` chunks.
- Auxiliary metadata chunks (`tEXt`, `zTXt`, `iTXt`, `pHYs`) containing timestamps, machine identifiers, or camera profiles are completely stripped.
- Files are written to a temporary `.tmp.png` file first and atomically swapped into place only upon passing validation.

---

## Dedicated Workspace Confinement

All authorized screenshots are saved exclusively to:
```
~/Desktop/friday workspace/screenshots/
```
- Non-destructive atomic creation preserves existing files.
- Path traversal (`../`, `/tmp`) and symlink escapes raise `PrivacyViolationError`.

---

## CLI Usage

```bash
# Check Screen Recording permission status
friday --check-screen-permission

# Discover connected displays and Retina resolutions
friday --discover-displays

# Preview capture without acquiring pixels or writing files
friday --take-screenshot fullscreen --dry-run

# Capture active window
friday --take-screenshot window

# Capture rectangular bounding region
friday --capture-region "100,100,600,400"

# Cancel active capture authorization
friday --cancel-capture

# Test capture using synthetic fixture
friday --take-screenshot fullscreen --simulated-capture
```
