import os
import sys
from io import StringIO
from subprocess import PIPE, Popen, run


class Pager:
    """Context manager for paging output through less or similar."""

    def __init__(self, use_pager: str = 'auto'):
        """Initialize pager settings.

        Args:
            use_pager: 'always', 'never', or 'auto' (default)
        """
        self.use_pager = use_pager
        self.original_stdout = None
        self.buffer = None
        self.pager_process = None

    def should_page(self) -> bool:
        """Determine if paging should be used."""
        if self.use_pager == 'always':
            return True
        elif self.use_pager == 'never':
            return False
        else:  # auto
            # Use pager if output is to a TTY
            return sys.stdout.isatty()

    def __enter__(self):
        """Start capturing output for potential paging."""
        if self.should_page():
            # Capture output in a buffer first
            self.original_stdout = sys.stdout
            self.buffer = StringIO()
            sys.stdout = self.buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Send captured output through pager if needed."""
        if self.original_stdout:
            # Restore original stdout
            sys.stdout = self.original_stdout

            if self.buffer:
                output = self.buffer.getvalue()

                # Only page if output is substantial (more than terminal height)
                try:
                    terminal_height = int(os.environ.get('LINES', 24))
                    output_lines = output.count('\n')

                    if output_lines > terminal_height - 2:  # Leave room for prompt
                        # Use git's pager settings if available
                        pager_cmd = run(['git', 'config', 'core.pager'],
                                      capture_output=True, text=True).stdout.strip()
                        if not pager_cmd:
                            # Default to less with good options
                            pager_cmd = 'less -FRSX'

                        # Send output through pager
                        try:
                            pager = Popen(pager_cmd, shell=True, stdin=PIPE, text=True)
                            pager.communicate(output)
                        except Exception:
                            # If pager fails, just print directly
                            print(output, end='')
                    else:
                        # Output fits in terminal, print directly
                        print(output, end='')
                except Exception:
                    # If anything goes wrong, just print
                    print(output, end='')
