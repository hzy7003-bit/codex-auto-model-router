#!/usr/bin/env python3
"""Install the opt-in Codex user prompt hook without replacing other hooks."""

import argparse
import copy
import json
import os
import shlex
import stat
import sys
import tempfile
from pathlib import Path


def _commands(script_path):
    script = Path(script_path).resolve()
    posix_command = f"python3 {shlex.quote(str(script))}"
    windows_python = sys.executable if os.name == "nt" else "python"
    windows_command = f'"{windows_python}" "{script}"' if os.name == "nt" else f'python "{script}"'
    return posix_command, windows_command


def _is_owned(handler, commands):
    return (
        isinstance(handler, dict)
        and handler.get("type") == "command"
        and any(handler.get(field) in commands for field in ("command", "commandWindows"))
    )


def _install(data, commands):
    if not isinstance(data, dict):
        raise ValueError("hooks.json must contain a JSON object")
    original = copy.deepcopy(data)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks.json 'hooks' must contain a JSON object")
    groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(groups, list):
        raise ValueError("hooks.json UserPromptSubmit must contain a JSON array")

    retained_groups = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            retained_groups.append(group)
            continue
        retained_handlers = [
            handler for handler in group["hooks"] if not _is_owned(handler, commands)
        ]
        if retained_handlers:
            updated_group = dict(group)
            updated_group["hooks"] = retained_handlers
            retained_groups.append(updated_group)
        elif not group["hooks"]:
            retained_groups.append(group)

    posix_command, windows_command = commands
    retained_groups.append({
        "hooks": [{
            "type": "command",
            "command": posix_command,
            "commandWindows": windows_command,
            "timeout": 5,
        }]
    })
    hooks["UserPromptSubmit"] = retained_groups
    return data, data != original


def install(codex_home, script_path):
    config_path = Path(codex_home).expanduser() / "hooks.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.is_symlink() or config_path.is_dir():
        raise ValueError("refusing to replace a non-regular hooks.json target")

    existed = config_path.exists()
    old_mode = stat.S_IMODE(config_path.stat().st_mode) if existed else None
    if existed:
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read existing hooks.json: {type(exc).__name__}") from exc
    else:
        data = {}

    updated, changed = _install(data, _commands(script_path))
    if not changed:
        return False

    fd, temporary_name = tempfile.mkstemp(prefix=".hooks.json.", dir=config_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(updated, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if old_mode is not None:
            os.chmod(temporary_name, old_mode)
        os.replace(temporary_name, config_path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", required=True)
    parser.add_argument("--script", default=str(Path(__file__).with_name("user_prompt_submit.py")))
    args = parser.parse_args(argv)
    install(args.codex_home, args.script)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
