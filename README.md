# ollama-commit

> Generate Git commit messages using local LLMs via [Ollama](https://ollama.com) — no cloud, no API keys, no data leaving your machine.

```
$ git add src/auth.py
$ ollama-commit

Staged files (1): src/auth.py
Querying mistral via http://localhost:11434…

╭─ Suggested commit message ──────────────────────────────╮
│ feat(auth): add JWT refresh token rotation               │
╰──────────────────────────────────────────────────────────╯

Commit with this message? [Y/n]:
```

## Features

- **Local-first** — uses Ollama, everything runs on your machine
- **Conventional Commits** — output follows the [Conventional Commits](https://www.conventionalcommits.org) spec
- **Multiple suggestions** — get up to 5 variants and pick the best one (`-n 3`)
- **Context hints** — give the model a nudge (`--hint "refactoring auth"`)
- **Git hook** — auto-fill the commit message editor on every `git commit`
- **Interactive or silent** — `--yes` flag for scripting and CI

## Requirements

- Python ≥ 3.10
- [Ollama](https://ollama.com) running locally (`ollama serve`)
- At least one model pulled: `ollama pull mistral`

## Installation

```bash
pip install ollama-commit
```

Or for development:

```bash
git clone https://github.com/dennisreichenberg/ollama-commit
cd ollama-commit
pip install -e ".[dev]"
```

## Usage

### Basic

```bash
# Stage your changes, then:
git add .
ollama-commit
```

### Get multiple suggestions

```bash
ollama-commit --count 3
```

### Use a different model

```bash
ollama-commit --model llama3
ollama-commit --model codellama
```

### Add a context hint

```bash
ollama-commit --hint "this fixes the login redirect bug"
```

### Auto-commit without prompting

```bash
ollama-commit --yes
```

### Dry run (print only, do not commit)

```bash
ollama-commit --dry-run
```

### List available models

```bash
ollama-commit models
```

### Git hook (auto-fill on `git commit`)

```bash
# Install hook in current repo
ollama-commit install-hook

# Remove hook
ollama-commit uninstall-hook
```

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--model` | `-m` | `mistral` | Ollama model to use |
| `--host` | | `http://localhost:11434` | Ollama base URL |
| `--count` | `-n` | `1` | Number of suggestions (1–5) |
| `--hint` | `-h` | | Optional hint for the model |
| `--yes` | `-y` | | Auto-accept and commit |
| `--dry-run` | | | Print message, don't commit |

## Recommended models

| Model | Size | Notes |
|-------|------|-------|
| `mistral` | 4.1 GB | Best quality/speed for commits |
| `llama3` | 4.7 GB | Excellent for English commits |
| `codellama` | 3.8 GB | Code-focused, good for technical diffs |
| `phi3` | 2.2 GB | Fast, good quality for small models |
| `qwen2.5-coder` | 4.7 GB | Strong code understanding |

## How it works

1. Reads `git diff --staged` from the current repository
2. Sends the diff (and optional hint) to your local Ollama model
3. Receives a Conventional Commit formatted message
4. Optionally commits with that message after confirmation

## Configuration via environment variables

```bash
export OLLAMA_COMMIT_MODEL=llama3
export OLLAMA_COMMIT_HOST=http://localhost:11434
```

_(Env var support coming in v0.2)_

## License

MIT — see [LICENSE](LICENSE)

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
