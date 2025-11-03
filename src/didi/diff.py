import sys
from subprocess import run

from utz import err


def build_diff_cmd(
    ignore_whitespace: bool = False,
    find_renames: str = None,
    find_copies: str = None,
    follow: bool = False,
) -> list[str]:
    """Build base git diff command with common options."""
    cmd = ['git', 'diff']
    if follow:
        cmd.append('--follow')
    if ignore_whitespace:
        cmd.append('-w')
    if find_renames:
        cmd.append(f'-M{find_renames}')
    if find_copies:
        cmd.append(f'-C{find_copies}')
    return cmd


def get_changed_files(refspec: str, paths: tuple[str, ...] = ()) -> list[str]:
    """Get list of files changed in a git refspec, optionally filtered by paths."""
    cmd = ['git', 'diff', '--name-only', refspec]
    if paths:
        cmd.extend(['--', *paths])
    result = run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        err(f"Error getting changed files for {refspec}: {result.stderr.strip()}")
        sys.exit(1)
    return [f for f in result.stdout.strip().split('\n') if f]


def normalize_diff(diff_text: str) -> str:
    """Normalize diff text by removing variable parts like index SHAs."""
    lines = []
    for line in diff_text.splitlines():
        # Remove index line SHAs: "index abc123..def456" -> "index ..."
        if line.startswith('index '):
            lines.append('index ...')
        else:
            lines.append(line)
    return '\n'.join(lines)


def get_file_diff(
    refspec: str,
    filepath: str,
    ignore_whitespace: bool = False,
    unified: int = 3,
    find_renames: str = None,
    find_copies: str = None,
) -> str:
    """Get diff for a specific file in a refspec."""
    cmd = build_diff_cmd(ignore_whitespace, find_renames, find_copies, follow=True)
    cmd.extend([f'-U{unified}', refspec, '--', filepath])
    result = run(cmd, capture_output=True, text=True)
    return result.stdout


def get_commits(refspec: str) -> list[str]:
    """Get list of commits in a refspec."""
    result = run(['git', 'log', '--oneline', refspec], capture_output=True, text=True)
    if result.returncode != 0:
        err(f"Error getting commits for {refspec}: {result.stderr}")
        return []
    return [line for line in result.stdout.strip().split('\n') if line]
