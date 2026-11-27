# FRIDAY Automation Architecture (AppleScript & Shortcuts)

## Overview & Security Policy
Milestone 6.3 introduces secure automation for macOS via allowlisted AppleScript templates and macOS Shortcuts integration.

### Fundamental Security & Privacy Invariants

1. **Strictly Allowlisted AppleScript Templates Only:**
   - FRIDAY never executes arbitrary, dynamic, or LLM-generated AppleScript or JXA code.
   - All automations run from statically reviewed, strongly typed templates with parameter schemas.
2. **Prohibited Token Gates:**
   - Any script containing shell execution (`do shell script`), elevation (`administrator privileges`, `sudo`), or destructive file operations (`rm -rf`) is rejected immediately prior to compilation or execution.
3. **Shortcuts Verification & Approval Registry:**
   - macOS Shortcuts (`/usr/bin/shortcuts`) require pre-approval with documented resource boundaries.
   - Unverified or modified shortcuts are blocked by default until explicitly approved by the user.
4. **Permanent PrivacyGuard Enforcement:**
   - Any parameter, script text, shortcut name, or input file pointing to `~/Desktop/me and she/` or protected system repositories (Photos Library, Messages, Keychains, Mail, SSH, AWS, GPG) is immediately blocked.
   - Never inspects, lists, or modifies protected folders.
5. **Dedicated Workspace Confinement:**
   - All automation outputs are strictly confined to `~/Desktop/friday workspace/` (specifically `friday workspace/reports/` for shortcuts).
6. **Process-Group Timeout & Tree Termination:**
   - Subprocesses are spawned in dedicated POSIX process groups (`preexec_fn=os.setsid`).
   - If execution exceeds the allotted timeout, `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` terminates the entire process tree cleanly.

---

## Allowlisted AppleScript Templates

| Template Name | Description | Parameters | Risk / Confirmation |
|---|---|---|---|
| `display_notification` | Native macOS banner notification | `title` (str), `message` (str), `sound` (str) | Low / No |
| `create_note` | Append/create note in Apple Notes | `title` (str), `body` (str) | Low / No |
| `music_play_pause` | Toggle playback in Music.app | None | Low / No |
| `get_current_track` | Query track & artist from Music.app | None | Read-Only / No |
| `set_volume` | Set system volume (0-100) | `level` (int) | Low / No |
| `empty_trash` | Empty macOS Finder Trash | None | High / **Requires Confirmation** |

---

## macOS Shortcuts Integration

FRIDAY integrates with macOS Shortcuts CLI (`/usr/bin/shortcuts`):
- **List Installed Shortcuts:** Discovers available system shortcuts.
- **Approval Registry:** Stores approved shortcut metadata and boundaries in `~/.friday/approved_shortcuts.json`.
- **Default Allowlisted Shortcuts:** Includes `Charger Sound`, `Quick Note`, and `Open Workspace`.
- **Safe Execution:** Enforces parameter sanitization, timeout management, and output directory confinement.

---

## Natural Language Routing Examples

English, Hindi, and Hinglish queries are routed directly to allowlisted automations:
- *"show notification Build complete"* -> `display_notification`
- *"notification dikhao System ready"* -> `display_notification`
- *"create note Grocery shopping list"* -> `create_note`
- *"note banao Meeting agenda"* -> `create_note`
- *"play music"* / *"gaana bajao"* -> `music_play_pause`
- *"what is playing"* / *"kaunsa gaana chal raha hai"* -> `get_current_track`
- *"empty trash"* / *"trash khali karo"* -> `empty_trash` (prompts for confirmation)
- *"list shortcuts"* / *"shortcuts dikhao"* -> `list_shortcuts`
- *"run shortcut Charger Sound"* -> `run_shortcut`

---

## CLI Inspection Commands

```bash
# List available AppleScript templates
friday --list-scripts

# Execute a notification template (dry-run preview)
friday --run-script display_notification --script-title "FRIDAY" --script-message "Hello" --dry-run

# List installed macOS shortcuts and security approval status
friday --list-shortcuts

# Approve an installed shortcut
friday --approve-shortcut "Daily Routine"

# Execute a verified shortcut
friday --run-shortcut "Charger Sound"
```
