import json
import os
import sys
from importlib import reload
import typing

from PyQt6.QtCore import QFileSystemWatcher, Qt
from PyQt6.QtGui import (
    QPen,
    QPainter,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QStyleOption,
    QMainWindow,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QProxyStyle,
    QWidget,
)


def hard_restart_program():
    """
    Restarts the current program.
    """
    try:
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        print(e)


class DiagnosticStyle(QProxyStyle):
    def __init__(self) -> None:
        super().__init__()
        self.selected_widgets = []

    # highlight the selected widget
    def drawControl(
        self,
        element: QStyle.ControlElement,
        option: QStyleOption,
        painter: QPainter,
        widget: typing.Optional[QWidget] = ...,
    ) -> None:
        if widget in self.selected_widgets:
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.red))
            painter.drawRect(option.rect)
            painter.restore()
        super().drawControl(element, option, painter, widget)


class InspectTreeItem:
    """
    A class to hold the item and the associated item in the object tree
    """

    def __init__(self, object_tree_item):
        self.object_tree_item = object_tree_item

        label = object_tree_item.__class__.__name__
        self.tree_view_item = QTreeWidgetItem([label])

        if not hasattr(object_tree_item, "geometry"):
            self.tree_view_item.setForeground(0, Qt.GlobalColor.gray)

        self.children = []

    def add_child(self, object_tree_item):
        child = InspectTreeItem(object_tree_item)
        self.children.append(child)
        self.tree_view_item.addChild(child.tree_view_item)


