# task-management

A lightweight local task-state helper for multi-step agent workflows.

It keeps progress in JSON files under `.task_state/` and enforces:
- inspect state before changes,
- exactly one `in_progress` task,
- append notes after meaningful attempts,
- auto-`blocked` after 3 failed validations (default),
- final review for remaining `pending` / `blocked` tasks.

## Project Structure

```text
task-management/
├─ AGENTS.md
├─ tools/
│  └─ task_state.py
├─ .task_state/
│  └─ <session>.json
└─ .agents/
   └─ skills/
      └─ task-state-management/
         └─ SKILL.md
```

## Requirements

- Python 3.6+

## Quick Start

```bash
export TASK_SESSION_ID=demo

python3 tools/task_state.py init \
  --session "$TASK_SESSION_ID" \
  --objective "Fix bug, add tests, update docs" \
  --task T1="Fix bug" \
  --task T2="Add tests" \
  --task T3="Update docs"

python3 tools/task_state.py show --session "$TASK_SESSION_ID"
python3 tools/task_state.py start --session "$TASK_SESSION_ID" --task T1
python3 tools/task_state.py note --session "$TASK_SESSION_ID" --task T1 --text "Reproduced issue"
python3 tools/task_state.py fail --session "$TASK_SESSION_ID" --task T1 --text "Validation failed"
python3 tools/task_state.py done --session "$TASK_SESSION_ID" --task T1 --text "Patched and verified"
python3 tools/task_state.py review --session "$TASK_SESSION_ID"
```

## Codex Installation And Usage

### 1) Prerequisite

Install Codex CLI first (this repo provides the workflow/skill, not the CLI binary).

### 2) Use directly inside a project (recommended)

Copy this repository structure into your target project root:

```text
your-project/
├─ AGENTS.md
├─ tools/task_state.py
└─ .agents/skills/task-state-management/SKILL.md
```

Then in Codex, explicitly ask to use the skill:

```text
Please use task-state-management skill for this multi-step task.
```

And set a session id in shell before running workflow commands:

```bash
export TASK_SESSION_ID=my_task_session
python3 tools/task_state.py show --session "$TASK_SESSION_ID"
```

### 3) Install as global Codex skill (optional)

If you want this skill available across repositories:

```bash
mkdir -p ~/.codex/skills/task-state-management
cp .agents/skills/task-state-management/SKILL.md ~/.codex/skills/task-state-management/SKILL.md
```

Recommended pattern:
- keep `tools/task_state.py` in each project repo,
- keep global `~/.codex/skills/task-state-management/SKILL.md` as reusable instruction template.

## License

MIT. See [LICENSE](LICENSE).
