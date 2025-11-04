import sys
from subprocess import run
from typing import Dict

from utz import err


def get_rename_mapping(
    refspec: str,
    find_renames: str = None,
    find_copies: str = None,
) -> Dict[str, str]:
    """Get file rename/copy mapping for a refspec.

    Returns a dict mapping old paths to new paths for renamed/copied files.
    """
    cmd = ['git', 'diff', '--name-status']
    if find_renames:
        cmd.append(f'-M{find_renames}')
    if find_copies:
        cmd.append(f'-C{find_copies}')
    cmd.append(refspec)

    result = run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}

    mapping = {}
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            continue

        status = parts[0]
        # R = rename, C = copy
        # Format: R100\told_path\tnew_path or just R\told_path\tnew_path
        if status.startswith('R') or status.startswith('C'):
            if len(parts) >= 3:
                old_path = parts[1]
                new_path = parts[2]
                mapping[old_path] = new_path

    return mapping


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


def normalize_diff(diff_text: str, path_mapping: Dict[str, str] = None) -> str:
    """Normalize diff text by removing variable parts like index SHAs and mapping paths.

    Args:
        diff_text: The diff text to normalize
        path_mapping: Optional dict mapping old paths to new paths (for renames)

    Returns:
        Normalized diff text
    """
    lines = []
    for line in diff_text.splitlines():
        # Remove index line SHAs: "index abc123..def456" -> "index ..."
        if line.startswith('index '):
            lines.append('index ...')
        # Normalize paths in diff headers if mapping provided
        elif path_mapping and (line.startswith('diff --git ') or
                               line.startswith('--- ') or
                               line.startswith('+++ ')):
            # Apply path mapping to normalize renamed files
            normalized_line = line
            for old_path, new_path in path_mapping.items():
                normalized_line = normalized_line.replace(old_path, new_path)
            lines.append(normalized_line)
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


def parse_refspec_bases(refspec1: str, refspec2: str) -> tuple[str, str, str, str]:
    """Parse two refspecs to extract bases.

    Given refspecs like 'A..B' and 'C..D', returns (A, B, C, D).
    This allows computing A..C to find upstream changes (renames, etc).

    Returns:
        tuple: (base1, tip1, base2, tip2) or empty strings if not parseable
    """
    if '..' not in refspec1 or '..' not in refspec2:
        return ('', '', '', '')

    base1, tip1 = refspec1.split('..', 1)
    base2, tip2 = refspec2.split('..', 1)

    return (base1, tip1, base2, tip2)


def compute_upstream_range(refspec1: str, refspec2: str) -> str:
    """Compute upstream range from two refspecs.

    Given 'A..B' (before rebase) and 'C..D' (after rebase),
    returns 'A..C' (upstream changes).

    Returns empty string if refspecs can't be parsed.
    """
    base1, _, base2, _ = parse_refspec_bases(refspec1, refspec2)
    if base1 and base2:
        return f'{base1}..{base2}'
    return ''
