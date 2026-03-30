#!/usr/bin/env python3

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


STATE_DIR = Path(".task_state")
DEFAULT_MAX_RETRY = 3
VALID_STATUS = {"pending", "in_progress", "blocked", "done", "skipped"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def session_file(session_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in session_id)
    return STATE_DIR / f"{safe}.json"


def make_task(task_id: str, title: str) -> Dict[str, Any]:
    return {
        "id": task_id,
        "title": title,
        "status": "pending",  # pending | in_progress | blocked | done | skipped
        "retry_count": 0,
        "blocked_reason": None,
        "notes": [],
        "updated_at": now_iso(),
    }


def load_state(session_id: str) -> Dict[str, Any]:
    path = session_file(session_id)
    if not path.exists():
        raise FileNotFoundError(
            f"No task state found for session '{session_id}'. "
            f"Initialize first with: python3 tools/task_state.py init --session {session_id} ..."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def atomic_save(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def save_state(session_id: str, data: Dict[str, Any]) -> None:
    ensure_state_dir()
    path = session_file(session_id)
    atomic_save(path, data)


def summarize(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {"pending": 0, "in_progress": 0, "blocked": 0, "done": 0, "skipped": 0}
    for t in tasks:
        out[t["status"]] = out.get(t["status"], 0) + 1
    return out


def touch_state(data: Dict[str, Any]) -> None:
    data["updated_at"] = now_iso()


def validate_unique_in_progress(tasks: List[Dict[str, Any]]) -> None:
    in_progress = [t for t in tasks if t["status"] == "in_progress"]
    if len(in_progress) > 1:
        ids = ", ".join(t["id"] for t in in_progress)
        raise ValueError(f"State invalid: more than one in_progress task: {ids}")


def find_task(tasks: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    for t in tasks:
        if t["id"] == task_id:
            return t
    raise KeyError(f"Task not found: {task_id}")


def add_note(task: Dict[str, Any], text: str) -> None:
    task.setdefault("notes", []).append(f"[{now_iso()}] {text}")
    task["updated_at"] = now_iso()


def set_status(tasks: List[Dict[str, Any]], task: Dict[str, Any], status: str) -> None:
    if status not in VALID_STATUS:
        raise ValueError(f"Invalid status: {status}")
    if status == "in_progress":
        for t in tasks:
            if t["id"] != task["id"] and t["status"] == "in_progress":
                t["status"] = "pending"
                t["updated_at"] = now_iso()
                t.setdefault("notes", []).append(
                    f"[{now_iso()}] Auto-moved to pending because '{task['id']}' was started."
                )
    task["status"] = status
    task["updated_at"] = now_iso()


def print_state(data: Dict[str, Any]) -> None:
    tasks = data.get("tasks", [])
    summary = summarize(tasks)
    print(f"session:   {data.get('session_id')}")
    print(f"objective: {data.get('objective')}")
    print(f"created:   {data.get('created_at')}")
    print(f"updated:   {data.get('updated_at')}")
    print(
        "summary:   "
        f"pending={summary['pending']} "
        f"in_progress={summary['in_progress']} "
        f"blocked={summary['blocked']} "
        f"done={summary['done']} "
        f"skipped={summary['skipped']}"
    )
    print()
    for t in tasks:
        line = f"- {t['id']} [{t['status']}] retry={t.get('retry_count', 0)} title={t['title']}"
        if t.get("blocked_reason"):
            line += f" blocked_reason={t['blocked_reason']}"
        print(line)
        if t.get("notes"):
            print(f"  last_note: {t['notes'][-1]}")


def init_session(args: argparse.Namespace) -> int:
    ensure_state_dir()
    path = session_file(args.session)
    if path.exists() and not args.force:
        print(f"Session already exists: {path}", file=sys.stderr)
        return 1

    tasks: List[Dict[str, Any]] = []
    for raw in args.task:
        if "=" not in raw:
            print(f"Invalid --task format: {raw!r}. Expected ID=Title", file=sys.stderr)
            return 1
        task_id, title = raw.split("=", 1)
        tasks.append(make_task(task_id.strip(), title.strip()))

    if len({t["id"] for t in tasks}) != len(tasks):
        print("Duplicate task IDs found in --task arguments.", file=sys.stderr)
        return 1

    ts = now_iso()
    data = {
        "session_id": args.session,
        "objective": args.objective,
        "created_at": ts,
        "updated_at": ts,
        "max_retry": args.max_retry,
        "tasks": tasks,
    }
    save_state(args.session, data)
    print(f"Initialized: {session_file(args.session)}")
    print_state(data)
    return 0


def show_session(args: argparse.Namespace) -> int:
    data = load_state(args.session)
    validate_unique_in_progress(data.get("tasks", []))
    print_state(data)
    return 0


def start_task(args: argparse.Namespace) -> int:
    data = load_state(args.session)
    tasks = data.get("tasks", [])
    validate_unique_in_progress(tasks)

    if args.task:
        task = find_task(tasks, args.task)
    else:
        candidates = [t for t in tasks if t["status"] == "pending"]
        if not candidates:
            print("No pending task to start.", file=sys.stderr)
            return 1
        task = candidates[0]

    if task["status"] in {"done", "skipped"}:
        print(f"Task {task['id']} is {task['status']}, cannot start.", file=sys.stderr)
        return 1

    set_status(tasks, task, "in_progress")
    add_note(task, args.text or "Task started")
    touch_state(data)
    save_state(args.session, data)
    print(f"Started task: {task['id']}")
    return 0


def note_task(args: argparse.Namespace) -> int:
    data = load_state(args.session)
    tasks = data.get("tasks", [])
    validate_unique_in_progress(tasks)
    task = find_task(tasks, args.task)
    add_note(task, args.text)
    touch_state(data)
    save_state(args.session, data)
    print(f"Noted task: {task['id']}")
    return 0


def fail_task(args: argparse.Namespace) -> int:
    data = load_state(args.session)
    tasks = data.get("tasks", [])
    validate_unique_in_progress(tasks)
    task = find_task(tasks, args.task)
    max_retry = int(data.get("max_retry", DEFAULT_MAX_RETRY))

    task["retry_count"] = int(task.get("retry_count", 0)) + 1
    add_note(task, f"FAILED attempt {task['retry_count']}: {args.text}")

    if task["retry_count"] >= max_retry:
        task["blocked_reason"] = args.reason or f"Failed validation {task['retry_count']} times"
        set_status(tasks, task, "blocked")
        add_note(task, "Auto-blocked after reaching max retry")
        print(f"Task blocked: {task['id']}")
    else:
        set_status(tasks, task, "in_progress")
        print(f"Task failed attempt recorded: {task['id']} retry={task['retry_count']}/{max_retry}")

    touch_state(data)
    save_state(args.session, data)
    return 0


def done_task(args: argparse.Namespace) -> int:
    data = load_state(args.session)
    tasks = data.get("tasks", [])
    validate_unique_in_progress(tasks)
    task = find_task(tasks, args.task)
    if args.text:
        add_note(task, args.text)
    set_status(tasks, task, "done")
    task["blocked_reason"] = None
    touch_state(data)
    save_state(args.session, data)
    print(f"Done task: {task['id']}")
    return 0


def block_task(args: argparse.Namespace) -> int:
    data = load_state(args.session)
    tasks = data.get("tasks", [])
    validate_unique_in_progress(tasks)
    task = find_task(tasks, args.task)
    task["blocked_reason"] = args.reason
    if args.text:
        add_note(task, args.text)
    set_status(tasks, task, "blocked")
    touch_state(data)
    save_state(args.session, data)
    print(f"Blocked task: {task['id']}")
    return 0


def review_session(args: argparse.Namespace) -> int:
    data = load_state(args.session)
    tasks = data.get("tasks", [])
    validate_unique_in_progress(tasks)
    print_state(data)
    pending = [t["id"] for t in tasks if t["status"] == "pending"]
    blocked = [t["id"] for t in tasks if t["status"] == "blocked"]
    print()
    if pending:
        print(f"remaining_pending: {', '.join(pending)}")
    else:
        print("remaining_pending: none")
    if blocked:
        print(f"remaining_blocked: {', '.join(blocked)}")
    else:
        print("remaining_blocked: none")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Local JSON task state manager")
    sub = p.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Initialize task session")
    p_init.add_argument("--session", required=True)
    p_init.add_argument("--objective", required=True)
    p_init.add_argument("--task", action="append", default=[], help="Format: ID=Title")
    p_init.add_argument("--max-retry", type=int, default=DEFAULT_MAX_RETRY)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=init_session)

    p_show = sub.add_parser("show", help="Show task session")
    p_show.add_argument("--session", required=True)
    p_show.set_defaults(func=show_session)

    p_start = sub.add_parser("start", help="Start one task")
    p_start.add_argument("--session", required=True)
    p_start.add_argument("--task", help="If omitted, start first pending task")
    p_start.add_argument("--text", default="")
    p_start.set_defaults(func=start_task)

    p_note = sub.add_parser("note", help="Append a note to a task")
    p_note.add_argument("--session", required=True)
    p_note.add_argument("--task", required=True)
    p_note.add_argument("--text", required=True)
    p_note.set_defaults(func=note_task)

    p_fail = sub.add_parser("fail", help="Record failed attempt; auto-block on max retry")
    p_fail.add_argument("--session", required=True)
    p_fail.add_argument("--task", required=True)
    p_fail.add_argument("--text", required=True)
    p_fail.add_argument("--reason", default="")
    p_fail.set_defaults(func=fail_task)

    p_done = sub.add_parser("done", help="Mark task done")
    p_done.add_argument("--session", required=True)
    p_done.add_argument("--task", required=True)
    p_done.add_argument("--text", default="")
    p_done.set_defaults(func=done_task)

    p_block = sub.add_parser("block", help="Mark task blocked")
    p_block.add_argument("--session", required=True)
    p_block.add_argument("--task", required=True)
    p_block.add_argument("--reason", required=True)
    p_block.add_argument("--text", default="")
    p_block.set_defaults(func=block_task)

    p_review = sub.add_parser("review", help="Review remaining pending/blocked tasks")
    p_review.add_argument("--session", required=True)
    p_review.set_defaults(func=review_session)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help(sys.stderr)
        return 1
    try:
        return int(args.func(args))
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
