"""Tests for cli.py - CLI commands via CliRunner."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from click.testing import CliRunner

from ollama_commit.cli import main
from ollama_commit.git import DiffInfo, GitError


_SENTINEL = object()


def _diff_info(files=_SENTINEL, diff="diff content"):
    if files is _SENTINEL:
        files = ["src/main.py"]
    return DiffInfo(diff=diff, staged_files=files)


def _mock_generate(messages=None):
    if messages is None:
        messages = ["feat: add feature"]

    def _gen(*args, **kwargs):
        return messages

    return _gen


class TestMainCommand:
    def test_exits_when_no_staged_files(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info(files=[])):
            result = runner.invoke(main, [])
        assert result.exit_code == 1
        assert "No staged changes" in result.output

    def test_exits_on_git_error(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.get_staged_diff", side_effect=GitError("not a repo")):
            result = runner.invoke(main, [])
        assert result.exit_code == 1
        assert "Git error" in result.output

    def test_dry_run_does_not_commit(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info()), \
             patch("ollama_commit.cli.generate_messages", _mock_generate()), \
             patch("ollama_commit.cli.commit") as mock_commit:
            result = runner.invoke(main, ["--dry-run", "--yes"])
        assert result.exit_code == 0
        mock_commit.assert_not_called()
        assert "--dry-run" in result.output or "not committing" in result.output

    def test_yes_flag_commits_without_prompt(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info()), \
             patch("ollama_commit.cli.generate_messages", _mock_generate()), \
             patch("ollama_commit.cli.commit", return_value="[main abc] feat: add feature"):
            result = runner.invoke(main, ["--yes"])
        assert result.exit_code == 0
        assert "Committed" in result.output

    def test_connect_error_exits_with_message(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info()), \
             patch("ollama_commit.cli.generate_messages",
                   side_effect=httpx.ConnectError("connection refused")):
            result = runner.invoke(main, ["--yes"])
        assert result.exit_code == 1
        assert "Cannot connect" in result.output

    def test_http_status_error_exits(self):
        runner = CliRunner()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info()), \
             patch("ollama_commit.cli.generate_messages",
                   side_effect=httpx.HTTPStatusError(
                       "err", request=MagicMock(), response=mock_response
                   )):
            result = runner.invoke(main, ["--yes"])
        assert result.exit_code == 1
        assert "Ollama API error" in result.output

    def test_commit_error_exits(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info()), \
             patch("ollama_commit.cli.generate_messages", _mock_generate()), \
             patch("ollama_commit.cli.commit", side_effect=GitError("nothing to commit")):
            result = runner.invoke(main, ["--yes"])
        assert result.exit_code == 1
        assert "Commit failed" in result.output

    def test_count_clamped_to_1_minimum(self):
        runner = CliRunner()
        captured_kwargs = {}

        def fake_generate(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return ["feat: x"]

        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info()), \
             patch("ollama_commit.cli.generate_messages", fake_generate), \
             patch("ollama_commit.cli.commit", return_value="done"):
            runner.invoke(main, ["--count", "0", "--yes"])

        assert captured_kwargs.get("count", 1) >= 1

    def test_count_clamped_to_5_maximum(self):
        runner = CliRunner()
        captured_kwargs = {}

        def fake_generate(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return ["feat: x"]

        with patch("ollama_commit.cli.get_staged_diff", return_value=_diff_info()), \
             patch("ollama_commit.cli.generate_messages", fake_generate), \
             patch("ollama_commit.cli.commit", return_value="done"):
            runner.invoke(main, ["--count", "10", "--yes"])

        assert captured_kwargs.get("count", 5) <= 5


class TestModelsCommand:
    def test_lists_models(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.list_models", return_value=["mistral", "llama3"]):
            result = runner.invoke(main, ["models"])
        assert result.exit_code == 0
        assert "mistral" in result.output
        assert "llama3" in result.output

    def test_shows_message_when_no_models(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.list_models", return_value=[]):
            result = runner.invoke(main, ["models"])
        assert result.exit_code == 0
        assert "No models" in result.output

    def test_connect_error(self):
        runner = CliRunner()
        with patch("ollama_commit.cli.list_models",
                   side_effect=httpx.ConnectError("refused")):
            result = runner.invoke(main, ["models"])
        assert result.exit_code == 1
        assert "Cannot connect" in result.output


class TestInstallHookCommand:
    def test_install_hook_called(self):
        runner = CliRunner()
        with patch("ollama_commit.hook.install_hook") as mock_install:
            result = runner.invoke(main, ["install-hook"])
        mock_install.assert_called_once_with(force=False)

    def test_install_hook_with_force(self):
        runner = CliRunner()
        with patch("ollama_commit.hook.install_hook") as mock_install:
            runner.invoke(main, ["install-hook", "--force"])
        mock_install.assert_called_once_with(force=True)


class TestUninstallHookCommand:
    def test_uninstall_hook_called(self):
        runner = CliRunner()
        with patch("ollama_commit.hook.uninstall_hook") as mock_uninstall:
            runner.invoke(main, ["uninstall-hook"])
        mock_uninstall.assert_called_once()
