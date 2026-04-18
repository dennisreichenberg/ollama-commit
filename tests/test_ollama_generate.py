"""Tests for ollama.py - generate_messages and list_models."""

from unittest.mock import MagicMock, patch

from ollama_commit.ollama import _build_prompt, generate_messages, list_models


class TestBuildPrompt:
    def test_no_files_shows_none(self):
        prompt = _build_prompt("diff", [], hint=None)
        assert "(none)" in prompt

    def test_no_hint_omits_hint_section(self):
        prompt = _build_prompt("diff", ["a.py"], hint=None)
        assert "User hint" not in prompt

    def test_with_hint(self):
        prompt = _build_prompt("diff", ["a.py"], hint="auth refactor")
        assert "auth refactor" in prompt

    def test_diff_not_truncated_when_short(self):
        short_diff = "x" * 100
        prompt = _build_prompt(short_diff, [], hint=None)
        assert "[diff truncated...]" not in prompt

    def test_diff_truncated_at_6000_chars(self):
        big_diff = "y" * 7000
        prompt = _build_prompt(big_diff, [], hint=None)
        assert "[diff truncated...]" in prompt

    def test_multiple_files_listed(self):
        prompt = _build_prompt("diff", ["a.py", "b.py", "c.py"], hint=None)
        assert "a.py" in prompt
        assert "b.py" in prompt
        assert "c.py" in prompt


def _make_mock_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {"message": {"content": content}}
    resp.raise_for_status = MagicMock()
    return resp


class TestGenerateMessages:
    def test_returns_single_message(self):
        mock_resp = _make_mock_response("feat: add login")
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            result = generate_messages("diff", ["main.py"])

        assert result == ["feat: add login"]
        mock_client.post.assert_called_once()

    def test_returns_multiple_messages(self):
        responses = [_make_mock_response(f"feat: msg {i}") for i in range(3)]
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = responses

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            result = generate_messages("diff", ["a.py"], count=3)

        assert len(result) == 3

    def test_strips_markdown_fences(self):
        content = "```\nfeat: add feature\n```"
        mock_resp = _make_mock_response(content)
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            result = generate_messages("diff", [])

        assert result[0] == "feat: add feature"
        assert "```" not in result[0]

    def test_passes_model_and_hint(self):
        mock_resp = _make_mock_response("fix: bug")
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            generate_messages("diff", [], model="llama3", hint="auth")

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs.kwargs["json"]
        assert payload["model"] == "llama3"
        user_content = payload["messages"][1]["content"]
        assert "auth" in user_content

    def test_single_count_uses_lower_temperature(self):
        mock_resp = _make_mock_response("feat: x")
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            generate_messages("diff", [], count=1)

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["options"]["temperature"] == 0.4

    def test_multi_count_uses_higher_temperature(self):
        responses = [_make_mock_response("feat: x"), _make_mock_response("feat: y")]
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = responses

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            generate_messages("diff", [], count=2)

        payload = mock_client.post.call_args_list[0].kwargs["json"]
        assert payload["options"]["temperature"] == 0.7


class TestListModels:
    def test_returns_model_names(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "mistral"}, {"name": "llama3"}]}
        mock_resp.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            result = list_models()

        assert result == ["mistral", "llama3"]

    def test_returns_empty_list_when_no_models(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("ollama_commit.ollama.httpx.Client", return_value=mock_client):
            result = list_models()

        assert result == []
