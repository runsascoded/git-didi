"""Test color utilities."""

import sys
from unittest.mock import patch

from didi.color import should_use_color


def test_should_use_color_always():
    """Test that 'always' always returns True."""
    assert should_use_color('always') is True


def test_should_use_color_never():
    """Test that 'never' always returns False."""
    assert should_use_color('never') is False


def test_should_use_color_auto_tty():
    """Test that 'auto' returns True when stdout is a TTY."""
    with patch.object(sys.stdout, 'isatty', return_value=True):
        assert should_use_color('auto') is True


def test_should_use_color_auto_no_tty():
    """Test that 'auto' returns False when stdout is not a TTY."""
    with patch.object(sys.stdout, 'isatty', return_value=False):
        assert should_use_color('auto') is False
