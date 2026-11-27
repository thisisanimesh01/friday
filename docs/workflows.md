# FRIDAY Multi-Step Desktop Workflows (Milestone 6.5)

## Overview
The FRIDAY Desktop Workflow Engine provides structured, sequential execution of multi-step desktop tasks using strictly allowlisted `ActionRegistry` operations. It transforms high-level natural language requests and structured definitions into deterministic macOS actions with dependency validation, bounded retries, real-time cancellation, and automatic rollback of reversible steps.

---

## Architecture & Core Components

```
                   User Natural Language Intent
                     (English / Hindi / Hinglish)
                                  │
                                  ▼
                        route_macos_intent()
                                  │
                                  ▼
                        WorkflowEngine (M6.5)
      ┌───────────────────────────┴───────────────────────────┐
      │                                                       │
      ▼                                                       ▼
Built-in Workflows (8)                               Custom Workflows (CRUD)
(developer_mode, study_mode,                (~/Desktop/friday workspace/workflows/)
 system_health_check, etc.)                                   │
      │                                                       │
      └───────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
                       Sequential Execution Loop
      ┌───────────────────────────┼───────────────────────────┐
      │ Step Prerequisite Check   │ Timeout / Cancel Check    │
      │ Single-Use Media Gate     │ Reversible Step Tracking  │
      └───────────────────────────┼───────────────────────────┘
                                  │
                                  ▼
                         ActionRegistry.execute()
```

### 1. Built-in Workflows
1. **Developer Mode (`developer_mode`)**:
   - Switches system appearance to Dark Mode.
   - Sets focused volume level to 20%.
   - Launches macOS Terminal.
   - Snaps Terminal window to `left_half`.
2. **Study Mode (`study_mode`)**:
   - Enables Focus Mode / Do Not Disturb.
   - Mutes system audio output.
3. **System Health Check (`system_health_check`)**:
   - Queries battery level and power source.
   - Queries thermal state and throttling warnings.
   - Samples CPU, RAM, and Disk metrics.
   - Generates a health report inside `~/Desktop/friday workspace/reports/`.
4. **Python Project Setup (`python_project_setup`)**:
   - Creates a structured directory under `~/Desktop/friday workspace/projects/<name>/` (`src/`, `tests/`, `README.md`, `main.py`).
   - Verifies hardware baseline.
5. **Morning Routine (`morning_routine`)**:
   - Switches appearance to Light Mode.
   - Sets daytime audio volume to 45% and unmutes.
   - Reports morning battery levels.
6. **Night Mode (`night_mode`)**:
   - Switches appearance to Dark Mode.
   - Sets soft night volume (15%).
   - Enables Focus Mode / Do Not Disturb.
7. **Focus Mode (`focus_mode`)**:
   - Activates Do Not Disturb.
   - Mutes audio notifications.
8. **Workspace Organization (`workspace_organization`)**:
   - Ensures standard workspace subfolders (`reports/`, `workflows/`, `projects/`, `exports/`, `logs/`) exist without touching existing user files.

---

## Custom Workflow Schema

Custom workflows are stored strictly as JSON files within `~/Desktop/friday workspace/workflows/<id>.json`.

```json
{
  "id": "my_custom_flow",
  "name": "My Custom Workflow",
  "description": "Sets up my custom environment",
  "timeout_s": 60.0,
  "author": "user",
  "steps": [
    {
      "id": "step_1",
      "action": "set_appearance",
      "args": { "dark_mode": true },
      "description": "Switch to dark mode",
      "reversible": true,
      "rollback_action": "set_appearance",
      "rollback_args": { "dark_mode": false }
    },
    {
      "id": "step_2",
      "action": "set_volume",
      "args": { "level": 30 },
      "depends_on": ["step_1"]
    }
  ]
}
```

---

## Safety, Privacy & Resilience Features

- **No Arbitrary Code/Shell Execution:** Only allowlisted operations in `ActionRegistry` can be targeted. Shell commands, arbitrary Python, or unverified AppleScripts are rejected.
- **Dependency Guard:** If any prerequisite step in `depends_on` fails or is skipped, subsequent dependent steps are halted immediately.
- **Bounded Retries:** Step failures may be retried up to 2 times (maximum 3 total attempts) with a 0.2s pause between attempts. Uncontrolled loops are strictly prevented.
- **Safe Rollback:** If a workflow halts mid-sequence due to failure or cancellation, previously executed reversible steps are rolled back in reverse order.
- **Single-Use Media Authorization:** Automated workflows cannot schedule or execute camera captures (`capture_camera`, `capture_photo`) or screenshots (`capture_screenshot`). Live, individual interactive user authorization is always mandatory.
- **Cancellation:** Real-time cancellation can be signaled via CLI (`--stop-workflow`) or voice commands ("Friday, stop the workflow", "workflow roko").

---

## CLI Usage

```bash
# List all built-in and custom workflows
friday --list-workflows

# Preview workflow steps
friday --workflow-preview developer_mode

# Run a workflow
friday --run-workflow developer_mode

# Stop an active workflow
friday --stop-workflow

# Create custom workflow from JSON file
friday --create-workflow /path/to/workflow.json

# Delete custom workflow (requires confirmation)
friday --delete-workflow my_custom_flow --yes
```
