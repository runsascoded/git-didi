"""Shell integration command."""

from os import environ
from pathlib import Path

from click import Choice
from utz import err
from utz.cli import arg


def shell_integration(shell: str | None) -> None:
    """Output shell aliases for git-didi commands.

    Usage:
        # Bash/Zsh: Add to your ~/.bashrc or ~/.zshrc:
        eval "$(git-didi shell-integration bash)"

        # Fish: Add to your ~/.config/fish/config.fish:
        git-didi shell-integration fish | source

        # Or save to a file and source it:
        git-didi shell-integration bash > ~/.git-didi-aliases.sh
        echo 'source ~/.git-didi-aliases.sh' >> ~/.bashrc
    """
    # Auto-detect shell if not specified
    if not shell:
        shell_env = environ.get('SHELL', '')
        if 'fish' in shell_env:
            shell = 'fish'
        elif 'zsh' in shell_env:
            shell = 'zsh'
        else:
            shell = 'bash'  # default

    # Get the shell directory (in the didi package)
    shell_dir = Path(__file__).parent.parent / 'shell'
    shell_file = shell_dir / f'git-didi.{shell if shell != "zsh" else "bash"}'

    if shell_file.exists():
        with open(shell_file, 'r') as f:
            print(f.read())
    else:
        err(f"Error: Shell integration file not found: {shell_file}")
        exit(1)


def register(cli):
    """Register command with CLI."""
    cli.command(name='shell-integration')(
        arg('shell', type=Choice(['bash', 'zsh', 'fish']), required=False)(
            shell_integration
        )
    )
