"""Unit tests for the Ollama client (prompt building only — no network calls)."""

from ollama_commit.ollama import _build_prompt


def test_build_prompt_includes_files():
    prompt = _build_prompt("diff --git a/foo.py", ["foo.py"], hint=None)
    assert "foo.py" in prompt
    assert "diff --git a/foo.py" in prompt


def test_build_prompt_includes_hint():
    prompt = _build_prompt("diff", ["a.py"], hint="refactoring auth")
    assert "refactoring auth" in prompt


def test_build_prompt_truncates_large_diff():
    large_diff = "x" * 7000
    prompt = _build_prompt(large_diff, [], hint=None)
    assert "[diff truncated...]" in prompt
    assert len(prompt) < 8000
