"""Tests for hook.py - install/uninstall git hook."""

import stat
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ollama_commit.hook import find_git_dir, install_hook, uninstall_hook


class TestFindGitDir:
    def test_finds_git_dir_in_cwd(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("ollama_commit.hook.Path.cwd", return_value=tmp_path):
            result = find_git_dir()

        assert result == git_dir

    def test_finds_git_dir_in_parent(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "sub" / "dir"
        subdir.mkdir(parents=True)

        with patch("ollama_commit.hook.Path.cwd", return_value=subdir):
            result = find_git_dir()

        assert result == git_dir

    def test_raises_when_not_in_repo(self, tmp_path):
        with patch("ollama_commit.hook.Path.cwd", return_value=tmp_path):
            with pytest.raises(FileNotFoundError, match="Not inside a Git repository"):
                find_git_dir()


class TestInstallHook:
    def _make_git_dir(self, tmp_path: Path) -> Path:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        return git_dir

    def test_installs_hook_file(self, tmp_path):
        git_dir = self._make_git_dir(tmp_path)

        with patch("ollama_commit.hook.find_git_dir", return_value=git_dir):
            install_hook()

        hook_path = git_dir / "hooks" / "prepare-commit-msg"
        assert hook_path.exists()
        assert "ollama-commit" in hook_path.read_text()

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod exec bit not meaningful on Windows")
    def test_hook_is_executable(self, tmp_path):
        git_dir = self._make_git_dir(tmp_path)

        with patch("ollama_commit.hook.find_git_dir", return_value=git_dir):
            install_hook()

        hook_path = git_dir / "hooks" / "prepare-commit-msg"
        mode = hook_path.stat().st_mode
        assert mode & stat.S_IXUSR

    def test_refuses_overwrite_without_force(self, tmp_path):
        git_dir = self._make_git_dir(tmp_path)
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "prepare-commit-msg"
        hook_path.write_text("existing hook")

        with patch("ollama_commit.hook.find_git_dir", return_value=git_dir):
            with pytest.raises(SystemExit):
                install_hook(force=False)

    def test_overwrites_with_force(self, tmp_path):
        git_dir = self._make_git_dir(tmp_path)
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "prepare-commit-msg"
        hook_path.write_text("old hook")

        with patch("ollama_commit.hook.find_git_dir", return_value=git_dir):
            install_hook(force=True)

        assert "ollama-commit" in hook_path.read_text()

    def test_creates_hooks_dir_if_missing(self, tmp_path):
        git_dir = self._make_git_dir(tmp_path)

        with patch("ollama_commit.hook.find_git_dir", return_value=git_dir):
            install_hook()

        assert (git_dir / "hooks").is_dir()


class TestUninstallHook:
    def test_removes_existing_hook(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "prepare-commit-msg"
        hook_path.write_text("hook content")

        with patch("ollama_commit.hook.find_git_dir", return_value=git_dir):
            uninstall_hook()

        assert not hook_path.exists()

    def test_no_error_when_hook_missing(self, tmp_path, capsys):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("ollama_commit.hook.find_git_dir", return_value=git_dir):
            uninstall_hook()

        captured = capsys.readouterr()
        assert "No hook installed" in captured.err
