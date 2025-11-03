# git-didi Test Strategy: Diff-of-Diffs Matrix

## Overview

`git-didi` compares diffs between two git ranges, producing a "diff of diffs." This is particularly useful for verifying rebases. The test strategy creates synthetic branches exhibiting various change patterns to systematically test all combinations of operations.

## The Rebase Quadrilateral

When comparing diffs before and after a rebase, we're implicitly analyzing a 4-point structure:

```
    MB (merge base)
   /  \
  /    \
 B0    U0 (upstream before)
  \    /
   \  /
    U1 (upstream after = new merge base)
     |
     B1 (branch after rebase)
```

We compare:
- **Left diff**: `MB..B0` (branch changes before rebase)
- **Right diff**: `U1..B1` (branch changes after rebase)
- **Implicit context**: `MB..U0..U1` (what changed upstream)

The diff-of-diffs reveals:
1. **No changes**: Rebase was clean, patches identical
2. **Index-only changes**: SHAs changed but content identical (filtered by `didi`)
3. **Content changes**: Actual differences in how patches apply

## Diff-of-Diff Line Prefix Semantics

In a diff-of-diffs, each line has a **2-character prefix**:

### First character (outer diff):
- `+`: This line exists in the "after rebase" diff but not "before"
- `-`: This line existed "before rebase" but not "after"
- ` ` (space): This line is common to both diffs

### Second character (inner diff):
- `+`: This is an added line in the original patch
- `-`: This is a removed line in the original patch
- ` ` (space): This is context in the original patch
- `@`: Hunk header
- `d`, `i`: diff metadata (diff --git, index, etc.)

### Common patterns:

| Prefix | Meaning |
|--------|---------|
| `++` | Line was added in the after-rebase patch (not in before) |
| `--` | Line was removed in the before-rebase patch (not in after) |
| `+-` | A removed line in the before-rebase patch |
| `-+` | An added line in the before-rebase patch |
| `+ ` | Context line in the after-rebase patch only |
| `- ` | Context line in the before-rebase patch only |
| ` +` | Added line present in both patches (identical) |
| ` -` | Removed line present in both patches (identical) |
| `  ` | Context line present in both patches (identical) |

### Real-world example interpretations:

From `/Users/ryan/c/oa/marin` example:

```diff
--          PYTHONPATH=tests:. uv run pytest -n3 --durations=5 --tb=short -m 'not slow and not tpu_ci' -v tests/
-+          PYTHONPATH=tests:. uv run --extra=cpu pytest -n3 --durations=5 --tb=short -m 'not slow and not tpu_ci' -v tests/
+-          PYTHONPATH=tests:. uv run pytest -n3 --durations=5 --tb=short -m 'not slow and not gcp' -v tests/
++          PYTHONPATH=tests:. uv run --extra=cpu pytest -n3 --durations=5 --tb=short -m 'not slow and not gcp' -v tests/
```

This shows:
- Before rebase: Changed `tpu_ci` → `tpu_ci` (no marker change)
- After rebase: Changed `gcp` → `gcp` with `--extra=cpu` added
- The marker name changed upstream from `tpu_ci` → `gcp`, and the `--extra=cpu` addition was preserved

## Test Matrix Dimensions

### Dimension 1: Change Types (Operations)

Basic atomic operations:
1. **Add lines** (to function, class, file)
2. **Remove lines**
3. **Modify lines** (change content)
4. **Add function/class**
5. **Remove function/class**
6. **Rename function/class** (same location)
7. **Move function/class** (different location in same file)
8. **Add file**
9. **Remove file**
10. **Rename file**
11. **Move file** (to different directory)
12. **Reformat** (whitespace, sort imports, etc.)
13. **Add parameter** (to function signature)
14. **Remove parameter**
15. **Reorder parameters**
16. **Change imports** (add, remove, reorder)

### Dimension 2: Locations

