import sys


def should_use_color(color_option: str) -> bool:
    """Determine if color should be used based on option and TTY status."""
    if color_option == 'always':
        return True
    elif color_option == 'never':
        return False
    else:  # auto
        return sys.stdout.isatty()
