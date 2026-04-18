"""CLI entry point for ollama-commit."""

import sys

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from .git import GitError, commit, get_staged_diff
from .ollama import OLLAMA_DEFAULT_URL, generate_messages, list_models

console = Console()
err = Console(stderr=True)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--model", "-m", default="mistral", show_default=True, help="Ollama model to use.")
@click.option("--host", default=OLLAMA_DEFAULT_URL, show_default=True, help="Ollama base URL.")
@click.option("--count", "-n", default=1, show_default=True, help="Number of suggestions (1–5).")
@click.option("--hint", "-h", default=None, help="Optional context hint for the model.")
@click.option("--yes", "-y", is_flag=True, help="Auto-accept the first suggestion and commit.")
@click.option("--dry-run", is_flag=True, help="Print message but do not commit.")
def main(  # noqa: PLR0913
    ctx: click.Context,
    model: str,
    host: str,
    count: int,
    hint: str | None,
    yes: bool,
    dry_run: bool,
) -> None:
    """Generate a Git commit message using a local Ollama LLM.

    Run inside a git repository with staged changes.

    \b
    Examples:
      ollama-commit
      ollama-commit --model llama3 --count 3
      ollama-commit --hint "refactoring auth module" --yes
    """
    if ctx.invoked_subcommand is not None:
        return

    count = max(1, min(count, 5))

    # 1. Read staged diff
    try:
        diff_info = get_staged_diff()
    except GitError as e:
        err.print(f"[red]Git error:[/red] {e}")
        sys.exit(1)

    if not diff_info.staged_files:
        err.print(
            "[yellow]No staged changes found.[/yellow] Stage your changes with `git add` first."
        )
        sys.exit(1)

    files_str = ", ".join(diff_info.staged_files)
    console.print(f"[dim]Staged files ({len(diff_info.staged_files)}):[/dim] {files_str}")
    console.print(f"[dim]Querying[/dim] [bold cyan]{model}[/bold cyan] [dim]via[/dim] {host}...\n")

    # 2. Generate suggestions
    try:
        with console.status("[bold green]Generating commit message…"):
            suggestions = generate_messages(
                diff_info.diff,
                diff_info.staged_files,
                model=model,
                base_url=host,
                count=count,
                hint=hint,
            )
    except httpx.ConnectError:
        err.print(f"[red]Cannot connect to Ollama at {host}.[/red] Is Ollama running?")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        err.print(f"[red]Ollama API error {e.response.status_code}:[/red] {e.response.text[:200]}")
        sys.exit(1)

    # 3. Present suggestions
    if count == 1 or yes:
        chosen = suggestions[0]
        panel = Panel(
            Text(chosen, style="bold white"), title="Suggested commit message", border_style="green"
        )
        console.print(panel)
    else:
        for i, msg in enumerate(suggestions, 1):
            console.print(
                Panel(Text(msg, style="bold white"), title=f"Option {i}", border_style="cyan")
            )

        choice_str = Prompt.ask(
            "Pick a suggestion",
            choices=[str(i) for i in range(1, len(suggestions) + 1)] + ["e", "q"],
            default="1",
        )
        if choice_str == "q":
            console.print("[dim]Aborted.[/dim]")
            sys.exit(0)
        if choice_str == "e":
            chosen = click.edit(suggestions[0]) or suggestions[0]
        else:
            chosen = suggestions[int(choice_str) - 1]

    if dry_run:
        console.print("\n[dim]--dry-run: not committing.[/dim]")
        sys.exit(0)

    # 4. Confirm and commit
    if not yes:
        if not Confirm.ask("\nCommit with this message?", default=True):
            console.print("[dim]Aborted.[/dim]")
            sys.exit(0)

    try:
        output = commit(chosen)
        console.print(f"\n[bold green]Committed![/bold green]\n{output}")
    except GitError as e:
        err.print(f"[red]Commit failed:[/red] {e}")
        sys.exit(1)


@main.command("models")
@click.option("--host", default=OLLAMA_DEFAULT_URL, show_default=True, help="Ollama base URL.")
def models_cmd(host: str) -> None:
    """List available Ollama models."""
    try:
        available = list_models(host)
    except httpx.ConnectError:
        err.print(f"[red]Cannot connect to Ollama at {host}.[/red]")
        sys.exit(1)

    if not available:
        console.print("[yellow]No models found.[/yellow] Pull one with: ollama pull mistral")
        return

    console.print("[bold]Available Ollama models:[/bold]")
    for m in available:
        console.print(f"  [cyan]{m}[/cyan]")


@main.command("install-hook")
@click.option("--force", is_flag=True, help="Overwrite existing hook.")
def install_hook_cmd(force: bool) -> None:
    """Install a prepare-commit-msg Git hook that auto-fills commit messages."""
    from .hook import install_hook
    install_hook(force=force)


@main.command("uninstall-hook")
def uninstall_hook_cmd() -> None:
    """Remove the prepare-commit-msg Git hook installed by ollama-commit."""
    from .hook import uninstall_hook
    uninstall_hook()
