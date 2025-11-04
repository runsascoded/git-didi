"""git-didi: Compare diffs between two git ranges - a 'diff of diffs' tool."""

__version__ = "0.1.0"

from .cli import cli
from .color import should_use_color
from .diff import (
    build_diff_cmd,
    compute_upstream_range,
    get_changed_files,
    get_commits,
    get_file_diff,
    get_rename_mapping,
    normalize_diff,
    parse_refspec_bases,
)
from .pager import Pager

__all__ = [
    "cli",
    "should_use_color",
    "build_diff_cmd",
    "compute_upstream_range",
    "get_changed_files",
    "get_commits",
    "get_file_diff",
    "get_rename_mapping",
    "normalize_diff",
    "parse_refspec_bases",
    "Pager",
]
