"""Test that the package imports correctly."""


def test_import():
    """Test basic imports."""
    import didi
    assert didi.__version__


def test_import_cli():
    """Test CLI imports."""
    from didi import cli
    assert cli


def test_import_color():
    """Test color module imports."""
    from didi import should_use_color
    assert should_use_color


def test_import_diff():
    """Test diff module imports."""
    from didi import (
        build_diff_cmd,
        get_changed_files,
        get_commits,
        get_file_diff,
        normalize_diff,
    )
    assert build_diff_cmd
    assert get_changed_files
    assert get_commits
    assert get_file_diff
    assert normalize_diff


def test_import_pager():
    """Test pager module imports."""
    from didi import Pager
    assert Pager
