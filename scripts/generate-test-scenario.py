#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Generate test scenario branches for git-didi testing.

Creates orphan branches with a todo-app scaffold and demonstrates
various rebase/merge scenarios.
"""
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], **kwargs):
    """Run git command."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def create_base_scaffold(branch_name: str, scenario_num: str, description: str):
    """Create base branch with todo-app scaffold."""
    print(f"\nCreating base branch: {branch_name}")

    # Create orphan branch
    run(['git', 'checkout', '--orphan', branch_name])
    run(['git', 'rm', '-rf', '.'], capture_output=True)

    # Create todo app structure
    Path('src').mkdir(exist_ok=True)
    Path('tests').mkdir(exist_ok=True)

    # src/todo.py
    Path('src/todo.py').write_text('''"""Todo list data structures and logic."""
from dataclasses import dataclass
from typing import List


@dataclass
class Todo:
    """A todo item."""
    id: int
    text: str
    completed: bool = False


class TodoList:
    """Manage a list of todos."""

    def __init__(self):
        self.todos: List[Todo] = []
        self.next_id = 1

    def add_task(self, text: str) -> Todo:
        """Add a new todo."""
        todo = Todo(id=self.next_id, text=text)
        self.todos.append(todo)
        self.next_id += 1
        return todo

    def complete_task(self, todo_id: int) -> bool:
        """Mark a todo as complete."""
        for todo in self.todos:
            if todo.id == todo_id:
                todo.completed = True
                return True
        return False

    def list_tasks(self) -> List[Todo]:
        """Get all todos."""
        return self.todos
''')

    # src/storage.py
    Path('src/storage.py').write_text('''"""File storage for todos."""
import json
from pathlib import Path
from typing import List


def save_todos(todos: List[dict], filename: str = "todos.json"):
    """Save todos to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(todos, f, indent=2)


def load_todos(filename: str = "todos.json") -> List[dict]:
    """Load todos from a JSON file."""
    path = Path(filename)
    if not path.exists():
        return []
    with open(filename) as f:
        return json.load(f)
''')

    # src/cli.py
    Path('src/cli.py').write_text('''"""Command-line interface for todo app."""
import sys
from todo import TodoList


def main():
    """Main entry point."""
    todo_list = TodoList()

    if len(sys.argv) < 2:
        print("Usage: todo.py <add|list|complete> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            print("Usage: todo.py add <text>")
            sys.exit(1)
        text = " ".join(sys.argv[2:])
        todo = todo_list.add_task(text)
        print(f"Added: #{todo.id} {todo.text}")

    elif command == "list":
        todos = todo_list.list_tasks()
        if not todos:
            print("No todos!")
        for todo in todos:
            status = "✓" if todo.completed else " "
            print(f"[{status}] #{todo.id} {todo.text}")

    elif command == "complete":
        if len(sys.argv) < 3:
            print("Usage: todo.py complete <id>")
            sys.exit(1)
        todo_id = int(sys.argv[2])
        if todo_list.complete_task(todo_id):
            print(f"Completed #{todo_id}")
        else:
            print(f"Todo #{todo_id} not found")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
''')

    # tests/test_todo.py
    Path('tests/test_todo.py').write_text('''"""Tests for todo list."""
from src.todo import Todo, TodoList


def test_add_task():
    """Test adding a task."""
    todo_list = TodoList()
    todo = todo_list.add_task("Buy milk")
    assert todo.text == "Buy milk"
    assert todo.completed is False
    assert len(todo_list.todos) == 1


def test_complete_task():
    """Test completing a task."""
    todo_list = TodoList()
    todo = todo_list.add_task("Buy milk")
    assert todo_list.complete_task(todo.id) is True
    assert todo.completed is True


def test_complete_nonexistent():
    """Test completing a nonexistent task."""
    todo_list = TodoList()
    assert todo_list.complete_task(999) is False
''')

    # pyproject.toml
    Path('pyproject.toml').write_text('''[project]
name = "todo-app"
version = "1.0.0"
description = "Simple todo list application"
requires-python = ">=3.10"

[project.scripts]
todo = "src.cli:main"
''')

    # README.md
    Path('README.md').write_text(f'''# Test Scenario {scenario_num}

{description}

## Setup

This is a synthetic test scenario for `git-didi` demonstrating rebase/merge verification.

## Branches

- `{branch_name}`: Base scaffold (merge base)
- `tests/{scenario_num}/alice`: Alice's changes
- `tests/{scenario_num}/bob`: Bob's changes
- `tests/{scenario_num}/alice-rebased-on-bob`: Alice rebased onto Bob
- `tests/{scenario_num}/bob-rebased-on-alice`: Bob rebased onto Alice
- `tests/{scenario_num}/merged`: Merge commit of Alice and Bob

## Testing

```bash
# Compare Alice's rebase
git-didi patch {branch_name}..tests/{scenario_num}/alice \\
               tests/{scenario_num}/bob..tests/{scenario_num}/alice-rebased-on-bob

# Compare Bob's rebase
git-didi patch {branch_name}..tests/{scenario_num}/bob \\
               tests/{scenario_num}/alice..tests/{scenario_num}/bob-rebased-on-alice
```
''')

    # Commit the base
    run(['git', 'add', '.'])
    run(['git', 'commit', '-m', f'test-scenario {scenario_num}: base scaffold\n\n{description}'])

    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()