Where changes occur relative to each other:
1. **Disjoint**: Changes in completely separate files
2. **Same file, distant**: Changes in same file, different functions
3. **Same file, adjacent**: Changes in neighboring functions
4. **Same function**: Changes in same function body
5. **Same line**: Both sides modify the exact same line
6. **Overlapping hunks**: Changes that affect overlapping context

### Dimension 3: Conflict Resolution

How the rebase resolves:
1. **Clean**: No conflicts, automatic merge
2. **Conflict - keep ours**: Manual resolution chose branch's version
3. **Conflict - keep theirs**: Manual resolution chose upstream's version
4. **Conflict - merge both**: Manual resolution combined both changes
5. **Conflict - rewrite**: Manual resolution rewrote the section

### Dimension 4: Expected Diff-of-Diff Outcome

What should `didi` show:
1. **Identical**: No differences (successful rebase preservation)
2. **Index-only**: Only git SHAs differ (normalized away)
3. **Context shift**: Same changes, different surrounding context
4. **Line number shift**: Same changes, different line numbers
5. **Content differs**: Actual patch content changed (investigate!)

## Proposed Test Branch Structure

Create **orphan branches** under `tests/` namespace to demonstrate each scenario. Each branch is independent with no shared lineage with `main` or each other (except where they share a common base within a scenario).

### Branch Naming Convention:
```
tests/<scenario>/<variant>
```

Where:
- `<scenario>`: Short description (e.g., `01-clean-disjoint`, `05-import-sort`)
- `<variant>`: One of:
  - `base`: The common starting point (merge base)
  - `alice`: First developer's changes (feature branch)
  - `bob`: Second developer's changes (upstream/other feature)
  - `alice-rebased-on-bob`: Alice's branch after rebasing onto Bob
  - `bob-rebased-on-alice`: Bob's branch after rebasing onto Alice
  - `merged`: Result of merging Alice and Bob (shows both sides in one commit)

### Example for Scenario 01:
```
tests/01-clean-disjoint/base           # Empty todo app
tests/01-clean-disjoint/alice          # Adds feature A
tests/01-clean-disjoint/bob            # Adds feature B
tests/01-clean-disjoint/alice-rebased-on-bob
tests/01-clean-disjoint/bob-rebased-on-alice
tests/01-clean-disjoint/merged         # Merge commit showing both
```

### Testing Both Directions:
```bash
# Alice rebases onto Bob - should show clean rebase
git-didi patch tests/01-clean-disjoint/base..tests/01-clean-disjoint/alice \
               tests/01-clean-disjoint/bob..tests/01-clean-disjoint/alice-rebased-on-bob

# Bob rebases onto Alice - should show clean rebase (symmetric)
git-didi patch tests/01-clean-disjoint/base..tests/01-clean-disjoint/bob \
               tests/01-clean-disjoint/alice..tests/01-clean-disjoint/bob-rebased-on-alice

# Comparing pre-merge branches with merge commit parents
git-didi patch tests/01-clean-disjoint/base..tests/01-clean-disjoint/alice \
               tests/01-clean-disjoint/merged^1..tests/01-clean-disjoint/merged

git-didi patch tests/01-clean-disjoint/base..tests/01-clean-disjoint/bob \
               tests/01-clean-disjoint/merged^2..tests/01-clean-disjoint/merged
```

## Shared Scaffold: Todo List App

All test scenarios use a simple todo list application as the base project:

```
todo-app/
  src/
    todo.py          # Main todo list logic
    storage.py       # File I/O
    cli.py           # Command-line interface
  tests/
    test_todo.py     # Unit tests
  README.md          # Project documentation
  pyproject.toml    # Project config
```

This provides a realistic codebase where developers Alice and Bob independently work on features and maintenance.

### Key Scenarios to Implement

#### 1. Clean rebase - disjoint files
- **Alice**: Adds `priority` field to todos in `todo.py`
- **Bob**: Adds `--format json` flag in `cli.py`
- **Expected**: Identical diffs (changes in different files)
- **Demonstrates**: Basic case where rebase is perfect

