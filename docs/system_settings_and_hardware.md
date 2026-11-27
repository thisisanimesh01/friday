# FRIDAY System Settings & Audio/Display Controls Architecture

## Overview
Milestone 6.4 implements comprehensive macOS system settings, hardware controls, and health monitoring with strict risk classification and safety confirmations.

---

## 1. System Settings & Hardware Controls

| Control Domain | Actions / Handlers | Supported APIs / Tools | Safety / Confirmation |
|---|---|---|---|
| **Audio Output** | `set_audio_volume`, `get_audio_volume` | AppleScript / CoreAudio | Reversible; Direct Execution |
| **Audio Mute** | `set_audio_mute`, `toggle_audio_mute` | AppleScript | Reversible; Direct Execution |
| **Audio Devices** | `get_audio_devices`, `set_audio_device` | `system_profiler` / SwitchAudioSource | Read-only discovery. Switch requires SwitchAudioSource (unsupported reported gracefully) |
| **Display Brightness** | `get_display_brightness`, `set_display_brightness` | `brightness` CLI / System Events | Supported via `brightness` tool; graceful notification if unsupported |
| **Appearance** | `set_appearance`, `toggle_appearance` | System Events Appearance Preferences | Reversible Dark/Light mode toggle |
| **Focus Mode** | `get_focus_mode`, `toggle_focus_mode` | System Events / Control Center | Non-disruptive toggle |

---

## 2. Hardware Monitoring & Health Reports

1. **Battery & Power Monitoring (`get_battery_status`):**
   - Percentage level, AC/Battery power source, charging/discharging state, estimated time remaining via `pmset -g batt`.
2. **Thermal State & Throttling (`get_thermal_status`):**
   - Real-time thermal warning levels and CPU throttling notifications via `pmset -g therm`.
3. **Hardware Utilization Metrics (`get_hardware_metrics`):**
   - Live CPU percent, RAM total/used/percent, and root disk capacity/usage via `psutil`.
4. **Network & Wireless Status:**
   - Wi-Fi interface status (`get_wifi_status`) querying power state and active SSID via `/usr/sbin/networksetup`.
   - Bluetooth status (`get_bluetooth_status`) querying adapter power via `blueutil`.
5. **System Health Report Generation (`generate_system_health_report`):**
   - Generates structured Markdown reports confined strictly to `~/Desktop/friday workspace/reports/system_health_report_<timestamp>.md`.

---

## 3. Risk Classification & Confirmation Policies

| Action | Risk Tier | Confirmation Policy | Safe Simulation |
|---|---|---|---|
| `set_wifi_power` | `HIGH` | Requires explicit user confirmation | Simulated unless `--yes` and unsandboxed |
| `set_bluetooth_power` | `HIGH` | Requires explicit user confirmation | Simulated unless `--yes` and unsandboxed |
| `lock_screen` | `HIGH` | Requires confirmation | Simulated in automated test suites |
| `system_sleep` | `HIGH` | Requires confirmation | Simulated in automated test suites |
| `system_restart` | `CRITICAL` | Requires fresh, action-specific confirmation | Simulated; never force restarts |
| `system_shutdown` | `CRITICAL` | Requires fresh, action-specific confirmation | Simulated; never force shuts down |

---

## 4. Mandatory Security Invariants & Corrections

1. **Global `empty_trash` Permanently Disabled:**
   - The AppleScript `empty_trash` template has been permanently disabled. FRIDAY never deletes files or clears caches outside `~/Desktop/friday workspace/`.
2. **Audit of Default Shortcuts:**
   - Evaluated default shortcuts. `Quick Note` has been disabled because it interacts with unconfined external notes stores. Only verified, resource-bounded shortcuts (`Charger Sound`, `Open Workspace`) remain active.
3. **Apple Notes Automation Disabled:**
   - Notes creation automation is disabled because Notes.app synchronizes with external iCloud/system stores that cannot satisfy dedicated workspace confinement.
4. **Synthetic Fixture OS Isolation:**
   - Inode checks and Python path sanitizers are distinct from OS-level sandboxing. Real OS permissions and TCC boundaries are validated using synthetic test fixtures.
5. **Prohibited Target Protection:**
   - `~/Desktop/me and she/` is permanently blocked under deny-by-default rules. The folder is never inspected or touched.
6. **Zero Full Disk Access Requirement:**
   - FRIDAY strictly operates within normal user privileges and standard macOS TCC prompts. Full Disk Access is never requested.

---

## 5. CLI Commands

```bash
# Display live system metrics (CPU, RAM, Disk)
friday --system-metrics

# Query macOS thermal state and throttling
friday --thermal-status

# Audio controls
friday --mute
friday --unmute
friday --list-audio-devices

# Display brightness & appearance
friday --brightness 75
friday --appearance dark
friday --appearance toggle

# Generate comprehensive health report
friday --health-report

# Guarded controls (dry run / simulation without modifying state)
friday --wifi off --dry-run
friday --lock-screen --dry-run
friday --restart --dry-run
```
