"""Ollama API client for generating commit messages."""

import httpx

OLLAMA_DEFAULT_URL = "http://localhost:11434"

COMMIT_SYSTEM_PROMPT = """\
You are an expert developer writing Git commit messages.
Follow the Conventional Commits specification: https://www.conventionalcommits.org

Format: <type>(<optional scope>): <short description>

Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build

Rules:
- First line max 72 characters
- Use imperative mood ("add", not "added")
- Be specific and concise
- No period at the end of the first line
- Optionally add a blank line + body for context if the change is complex

Return ONLY the commit message, no explanation or markdown fences.\
"""


def _build_prompt(diff: str, files: list[str], hint: str | None) -> str:
    files_summary = "\n".join(f"  - {f}" for f in files) if files else "  (none)"
    hint_section = f"\nUser hint: {hint}" if hint else ""
    # Keep diff under ~6000 chars to stay within most model context windows
    truncated_diff = diff[:6000] + "\n[diff truncated...]" if len(diff) > 6000 else diff
    return (
        f"Staged files:\n{files_summary}{hint_section}\n\n"
        f"Git diff:\n```diff\n{truncated_diff}\n```\n\n"
        "Write a Conventional Commit message for this change:"
    )


def generate_messages(
    diff: str,
    files: list[str],
    *,
    model: str = "mistral",
    base_url: str = OLLAMA_DEFAULT_URL,
    count: int = 1,
    hint: str | None = None,
    timeout: float = 60.0,
) -> list[str]:
    prompt = _build_prompt(diff, files, hint)
    messages = []

    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        for _ in range(count):
            response = client.post(
                "/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": COMMIT_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.4 if count == 1 else 0.7},
                },
            )
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()
            # Strip markdown fences if the model added them anyway
            if content.startswith("```"):
                content = "\n".join(
                    line for line in content.splitlines()
                    if not line.startswith("```")
                ).strip()
            messages.append(content)

    return messages


def list_models(base_url: str = OLLAMA_DEFAULT_URL) -> list[str]:
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        response = client.get("/api/tags")
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]