#### 2. Same line modification (conflict)
- **Alice**: Changes `VERSION = "1.0"` → `VERSION = "1.1"` (patch release)
- **Bob**: Changes `VERSION = "1.0"` → `VERSION = "2.0"` (major release)
- **Alice rebased**: Resolves to `VERSION = "2.1"` (preserves both intents)
- **Bob rebased**: Resolves to `VERSION = "2.1"` (same resolution)
- **Expected**: Diff shows different version targets in before-rebase, same in after
- **Demonstrates**: Conflict resolution visible in didi

#### 3. Function rename + new callsite
- **Alice**: Renames `add_task()` → `create_task()` throughout codebase
- **Bob**: Adds new feature calling `add_task()` in `cli.py`
- **Alice rebased**: Must manually update Bob's new call to `create_task()`
- **Expected**: Shows rename, plus additional change to fix Bob's callsite
- **Demonstrates**: Semantic conflict requiring manual intervention

#### 4. File rename + content modification
- **Alice**: Renames `storage.py` → `persistence.py`
- **Bob**: Adds caching logic to `storage.py`
- **Alice rebased**: Git tracks rename, applies Bob's changes to `persistence.py`
- **Expected**: Identical content changes, different file paths
- **Demonstrates**: Git's rename detection with `-M` flag

#### 5. Import sorting vs new import
- **Alice**: Sorts all imports alphabetically
- **Bob**: Adds `import json` in middle of unsorted imports
- **Alice rebased**: Re-sorts to include `import json`
- **Expected**: Shows full import list reordering
- **Demonstrates**: Formatting changes interacting with content changes

#### 6. Parameter addition (both sides)
- **Alice**: Adds `debug: bool = False` parameter to `save_todos()`
- **Bob**: Adds `compress: bool = True` parameter to `save_todos()`
- **Alice rebased**: Keeps both parameters
- **Expected**: Shows both parameters in after-rebase
- **Demonstrates**: Complementary changes that merge cleanly

#### 7. Duplicate refactoring
- **Alice**: Extracts `_validate_todo(todo)` helper function
- **Bob**: Extracts identical `_validate_todo(todo)` helper function
- **Alice rebased**: Removes duplicate, keeps Bob's version
- **Expected**: Shows helper in alice's before-rebase, absent in after
- **Demonstrates**: Recognizing and removing duplicate work

#### 8. Function move within file
- **Alice**: Moves `complete_task()` from line 50 to line 150 (reordering)
- **Bob**: Modifies nearby `list_tasks()` at line 60
- **Alice rebased**: Both changes apply with different context lines
- **Expected**: Same function content, different surrounding context
- **Demonstrates**: Context line shifts without content changes

#### 9. Delete vs modify (conflict)
- **Alice**: Deletes deprecated `export_csv()` function
- **Bob**: Adds docstring and type hints to `export_csv()`
- **Alice rebased**: Keeps deletion (feature is deprecated)
- **Expected**: Shows modification in before-rebase, deletion in after
- **Demonstrates**: Conflicting intents resolved by choosing one

#### 10. Whitespace/formatting
- **Alice**: Runs `black` formatter (adds spaces, line breaks)
- **Bob**: Adds new `archive_completed()` function
- **Alice rebased**: New function gets formatted
- **Expected**: With `-w`, should show identical logical changes
- **Demonstrates**: Whitespace normalization with `-w` flag

#### 11. Directory restructure
- **Alice**: Moves `src/storage.py` → `src/backend/storage.py`
- **Bob**: Adds `src/cache.py` file
- **Alice rebased**: Directory structure reflects reorganization
- **Expected**: Shows file paths differ, content identical
- **Demonstrates**: Structural refactoring

#### 12. Merge commit demonstration
- **Alice**: Implements `--due-date` feature (3 commits)
- **Bob**: Implements `--tags` feature (2 commits)
- **Merged**: Merge commit combining both features
- **Expected**: Can compare each parent with merge result
- **Demonstrates**: Using didi with merge commits, not just rebases

## Test Implementation Strategy

