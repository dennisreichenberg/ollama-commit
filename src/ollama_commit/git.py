"""Git operations for reading staged diff and committing."""

import subprocess
from dataclasses import dataclass


class GitError(Exception):
    pass


@dataclass
class DiffInfo:
    diff: str
    staged_files: list[str]


def get_staged_diff() -> DiffInfo:
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--staged", "--no-color"],
            stderr=subprocess.PIPE,
            text=True,
        )
        files_output = subprocess.check_output(
            ["git", "diff", "--staged", "--name-only"],
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise GitError(f"git command failed: {e.stderr.strip()}") from e
    except FileNotFoundError as e:
        raise GitError("git not found in PATH") from e

    staged_files = [f for f in files_output.strip().splitlines() if f]
    return DiffInfo(diff=diff, staged_files=staged_files)


def commit(message: str) -> str:
    try:
        result = subprocess.check_output(
            ["git", "commit", "-m", message],
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.strip()
    except subprocess.CalledProcessError as e:
        raise GitError(e.output.strip()) from e
