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
      └─ task-manager/
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

## License

MIT. See [LICENSE](LICENSE).
