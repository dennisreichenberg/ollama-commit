"""Git prepare-commit-msg hook installer."""

import os
import stat
import sys
from pathlib import Path

HOOK_TEMPLATE = """\
#!/usr/bin/env bash
# ollama-commit: auto-fill commit message via local LLM
# Installed by: ollama-commit install-hook
COMMIT_MSG_FILE="$1"
COMMIT_SOURCE="$2"

# Only run for empty commits (no -m flag, no template, no merge)
if [ -z "$COMMIT_SOURCE" ]; then
    ollama-commit --yes --dry-run > /tmp/ollama_commit_msg 2>/dev/null
    if [ $? -eq 0 ] && [ -s /tmp/ollama_commit_msg ]; then
        cat /tmp/ollama_commit_msg > "$COMMIT_MSG_FILE"
    fi
fi
"""


def find_git_dir() -> Path:
    path = Path.cwd()
    for candidate in [path, *path.parents]:
        git_dir = candidate / ".git"
        if git_dir.is_dir():
            return git_dir
    raise FileNotFoundError("Not inside a Git repository.")


def install_hook(force: bool = False) -> None:
    git_dir = find_git_dir()
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "prepare-commit-msg"

    if hook_path.exists() and not force:
        print(f"Hook already exists at {hook_path}. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    hook_path.write_text(HOOK_TEMPLATE)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Hook installed at {hook_path}")


def uninstall_hook() -> None:
    git_dir = find_git_dir()
    hook_path = git_dir / "hooks" / "prepare-commit-msg"
    if not hook_path.exists():
        print("No hook installed.", file=sys.stderr)
        return
    hook_path.unlink()
    print(f"Hook removed: {hook_path}")
