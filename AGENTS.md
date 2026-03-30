# AGENTS.md

## Task-state protocol (mandatory)

For any task involving multiple steps, bugs, milestones, or follow-up work, you must use the local task-state workflow.

Rules:
1. Before making changes, inspect task state first.
2. Keep exactly one task as `in_progress` at a time.
3. After each meaningful attempt, update task notes and status.
4. If the current task fails validation 3 times, mark it `blocked` and move to the next actionable task.
5. Do not loop indefinitely on the same bug.
6. Before declaring completion, run a final review and verify there are no forgotten `pending` tasks.

Session isolation:
- Use `TASK_SESSION_ID` to isolate task state by session.
- Never reuse another session's task file unless explicitly instructed.

Preferred workflow:
1. Initialize a task session if none exists.
2. Read current task list.
3. Choose one actionable task.
4. Work on it.
5. Update state.
6. Review remaining tasks before finishing.

Operational commands:
- Initialize: `python3 tools/task_state.py init --session "$TASK_SESSION_ID" --objective "<objective>" --task T1="<task>"`
- Inspect before edits: `python3 tools/task_state.py show --session "$TASK_SESSION_ID"`
- Start task: `python3 tools/task_state.py start --session "$TASK_SESSION_ID" --task T1`
- Record failure attempt: `python3 tools/task_state.py fail --session "$TASK_SESSION_ID" --task T1 --text "<why failed>"`
- Mark done: `python3 tools/task_state.py done --session "$TASK_SESSION_ID" --task T1 --text "<what changed>"`
- Final review: `python3 tools/task_state.py review --session "$TASK_SESSION_ID"`