### Phase 1: Create Test Branches
Use script to generate orphan branches with todo-app scaffold:

```bash
# Generate scenario 01 - Clean disjoint changes
./scripts/generate-test-scenario.py 01-clean-disjoint

# This creates:
# - tests/01-clean-disjoint/base
# - tests/01-clean-disjoint/alice  (adds priority field)
# - tests/01-clean-disjoint/bob (adds JSON format)
# - tests/01-clean-disjoint/alice-rebased-on-bob
# - tests/01-clean-disjoint/bob-rebased-on-alice
# - tests/01-clean-disjoint/merged
```

Each scenario is self-contained with its own README explaining:
- What Alice did
- What Bob did
- How conflicts were resolved (if any)
- Expected didi output
- Links to didi commands to run

### Phase 2: Integration Tests
```python
@pytest.mark.integration
def test_scenario_01_clean_disjoint_alice_on_bob():
    """Test Alice's clean rebase onto Bob."""
    result = run_didi(
        'tests/01-clean-disjoint/base..tests/01-clean-disjoint/alice',
        'tests/01-clean-disjoint/bob..tests/01-clean-disjoint/alice-rebased-on-bob'
    )
    assert result.returncode == 0
    assert "No differences in patches" in result.stderr

@pytest.mark.integration
def test_scenario_01_clean_disjoint_bob_on_alice():
    """Test Bob's clean rebase onto Alice."""
    result = run_didi(
        'tests/01-clean-disjoint/base..tests/01-clean-disjoint/bob',
        'tests/01-clean-disjoint/alice..tests/01-clean-disjoint/bob-rebased-on-alice'
    )
    assert result.returncode == 0
    assert "No differences in patches" in result.stderr

@pytest.mark.integration
def test_scenario_05_import_sort_shows_reordering():
    """Test import sorting interaction."""
    result = run_didi(
        'tests/05-import-sort/base..tests/05-import-sort/alice',
        'tests/05-import-sort/bob..tests/05-import-sort/alice-rebased-on-bob'
    )
    # Should show import differences
    assert "import" in result.stdout
    # Alice's version sorts, Bob's adds json mid-list, rebase re-sorts
    assert "+import json" in result.stdout

@pytest.mark.integration
def test_scenario_12_merge_commit():
    """Test didi with merge commits."""
    # Compare Alice's changes before/after merge
    result_alice = run_didi(
        'tests/12-merge/base..tests/12-merge/alice',
        'tests/12-merge/merged^1..tests/12-merge/merged'
    )
    # Compare Bob's changes before/after merge
    result_bob = run_didi(
        'tests/12-merge/base..tests/12-merge/bob',
        'tests/12-merge/merged^2..tests/12-merge/merged'
    )
    # Both should show clean integration
    assert "No differences" in result_alice.stderr
    assert "No differences" in result_bob.stderr
```

### Phase 3: Property-Based Tests
Generate random combinations of operations:
```python
@given(
    branch_ops=st.lists(st.sampled_from(OPERATIONS)),
    upstream_ops=st.lists(st.sampled_from(OPERATIONS)),
)
def test_rebase_properties(branch_ops, upstream_ops):
    # Generate commits, rebase, compare
    # Verify certain invariants hold
    pass
```

### Phase 4: Real-World Test Cases
Capture known rebase scenarios from production repos:
- Save the git state (commits, reflog)
- Record expected `didi` output
- Use as regression tests

## Benefits

1. **Comprehensive coverage**: Systematic exploration of operation combinations
2. **Documentation**: Each scenario serves as example for users
3. **Regression prevention**: Catch color scheme, normalization bugs
4. **Performance testing**: Measure speed on various diff sizes
5. **Educational**: Help users understand diff-of-diff semantics

## Next Steps

1. Create `test-cases/` directory structure
2. Implement scenarios 1, 2, 5, 6, 9 (cover main patterns)
3. Write integration test harness
4. Document each scenario's expected behavior
5. Add links in main README to scenario examples
