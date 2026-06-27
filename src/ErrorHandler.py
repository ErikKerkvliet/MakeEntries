"""Crash reporting for the application.

When the program stops because of an unhandled error we want to show the user
the same information that would otherwise scroll past in the terminal: every
line that was printed plus the traceback of the error. To do that we:

* tee ``sys.stdout`` / ``sys.stderr`` into an in-memory buffer so the full
  terminal output is available after a crash (``install``);
* show that buffer together with the traceback in a Tkinter dialog
  (``show_error_dialog``).
"""

import io
import sys
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext


class _Tee:
    """Write to several streams at once (the real terminal and a buffer)."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            try:
                stream.write(data)
            except Exception:
                pass
        return len(data)

    def flush(self):
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:
                pass


# Buffer holding everything printed to the terminal during the run.
_output_buffer = io.StringIO()


def install():
    """Start capturing terminal output and route Tk callback crashes here.

    Returns a callable that yields everything printed so far. Call this once,
    as early as possible, from the application entry point.
    """
    sys.stdout = _Tee(sys.__stdout__, _output_buffer)
    sys.stderr = _Tee(sys.__stderr__, _output_buffer)

    # Exceptions raised inside a Tk callback (e.g. a button handler) are
    # otherwise only printed to stderr and never reach the top-level
    # try/except, so surface them in the dialog too.
    def report_callback_exception(self, exc, val, tb):
        tb_text = ''.join(traceback.format_exception(exc, val, tb))
        sys.stderr.write(tb_text)
        show_error_dialog(get_terminal_output(), tb_text)

    tk.Tk.report_callback_exception = report_callback_exception

    return get_terminal_output


def get_terminal_output():
    """Return everything printed to stdout/stderr so far."""
    return _output_buffer.getvalue()


def show_error_dialog(terminal_output, traceback_text,
                      title='The application stopped because of an error'):
    """Show a modal window with the terminal output and the traceback."""
    content = ''
    if traceback_text:
        content += 'Traceback:\n' + traceback_text.rstrip() + '\n'
    if terminal_output:
        content += '\n' + ('-' * 80) + '\nTerminal output:\n' + terminal_output

    try:
        root = tk.Tk()
    except Exception:
        # No display available (e.g. headless) — fall back to the terminal.
        print(content, file=sys.__stderr__)
        return

    root.title(title)

    try:
        icon_path = Path(__file__).parent.parent / 'images' / 'MakeEntries.png'
        if icon_path.exists():
            root.wm_iconphoto(True, tk.PhotoImage(file=str(icon_path)))
    except Exception:
        pass

    width, height = 900, 600
    try:
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 3)
        root.geometry(f'{width}x{height}+{x}+{y}')
    except Exception:
        root.geometry(f'{width}x{height}')

    tk.Label(
        root,
        text=title + ':',
        anchor='w',
        fg='#b00020',
        font=('TkDefaultFont', 11, 'bold'),
    ).pack(fill='x', padx=10, pady=(10, 0))

    text = scrolledtext.ScrolledText(root, wrap='word', font=('TkFixedFont', 10))
    text.pack(fill='both', expand=True, padx=10, pady=10)
    text.insert('1.0', content)
    text.see('end')
    text.configure(state='disabled')

    buttons = tk.Frame(root)
    buttons.pack(fill='x', padx=10, pady=(0, 10))

    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(content)

    tk.Button(buttons, text='Copy', command=copy_to_clipboard).pack(side='right', padx=(5, 0))
    tk.Button(buttons, text='Close', command=root.destroy).pack(side='right')

    root.lift()
    try:
        root.attributes('-topmost', True)
    except Exception:
        pass
    root.mainloop()