def create_scenario_01():
    """Scenario 01: Clean rebase - disjoint files."""
    scenario = "01-clean-disjoint"
    desc = "Clean rebase with disjoint changes in different files"

    # Create base
    base_branch = f"tests/{scenario}/base"
    base_sha = create_base_scaffold(base_branch, scenario, desc)
    print(f"Base SHA: {base_sha}")

    # Alice: Adds priority field
    print(f"\nCreating Alice's branch")
    run(['git', 'checkout', '-b', f'tests/{scenario}/alice', base_sha])

    # Modify todo.py to add priority
    todo_content = Path('src/todo.py').read_text()
    todo_content = todo_content.replace(
        '    completed: bool = False',
        '    completed: bool = False\n    priority: int = 1  # 1=low, 2=medium, 3=high'
    )
    Path('src/todo.py').write_text(todo_content)

    run(['git', 'add', 'src/todo.py'])
    run(['git', 'commit', '-m', 'Add priority field to todos'])
    alice_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()

    # Bob: Adds JSON format flag
    print(f"\nCreating Bob's branch")
    run(['git', 'checkout', '-b', f'tests/{scenario}/bob', base_sha])

    cli_content = Path('src/cli.py').read_text()
    cli_content = cli_content.replace(
        '    elif command == "list":',
        '''    elif command == "list":
        format_json = "--format=json" in sys.argv
        '''
    )
    cli_content = cli_content.replace(
        '        if not todos:',
        '''        if format_json:
            import json
            data = [{"id": t.id, "text": t.text, "completed": t.completed} for t in todos]
            print(json.dumps(data, indent=2))
            return

        if not todos:'''
    )
    Path('src/cli.py').write_text(cli_content)

    run(['git', 'add', 'src/cli.py'])
    run(['git', 'commit', '-m', 'Add --format=json flag to list command'])
    bob_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()

    # Alice rebased on Bob
    print(f"\nCreating Alice rebased on Bob")
    run(['git', 'checkout', '-b', f'tests/{scenario}/alice-rebased-on-bob', bob_sha])
    run(['git', 'cherry-pick', alice_sha])

    # Bob rebased on Alice
    print(f"\nCreating Bob rebased on Alice")
    run(['git', 'checkout', '-b', f'tests/{scenario}/bob-rebased-on-alice', alice_sha])
    run(['git', 'cherry-pick', bob_sha])

    # Merged
    print(f"\nCreating merge commit")
    run(['git', 'checkout', '-b', f'tests/{scenario}/merged', alice_sha])
    run(['git', 'merge', '--no-ff', bob_sha, '-m', f'Merge: {desc}'])

    print(f"\n✓ Scenario {scenario} complete!")
    print(f"  Base: {base_sha}")
    print(f"  Alice: {alice_sha}")
    print(f"  Bob: {bob_sha}")


def main():
    """Generate test scenarios."""
    if len(sys.argv) < 2:
        print("Usage: generate-test-scenario.py <scenario>")
        print("\nAvailable scenarios:")
        print("  01-clean-disjoint    Clean rebase with disjoint file changes")
        print("  (more to be implemented)")
        sys.exit(1)

    scenario = sys.argv[1]

    if scenario == "01-clean-disjoint":
        create_scenario_01()
    else:
        print(f"Unknown scenario: {scenario}")
        sys.exit(1)


if __name__ == "__main__":
    main()
