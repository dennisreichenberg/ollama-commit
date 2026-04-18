# Contributing to ollama-commit

Thank you for considering a contribution! Here's how to get started.

## Setup

```bash
git clone https://github.com/dennisreichenberg/ollama-commit
cd ollama-commit
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -v
```

## Linting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Pull requests

- Keep PRs focused — one feature or fix per PR
- Add tests for new behavior
- Follow Conventional Commits for commit messages (we use this tool on itself!)
- Update `README.md` if you add or change CLI options

## Reporting bugs

Open an issue with:
- OS and Python version
- Ollama version and model used
- The command you ran
- The error output

## Ideas for contributions

- Environment variable config (`OLLAMA_COMMIT_MODEL`, `OLLAMA_COMMIT_HOST`)
- Config file support (`~/.config/ollama-commit/config.toml`)
- Support for `--amend` (reword last commit)
- Language option (`--lang de` for German messages)
- Token count estimation before sending diff
