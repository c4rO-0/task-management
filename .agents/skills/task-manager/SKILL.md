---
name: task-manager
description: Maintain local JSON task state for multi-step work, prevent getting stuck on one bug, and ensure remaining tasks are not forgotten.
---

# Task Manager Skill

Use this skill whenever:
- the user asks for 2 or more tasks,
- the work has milestones,
- there is a bugfix + tests + docs style workflow,
- or the task may take multiple iterations.

## Goal

Keep an external source of truth for task progress so work does not get stuck on one issue and forget remaining tasks.

## Required behavior

1. If `TASK_SESSION_ID` is not set, ask the user to set one or suggest one.
2. If no task file exists for the session, initialize it.
3. Always inspect task state before starting implementation.
4. Work on only one task at a time.
5. After each attempt, append a short note and update status.
6. If retry count reaches 3, mark the task as `blocked` and move on.
7. Before finishing, run a review and report any remaining `pending` or `blocked` tasks.

## Command examples

Initialize:

```bash
python3 tools/task_state.py init \
  --session "$TASK_SESSION_ID" \
  --objective "Fix parser bug, add regression tests, update README" \
  --task T1="Fix parser bug" \
  --task T2="Add regression tests" \
  --task T3="Update README"
```

Inspect:

```bash
python3 tools/task_state.py show --session "$TASK_SESSION_ID"
```

Start one task (keep only one `in_progress`):

```bash
python3 tools/task_state.py start --session "$TASK_SESSION_ID" --task T1
```

Record an attempt:

```bash
python3 tools/task_state.py note --session "$TASK_SESSION_ID" --task T1 --text "Reproduced bug with edge input"
python3 tools/task_state.py fail --session "$TASK_SESSION_ID" --task T1 --text "Validation failed in integration test"
```

Finish and review:

```bash
python3 tools/task_state.py done --session "$TASK_SESSION_ID" --task T1 --text "Patched and verified"
python3 tools/task_state.py review --session "$TASK_SESSION_ID"
```
