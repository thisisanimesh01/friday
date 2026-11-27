# FRIDAY Privacy and Security Architecture

## 1. Permanent Deny-by-Default PrivacyGuard

FRIDAY enforces a deterministic, code-level deny-by-default security barrier (`src/friday/security/privacy_guard.py`) that operates prior to and completely independent of LLM reasoning or prompt context.

### A. Permanently Protected Personal Folder
* **Protected Target:** `~/Desktop/me and she/`
* **Invariant:** NEVER read, write, scan, list, search, delete, copy, move, inspect, or upload.
* **Invariant:** NEVER access indirectly via AppleScript, Finder, Shortcuts, terminal aliases, symlinks, or hard links.
* **Invariant:** NEVER mention in active context, memory persistence, audit logs, or backups.
* **Non-Overridable:** Cannot be overridden by CLI flags, natural language, voice confirmations, or prompt injection.
* **Case and Encoding Neutral:** Normalizes uppercase, lowercase, mixed case, underscores, and URL encodings (`me%20and%20she`).
* **Inode Hard-Link Inspection:** Compares candidate filesystem inode numbers (`st_ino`, `st_dev`) against protected targets to prevent hard-link bypasses.

### B. Blocked macOS Personal Repositories
The following personal macOS data repositories are blocked by default:
* macOS Photos Library: `~/Pictures/Photos Library.photoslibrary`
* macOS Messages Database: `~/Library/Messages`
* macOS Keychains: `~/Library/Keychains`
* macOS Mail Containers: `~/Library/Mail`
* SSH Credentials: `~/.ssh`
* AWS Credentials: `~/.aws`
* GPG Keyrings: `~/.gnupg`

---

## 2. Dedicated FRIDAY Workspace Confinement

All user-facing file creation, audio recordings, camera captures, and screenshots are strictly confined to:
```
~/Desktop/friday workspace/
├── camera/          # Single-use on-demand camera captures
├── documents/       # Generated text documents and markdown
├── downloads/       # Downloaded files and assets
├── exports/         # Encrypted/exported memory archives
├── images/          # Images created or processed
├── projects/        # Workspace development projects
├── reports/         # System reports and audit summaries
├── screenshots/     # Authorized on-demand screenshots
├── temp/            # Ephemeral working files
└── videos/          # Recorded or processed video assets
```
* Path traversal attempts (`../`, `../../`, `/`, `~`) are blocked with `PrivacyViolationError`.
* Symbolic links pointing outside the workspace root are rejected.

---

## 3. macOS Permissions and OS-Level Isolation

FRIDAY respects macOS TCC (Transparency, Consent, and Control) architecture without ever requesting Full Disk Access or bypassing security boundaries:

1. **Inherited Environment:** FRIDAY inherits sandboxing and permissions from Terminal, Python, or the parent IDE.
2. **Never Request Full Disk Access:** FRIDAY does not require or prompt for Full Disk Access (`kTCCServiceSystemPolicyAllFiles`).
3. **Graceful Permission Failures:** When macOS Accessibility (`-1719`), Screen Recording, or Camera access is denied in System Settings, operations fail closed with clear status messaging rather than crashing.

---

## 4. Media Capture Authorization

* **Explicit On-Demand Only:** Single-use capture triggered only by direct user instruction. Background, continuous, or polling capture is strictly prohibited.
* **Hardware Immediate Release:** Camera sessions and capture devices close immediately upon single-frame acquisition.
* **Display Visibility Screen Scan:** Screen capture (`capture_screenshot`) performs a pre-flight window title scan (`is_protected_content_visible_on_screen`). If any visible window title contains protected keywords, capture is blocked immediately.
* **Safe Screenshot Modes:** Fullscreen capture is constrained by the visibility scan. Window-specific and region-specific captures are favored.

---

## 5. Process Termination & Process-Specific Killing

* Replaced unverified shell `pkill -9 -f <query>` with verified process lookup:
  1. Queries macOS System Events and `pgrep -x` for exact process name matches.
  2. Resolves exact PIDs.
  3. Terminates specific target PIDs only (`os.kill(pid, 9)`), avoiding accidental termination of unrelated applications or background processes.

---

## 8. System Settings, Hardware Controls & Health Monitoring Security

* **Mandatory Security Corrections (Milestone 6.4):**
  - **Global Trash Deletion Disabled:** The `empty_trash` template is permanently disabled to guarantee that FRIDAY never purges or removes files outside `~/Desktop/friday workspace/`.
  - **Unverified Shortcut Disablement:** Audited default shortcuts; `Quick Note` has been disabled due to external unconfined storage dependencies.
  - **External Notes Disablement:** Direct Apple Notes creation is disabled to preserve dedicated workspace confinement.
  - **OS-Level vs. Code-Level Separation:** Synthetic test fixtures explicitly verify that Python path sanitization is distinct from operating system sandboxing and TCC access controls.
* **Confirmation-Guarded Disruptive Hardware Controls:**
  - Connectivity (`set_wifi_power`, `set_bluetooth_power`) and power controls (`lock_screen`, `system_sleep`) are classified as HIGH risk and require confirmation.
  - System restart (`system_restart`) and shutdown (`system_shutdown`) are classified as CRITICAL risk and require fresh, action-specific user confirmation. Force-restarting or killing active processes is prohibited.
* **Workspace Report Confinement:**
  - Automated system health summaries are validated to write strictly into `~/Desktop/friday workspace/reports/`. Traversal attempts (`../`, `/`, `~`) trigger immediate `PrivacyViolationError`.
