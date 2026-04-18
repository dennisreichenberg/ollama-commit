"""Tests for git.py - staged diff and commit operations."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ollama_commit.git import DiffInfo, GitError, commit, get_staged_diff


class TestGetStagedDiff:
    def test_returns_diff_info(self):
        def fake_check_output(cmd, **kwargs):
            if "--name-only" in cmd:
                return "src/foo.py\nsrc/bar.py\n"
            return "diff --git a/src/foo.py b/src/foo.py\n+added line\n"

        with patch("subprocess.check_output", side_effect=fake_check_output):
            info = get_staged_diff()

        assert isinstance(info, DiffInfo)
        assert "foo.py" in info.diff
        assert "src/foo.py" in info.staged_files
        assert "src/bar.py" in info.staged_files

    def test_empty_staged_files(self):
        def fake_check_output(cmd, **kwargs):
            if "--name-only" in cmd:
                return "\n"
            return ""

        with patch("subprocess.check_output", side_effect=fake_check_output):
            info = get_staged_diff()

        assert info.staged_files == []
        assert info.diff == ""

    def test_raises_git_error_on_called_process_error(self):
        err = subprocess.CalledProcessError(1, "git", stderr="fatal: not a repo")
        with patch("subprocess.check_output", side_effect=err):
            with pytest.raises(GitError, match="git command failed"):
                get_staged_diff()

    def test_raises_git_error_when_git_not_found(self):
        with patch("subprocess.check_output", side_effect=FileNotFoundError):
            with pytest.raises(GitError, match="git not found"):
                get_staged_diff()

    def test_filters_empty_lines_from_file_list(self):
        def fake_check_output(cmd, **kwargs):
            if "--name-only" in cmd:
                return "a.py\n\nb.py\n\n"
            return "some diff"

        with patch("subprocess.check_output", side_effect=fake_check_output):
            info = get_staged_diff()

        assert info.staged_files == ["a.py", "b.py"]


class TestCommit:
    def test_returns_output_on_success(self):
        with patch("subprocess.check_output", return_value="[main abc1234] feat: add thing\n"):
            result = commit("feat: add thing")

        assert result == "[main abc1234] feat: add thing"

    def test_raises_git_error_on_failure(self):
        err = subprocess.CalledProcessError(1, "git", output="nothing to commit")
        with patch("subprocess.check_output", side_effect=err):
            with pytest.raises(GitError, match="nothing to commit"):
                commit("test: msg")

    def test_strips_trailing_whitespace(self):
        with patch("subprocess.check_output", return_value="[main 0000000] fix: bug\n\n"):
            result = commit("fix: bug")

        assert not result.endswith("\n")
