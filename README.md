# git-didi

Compare diffs between two git ranges - a "diff of diffs" tool.

This tool is particularly useful for verifying rebases, especially when complex conflict resolution was involved. It helps ensure that the actual changes in your branch remain the same before and after rebasing onto a new upstream.

## Installation

```bash
pip install git-didi
```

Or with `uv`:

```bash
uv tool install git-didi
```

## Usage

### Common use case - checking a rebase

After fetching and rebasing your branch onto main:

```bash
git fetch
git rebase main
```

You can verify the rebase preserved your changes:

```bash
git-didi patch main@{1}..branch@{1} main..branch
```

This compares:
- **Left side**: Your changes before the rebase (`main@{1}..branch@{1}`)
- **Right side**: Your changes after the rebase (`main..branch`)

The `@{1}` syntax refers to the previous position in the reflog. If both refs moved exactly once during the rebase, `@{1}` will work. If you've done multiple operations, you may need `@{2}`, `@{3}`, etc. Use `git reflog` to find the right positions.

### Commands

#### `stat` - Compare diff stats

Compare `git diff --stat` output between two refspecs:

```bash
git-didi stat main..feature upstream/main..feature
```

Shows only the files where the diff statistics differ.

#### `patch` - Compare patches file-by-file

Compare patches between two refspecs, showing differences for each file:

```bash
git-didi patch main..feature upstream/main..feature
```

This shows a "diff of diffs" with sophisticated coloring to distinguish:
- Changes in the outer diff (what changed between the two versions)
- Changes in the inner diffs (the actual patches)

Options:
- `-U N` / `--unified N`: Set context lines (default: 3)
- `-q` / `--quiet`: Only list files with differences
- `-w` / `--ignore-whitespace`: Ignore whitespace changes
- `-M[n]` / `--find-renames[=n]`: Detect renames
- `-C[n]` / `--find-copies[=n]`: Detect copies
- `--color {auto,always,never}`: Control colored output
- `--pager {auto,always,never}`: Control pager usage

#### `commits` - Compare commits

Compare individual commits between two refspecs:

```bash
git-didi commits main..feature upstream/main..feature
```

First verifies that commits correspond (same count and messages), then shows per-commit differences.

#### `swatches` - Display color palette

Show color swatches demonstrating the diff-of-diffs coloring scheme:

```bash
git-didi swatches --color=always
```

### Filtering by path

All commands support filtering to specific paths:

```bash
git-didi patch main..feature upstream/main..feature -- src/
git-didi stat main..feature upstream/main..feature -- "*.py"
```

## Git Aliases

You can add these to your `~/.gitconfig` for convenient access:

```ini
[alias]
    didi = !git-didi
    gdds = !git-didi stat
    gddp = !git-didi patch
    gddc = !git-didi commits
```

Then use:

```bash
git didi patch main@{1}..branch@{1} main..branch
git gddp main..feature upstream/main..feature
```

## How it works

The tool automatically filters out spurious differences like git index SHAs that change even when the actual patch content is identical. This makes it easy to verify that a rebase or cherry-pick truly preserved your changes without introducing unexpected modifications.

When comparing patches, it uses a sophisticated 256-color palette to make nested diffs easy to read:
- Bright backgrounds for added/removed lines within the outer diff
- Dark backgrounds for context lines
- Mixed colors for lines that changed type (+ to - or vice versa)

## Development

```bash
# Clone and setup
git clone https://github.com/ryan-williams/git-didi.git
cd git-didi

# Setup with uv
uv sync --extra test

# Run tests
uv run pytest tests/ -v

# Install locally
uv pip install -e .
```

## License

MIT License - see [LICENSE] for details.

[LICENSE]: LICENSE