class ReloadWindow(QMainWindow):
    def __init__(self, main_module, app):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setWindowTitle("Reloader")
        self.diagnostic_style = DiagnosticStyle()
        app.setStyle(self.diagnostic_style)

        import error_window

        def except_hook(type, value, traceback):
            self.main_window = error_window.ErrorWindow(type, value, traceback)
            self.setCentralWidget(self.main_window)
            self.copy_inner_window_attributes()

        sys.excepthook = except_hook

        self.main_module = main_module.__name__
        self.error_module = error_window.__name__
        self.main_window = main_module.MainWindow()

        try:
            with open("window_position.json", "r") as f:
                x, y = json.load(f).values()
                self.move(x, y)
        except:
            pass

        self.watcher = QFileSystemWatcher()
        self.watcher.addPath(".")
        self.watcher.directoryChanged.connect(self.on_directory_changed)
        self.watcher.fileChanged.connect(self.on_directory_changed)

        self.toolbar = QToolBar()
        self.toolbar.addAction("Hard restart", self.on_hard_restart_program)
        self.toolbar.addAction("Soft restart", self.soft_restart)
        self.toolbar.addSeparator()
        self.toolbar.addAction("Dump window geometry", self.dump_geometry)
        self.toolbar.addAction("Dump Object Tree", self.dump_object_tree)
        self.addToolBar(self.toolbar)

        self.copy_inner_window_attributes()
        self.setCentralWidget(self.main_window)
        self.setStyle(DiagnosticStyle())

        # Create a shortcut to Dump Object Tree
        self.dump_object_tree_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.dump_object_tree_shortcut.activated.connect(self.dump_object_tree)

        # Create a shortcut to hard restart
        self.hard_restart_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.hard_restart_shortcut.activated.connect(self.on_hard_restart_program)

    def dump_object_tree(self):
        # Create a new window
        self.inspect_window = QMainWindow()
        self.inspect_window.setWindowTitle("Object Tree")
        self.inspect_window.setMinimumSize(600, 700)

        # Delete on close
        self.inspect_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Create a shortcut to hard restart
        self.inspect_rs = QShortcut(QKeySequence("Ctrl+R"), self.inspect_window)
        self.inspect_rs.activated.connect(self.on_hard_restart_program)

        # Create a widget to hold the tree
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.inspect_window_highlighted_objects = []

        # Create a tree to hold the object tree
        self.inspect_window_tree = QTreeWidget()
        self.inspect_window_tree.setAnimated(True)
        self.inspect_window_tree.setAlternatingRowColors(True)
        self.inspect_window_tree.setHeaderLabels(["Object Tree"])
        self.inspect_window_tree.setFocus()
        self.inspect_window_tree.setStyleSheet("font-size: 22px;")

        self.inspect_window_tree.itemSelectionChanged.connect(
            self.on_tree_item_selection_changed
        )
        # Add the tree to the layout
        layout.addWidget(self.inspect_window_tree)

        self.inspect_window.setCentralWidget(widget)
        self.inspect_window_item_root = self.get_object_tree(self.main_window)
        self.inspect_window_tree.addTopLevelItem(
            self.inspect_window_item_root.tree_view_item
        )

        self.inspect_window.destroyed.connect(self.on_inspect_window_destroyed)
        self.inspect_window.show()

    def get_object_tree(self, obj: QWidget):
        """
        Get the object tree of an object as a dictionary
        """
        node = InspectTreeItem(obj)

        for child in node.object_tree_item.children():
            node.add_child(child)

        for child in node.children:
            self.get_object_tree_helper(child)

        return node

    def get_object_tree_helper(self, obj: InspectTreeItem):
        """
        Like `get_object_tree` but for the InspectTreeItem class
        """
        for child in obj.object_tree_item.children():
            obj.add_child(child)

        for child in obj.children:
            self.get_object_tree_helper(child)

    def create_tree_item(self, obj, children):
        """
        Create a tree item for an object
        """
        name = obj.__class__.__name__
        item = QTreeWidgetItem([name])
        item.obj = obj
        for child in children:
            for child_item, grandchildren in child.items():
                item.addChild(self.create_tree_item(child_item, grandchildren))
        return item

    def highlight_object(self, obj):
        if not hasattr(obj, "geometry"):
            return
        else:
            self.diagnostic_style.selected_widgets.append(obj)
            self.main_window.update()

    def on_inspect_window_destroyed(self):
        self.diagnostic_style.selected_widgets = []

    def on_tree_item_selection_changed(self):
        """
        When the selection changes in the tree, highlight the object
        """
        selected_items = self.inspect_window_tree.selectedItems()
        self.diagnostic_style.selected_widgets = []

        for selected_item in selected_items:
            inspect_item = self.find_inspect_item(selected_item)
            if inspect_item:
                self.highlight_object(inspect_item.object_tree_item)

    def find_inspect_item(self, tree_item):
        """
        Find the InspectTreeItem corresponding to a tree item
        """
        return self.find_inspect_item_helper(self.inspect_window_item_root, tree_item)

    def find_inspect_item_helper(self, inspect_item, tree_item):
        """
        Recursive helper function for `find_inspect_item`
        """
        if inspect_item.tree_view_item == tree_item:
            return inspect_item
        for child in inspect_item.children:
            result = self.find_inspect_item_helper(child, tree_item)
            if result:
                return result

    def dump_geometry(self):
        print("Window geometry:", self.geometry())
        print("Frame geometry:", self.frameGeometry())

    def copy_inner_window_attributes(self):
        """
        Copy the attributes of the inner (actual) window to the outer (reloader) window
        Highly likely there's stuff missing, just going to patch it in as we go along.
        """
        self.setMinimumHeight(self.main_window.minimumHeight())
        self.setMinimumWidth(self.main_window.minimumWidth())

        self.setMaximumHeight(self.main_window.maximumHeight())
        self.setMaximumWidth(self.main_window.maximumWidth())

        self.resize(self.main_window.size())
        self.setWindowTitle(self.main_window.windowTitle())

        self.setWindowFlags(self.main_window.windowFlags())
        self.show()

    def on_hard_restart_program(self):
        x = self.geometry().x()

        offset = self.geometry().y() - self.frameGeometry().y()
        y = self.geometry().y() - offset

        with open("window_position.json", "w") as f:
            f.write(f'{{"x": {x}, "y": {y}}}')

        hard_restart_program()

    def on_directory_changed(self, path):
        self.soft_restart()

    def soft_restart(self):
        """
        Check every non-library and non-standard-library module for changes.
        If there are changes, reload them.
        """
        reload(sys.modules[self.error_module])

        to_reload = []
        for module, module_type in sys.modules.items():
            if not hasattr(module_type, "__file__"):
                continue
            if module_type.__file__ is None:
                continue
            if module_type.__file__.startswith(sys.prefix):
                continue
            if module_type.__file__.startswith(sys.base_prefix):
                continue
            if module_type.__name__ == "__main__":
                continue

            to_reload.append(module_type.__name__)

        for module in to_reload:
            reload(sys.modules[module])
        self.main_window = sys.modules[self.main_module].MainWindow()

        self.copy_inner_window_attributes()
        self.setCentralWidget(self.main_window)
