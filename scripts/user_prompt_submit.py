#!/usr/bin/env python3
"""Add fail-open router guidance to Codex prompt submissions."""

import json
import sys
from pathlib import Path

ADDITIONAL_CONTEXT = (
    "Apply the codex-auto-model-router Skill when this request falls within its scope. "
    "Honor its project-disable setting, exclusions, benefit gate, and the active Codex mode. "
    "Treat a route as advice until a leaf is actually dispatched; the hook cannot change "
    "the model of this conversation."
)


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import router_lite

        event = json.load(sys.stdin)
        if not isinstance(event, dict) or event.get("hook_event_name") != "UserPromptSubmit":
            return 0
        cwd = event.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return 0
        skill_path = Path(__file__).resolve().parents[1] / "SKILL.md"
        if not skill_path.is_file():
            return 0
        state = router_lite._project_skill_state(cwd, skill_path)
        if not state["enabled"]:
            return 0
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ADDITIONAL_CONTEXT,
            }
        }, ensure_ascii=False))
    except Exception:
        # A prompt hook must never block ordinary work.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
