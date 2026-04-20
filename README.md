# Friday v2

A modular AI assistant for the terminal built with Python. Friday v2 introduces a plugin-based architecture, secure sandboxed file system, memory capabilities, and GitHub automation.

---

## Overview

Friday v2 is no longer just a chatbot. It is a structured command-driven assistant capable of handling system operations, managing files safely, and automating developer workflows.

---

## NOTE
To ensure secuity and responsible sharing, the following components are intentionally excluded from this public repository:

* -brain.py → Core AI reasoning engine
* -plugins/ → Advanced plugin implementations

## WORKFLOW
1. User inputs command in terminal
2. Command is parsed and matched to a plugin
3. Plugin executes action in a secure sandbox environment
4. Output is returned to user and stored in memory for context

## Core Features


### Plugin System

* Dynamic plugin loading
* Extend functionality easily
* GitHub plugin included (status, add, commit, push)

### Secure Sandbox Environment

* All file operations restricted to `friday_workspace`
* Safe file and folder creation
* Delete with confirmation
* Trash system for recovery

### File & Folder Management

* Create, read, open, delete files
* Create folders inside workspace
* Restore and manage trash

### GitHub Automation

* `github status`
* `github add`
* `github commit`
* `github push`

### Memory System

* Stores conversations
* Context-aware responses

### Safety Layer

* Blocks sensitive data access
* Prevents unsafe operations
* Confirmation system for destructive actions

### Built-in Utilities

* Weather
* News
* Time & date
* Location & distance
* Reminders
* Website launcher

---

## Tech Stack

* Python
* Transformers (Hugging Face)
* Local memory storage (SQLite)
* Modular plugin architecture
* External APIs (Weather, News, Maps)

---

## Installation

```bash
git clone https://github.com/thisisanimesh01/friday.git
cd friday
pip install -r requirement.txt
```

---

## Setup

Create workspace directory:

```bash
mkdir ~/Desktop/friday_workspace
```

---

## Run

```bash
python3 main.py
```

---

## Usage Examples

### File Operations

```bash
create test.txt
read test.txt
delete test.txt
```

### Folder Operations

```bash
make folder demo
delete demo
```

### GitHub Commands

```bash
github status
github add
github commit
github push
```

### Utilities

```bash
open youtube
weather in delhi
latest news
time
distance between lucknow to delhi
```

---

## Version

* v1: Basic assistant
* v2: Modular assistant with plugins, sandbox, and GitHub integration

---

## Next (v3)
Roadmap for friday

1.Scheduler + Daily Intelligence
2.Multi-Mode System
3.Self-Learning Command System (with user feedback)
4.Voice Enable (female voice)
5.System COntrol(maybe)

## Author

Animesh Yadav
