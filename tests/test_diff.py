"""Test diff utilities."""

from didi.diff import build_diff_cmd, normalize_diff


def test_build_diff_cmd_basic():
    """Test basic diff command building."""
    cmd = build_diff_cmd()
    assert cmd == ['git', 'diff']


def test_build_diff_cmd_with_follow():
    """Test diff command with --follow."""
    cmd = build_diff_cmd(follow=True)
    assert cmd == ['git', 'diff', '--follow']


def test_build_diff_cmd_with_ignore_whitespace():
    """Test diff command with -w flag."""
    cmd = build_diff_cmd(ignore_whitespace=True)
    assert cmd == ['git', 'diff', '-w']


def test_build_diff_cmd_with_renames():
    """Test diff command with -M flag."""
    cmd = build_diff_cmd(find_renames='50')
    assert cmd == ['git', 'diff', '-M50']


def test_build_diff_cmd_with_copies():
    """Test diff command with -C flag."""
    cmd = build_diff_cmd(find_copies='50')
    assert cmd == ['git', 'diff', '-C50']


def test_build_diff_cmd_all_options():
    """Test diff command with all options."""
    cmd = build_diff_cmd(
        ignore_whitespace=True,
        find_renames='50',
        find_copies='60',
        follow=True,
    )
    assert cmd == ['git', 'diff', '--follow', '-w', '-M50', '-C60']


def test_normalize_diff():
    """Test diff normalization removes index SHAs."""
    diff_text = """diff --git a/file.py b/file.py
index abc123..def456 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
-old line
+new line
"""
    normalized = normalize_diff(diff_text)
    assert 'abc123' not in normalized
    assert 'def456' not in normalized
    assert 'index ...' in normalized
    assert 'old line' in normalized
    assert 'new line' in normalized


def test_normalize_diff_preserves_non_index_lines():
    """Test that normalization preserves other diff content."""
    diff_text = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,1 +1,1 @@
-old content
+new content"""
    normalized = normalize_diff(diff_text)
    assert normalized == diff_text
