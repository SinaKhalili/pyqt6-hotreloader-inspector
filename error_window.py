import json
import os
import sys
import traceback as tracebacklib
from importlib import reload
from types import TracebackType
from typing import Type

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from PyQt6.QtCore import QFileSystemWatcher, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

sans_serif_fonts = "'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif"
monospace_fonts = (
    "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, Courier, monospace"
)

# Nextjs inspired error style template
error_msg_template = """
<div style="font-family: {sans_serif_fonts}; line-height: 1.5; color: #000; margin-left: 15px;">
    <div style="font-size: 24px; font-weight: 600;">{error_type}: {msg}</div>
    <div style="font-size: 20px; margin-bottom: 16px; color: grey;">
        Source at line {lineno}
    </div>
    <div style="font-size: 20px; margin-bottom: 16px;">
        {filename} {lineno}:{offset}
    </div>
    <div style="font-size: 20px">
        {highlighted_code}
    </div>
    <pre style="font-size: 14px; font-weight: 400; color: #666; margin-bottom: 16px;">{traceback}</pre>
</div>
"""

error_msg_template_generic = """
<pre style="color: #000">
    {traceback}
</pre>
"""


def get_highlighted_code_at_line(filename, lineno):
    with open(filename, "r") as f:
        lines = f.readlines()
        line_number = lineno - 1
        lines = lines[line_number - 2 : line_number + 3]

    formatter = HtmlFormatter(
        style="colorful",
        noclasses=True,
        linenos=False,
        hl_lines=[3],
        lineanchors="line",
        anchorlinenos=True,
    )
    return highlight("".join(lines), PythonLexer(), formatter)


class ErrorWindow(QMainWindow):
    def __init__(
        self, exception_class, exception_instance: Exception, traceback: TracebackType
    ):
        super().__init__()
        self.setMinimumSize(900, 700)
        self.setWindowTitle("Error")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: white;")

        # Print the exception for the console
        tracebacklib.print_exception(exception_class, exception_instance, traceback)

        tb = traceback
        while tb.tb_next:
            tb = tb.tb_next

        filename = tb.tb_frame.f_code.co_filename
        lineno = tb.tb_lineno
        offset = tb.tb_frame.f_code.co_firstlineno
        msg = exception_instance.args[0]
        te_error = tracebacklib.TracebackException.from_exception(exception_instance)

        if exception_class == SyntaxError:
            filename = te_error.filename
            lineno = te_error.lineno
            offset = te_error.offset
            msg = te_error.msg

        error_type = exception_class.__name__

        error_msg = error_msg_template.format(
            msg=msg,
            error_type=error_type,
            filename=filename,
            lineno=lineno,
            offset=offset,
            highlighted_code=get_highlighted_code_at_line(filename, int(lineno)),
            traceback="".join(
                tracebacklib.format_exception(
                    exception_class, exception_instance, traceback
                )
            ),
            sans_serif_fonts=sans_serif_fonts,
            monospace_fonts=monospace_fonts,
        )

        self.error_label = QLabel(error_msg)
        self.error_label.setWordWrap(True)
        self.error_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.top = QWidget()
        self.top.setStyleSheet("background-color: red;")
        self.top.setFixedHeight(5)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.top)
        self.layout.addWidget(self.error_label)

        self.layout.setContentsMargins(0, 0, 0, 0)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

    def toggle_traceback(self, event):
        if self.traceback_label.isVisible():
            self.traceback_label.hide()
            self.traceback_toggle.setText("Show traceback")
        else:
            self.traceback_label.show()
            self.traceback_toggle.setText("Hide traceback")
