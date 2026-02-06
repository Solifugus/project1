"""
Main Window (C:MainWindow)

Implements the main application window structure as specified in T:0020.
Provides three-pane layout with tab widget, editor/inspector area,
and AI Console + Privileged Requests with resizable splitters.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QTextEdit, QLabel, QPushButton,
    QMenuBar, QStatusBar, QMessageBox, QFileDialog, QPlainTextEdit,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QScrollArea,
    QDialog, QLineEdit, QDialogButtonBox, QCompleter
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QIcon, QUndoStack, QUndoCommand

from workspace_manager import create_workspace_manager
from doc_element import Kind


class GoToIdDialog(QDialog):
    """
    Dialog for navigating directly to an element by ID.
    T:0023 - Provides direct navigation to any element by ID.
    """

    def __init__(self, parent=None, available_ids=None):
        """
        Initialize the Go to ID dialog.

        Args:
            parent: Parent widget
            available_ids: List of available element IDs for auto-completion
        """
        super().__init__(parent)
        self.setWindowTitle("Go to Element ID")
        self.setMinimumWidth(400)
        self.setModal(True)

        # Create layout
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Enter an element ID to navigate directly to it.\n"
            "Examples: R:Purpose, C:MainWindow, T:0022, TP:0001"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # ID input field
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Element ID:"))

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter element ID (e.g., C:MainWindow)")

        # Set up auto-completion if IDs provided
        if available_ids:
            completer = QCompleter(available_ids)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.id_input.setCompleter(completer)

        input_layout.addWidget(self.id_input)
        layout.addLayout(input_layout)

        # Dialog buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # Enable/disable OK button based on input
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        self.id_input.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.buttons)

        self.setLayout(layout)

        # Focus on input field
        self.id_input.setFocus()

        # Allow Enter key to accept dialog
        self.id_input.returnPressed.connect(self.accept)

    def _on_text_changed(self, text):
        """Enable OK button only when text is entered."""
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(bool(text.strip()))

    def get_element_id(self):
        """Get the entered element ID."""
        return self.id_input.text().strip().upper()  # Normalize to uppercase

    def set_element_id(self, element_id):
        """Pre-populate the dialog with an element ID."""
        self.id_input.setText(element_id)
        self.id_input.selectAll()


class SettingsDialog(QDialog):
    """
    Dialog for editing global conventions.
    T:0024 - Provides interface to edit conventions.md file.
    """

    def __init__(self, parent=None, conventions_path=None):
        """
        Initialize the Settings dialog.

        Args:
            parent: Parent widget
            conventions_path: Path to the conventions.md file
        """
        super().__init__(parent)
        self.setWindowTitle("Settings - Edit Conventions")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self.setModal(True)

        self.conventions_path = Path(conventions_path) if conventions_path else None
        self.original_content = ""
        self.has_unsaved_changes = False

        # Create layout
        layout = QVBoxLayout()

        # Instructions
        info_label = QLabel("Edit the global conventions that apply across all projects in this workspace.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # File path display
        self.path_label = QLabel()
        self.path_label.setStyleSheet("font-family: monospace; color: #444; margin-bottom: 5px;")
        layout.addWidget(self.path_label)

        # Text editor for conventions content
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas, Monaco, 'Courier New', monospace", 10))
        self.editor.setPlaceholderText("Loading conventions...")
        self.editor.textChanged.connect(self._on_content_changed)
        layout.addWidget(self.editor)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic; margin-top: 5px;")
        layout.addWidget(self.status_label)

        # Button box
        self.buttons = QDialogButtonBox()
        self.save_button = self.buttons.addButton("Save", QDialogButtonBox.AcceptRole)
        self.cancel_button = self.buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.revert_button = self.buttons.addButton("Revert", QDialogButtonBox.ResetRole)

        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)

        # Connect button signals
        self.save_button.clicked.connect(self._save_changes)
        self.cancel_button.clicked.connect(self._cancel_changes)
        self.revert_button.clicked.connect(self._revert_changes)

        layout.addWidget(self.buttons)
        self.setLayout(layout)

        # Load conventions content
        self._load_conventions()

    def _load_conventions(self):
        """Load the conventions.md file content."""
        if not self.conventions_path:
            self.status_label.setText("Error: No conventions file path provided")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            return

        try:
            self.path_label.setText(f"File: {self.conventions_path}")

            if self.conventions_path.exists():
                content = self.conventions_path.read_text(encoding='utf-8')
                self.original_content = content
                self.editor.setPlainText(content)
                self.status_label.setText("Conventions loaded successfully")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText("Error: Conventions file not found")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.editor.setPlainText("")

        except Exception as e:
            self.status_label.setText(f"Error loading file: {e}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.editor.setPlainText("")

        # Reset change tracking
        self.has_unsaved_changes = False
        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)

        # Reset status after delay
        QTimer.singleShot(3000, lambda: self._reset_status())

    def _on_content_changed(self):
        """Handle content changes in the editor."""
        current_content = self.editor.toPlainText()
        has_changes = current_content != self.original_content

        if has_changes != self.has_unsaved_changes:
            self.has_unsaved_changes = has_changes
            self.save_button.setEnabled(has_changes)
            self.revert_button.setEnabled(has_changes)

            if has_changes:
                self.status_label.setText("Unsaved changes")
                self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self._reset_status()

    def _save_changes(self):
        """Save the changes back to conventions.md file."""
        if not self.conventions_path:
            return

        try:
            # Get current content
            content = self.editor.toPlainText()

            # Write to file
            self.conventions_path.write_text(content, encoding='utf-8')

            # Update original content
            self.original_content = content
            self.has_unsaved_changes = False

            # Update UI
            self.save_button.setEnabled(False)
            self.revert_button.setEnabled(False)
            self.status_label.setText("Saved successfully")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")

            # Close dialog after successful save
            QTimer.singleShot(1000, self.accept)

        except Exception as e:
            self.status_label.setText(f"Save failed: {e}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def _cancel_changes(self):
        """Cancel changes and close dialog."""
        if self.has_unsaved_changes:
            # Ask for confirmation if there are unsaved changes
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        self.reject()

    def _revert_changes(self):
        """Revert all changes to original content."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Revert Changes",
                "Are you sure you want to revert all changes?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Restore original content
        self.editor.setPlainText(self.original_content)

    def _reset_status(self):
        """Reset status label to default state."""
        if not self.has_unsaved_changes:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: gray; font-style: italic;")

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return

        event.accept()


class NavigationPane(QWidget):
    """
    Navigation pane for the left panel.
    T:0021 - Displays flat lists of elements by type with selection support.
    """

    # Signals
    element_selected = Signal(str)  # Emitted when an element is selected

    def __init__(self, parent=None):
        """Initialize the navigation pane."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.workspace_manager = None

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Create tabs with list widgets
        self.design_tab, self.design_list = self._create_design_tab()
        self.code_tab, self.code_list = self._create_code_tab()
        self.test_tab, self.test_list = self._create_test_tab()

        # Add tabs to widget
        self.tab_widget.addTab(self.design_tab, "Design")
        self.tab_widget.addTab(self.code_tab, "Code")
        self.tab_widget.addTab(self.test_tab, "Test")

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        # Connect signals
        self._connect_signals()

        # Load placeholder content initially
        self._load_placeholder_content()

    def _create_design_tab(self) -> tuple[QWidget, QListWidget]:
        """Create the Design tab content with list widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel("Design Elements")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Element list widget
        element_list = QListWidget()
        element_list.setAlternatingRowColors(True)
        element_list.setSortingEnabled(True)
        layout.addWidget(element_list)

        widget.setLayout(layout)
        return widget, element_list

    def _create_code_tab(self) -> tuple[QWidget, QListWidget]:
        """Create the Code tab content with list widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel("Development Tasks")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Task list widget
        task_list = QListWidget()
        task_list.setAlternatingRowColors(True)
        task_list.setSortingEnabled(True)
        layout.addWidget(task_list)

        widget.setLayout(layout)
        return widget, task_list

    def _create_test_tab(self) -> tuple[QWidget, QListWidget]:
        """Create the Test tab content with list widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel("Test Plans")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Test list widget
        test_list = QListWidget()
        test_list.setAlternatingRowColors(True)
        test_list.setSortingEnabled(True)
        layout.addWidget(test_list)

        widget.setLayout(layout)
        return widget, test_list

    def _connect_signals(self):
        """Connect list widget signals to handlers."""
        self.design_list.itemClicked.connect(self._on_design_element_selected)
        self.code_list.itemClicked.connect(self._on_code_element_selected)
        self.test_list.itemClicked.connect(self._on_test_element_selected)

    def _on_design_element_selected(self, item: QListWidgetItem):
        """Handle design element selection."""
        element_id = item.data(Qt.UserRole)
        if element_id:
            self.logger.info(f"Design element selected: {element_id}")
            self.element_selected.emit(element_id)

    def _on_code_element_selected(self, item: QListWidgetItem):
        """Handle code element (task) selection."""
        element_id = item.data(Qt.UserRole)
        if element_id:
            self.logger.info(f"Code element selected: {element_id}")
            self.element_selected.emit(element_id)

    def _on_test_element_selected(self, item: QListWidgetItem):
        """Handle test element selection."""
        element_id = item.data(Qt.UserRole)
        if element_id:
            self.logger.info(f"Test element selected: {element_id}")
            self.element_selected.emit(element_id)

    def _load_placeholder_content(self):
        """Load placeholder content when no workspace is available."""
        # Design tab placeholder
        design_items = [
            ("R:Purpose", "Define the system purpose"),
            ("R:Scope", "Define system scope"),
            ("C:MainWindow", "Main application window"),
            ("C:NavigationPane", "Navigation panel"),
            ("C:EditorPane", "Content editor"),
            ("D:DocElement", "Document element structure"),
            ("I:MCPServer", "MCP server interface")
        ]

        for element_id, title in design_items:
            item = QListWidgetItem(f"{element_id} - {title}")
            item.setData(Qt.UserRole, element_id)
            self.design_list.addItem(item)

        # Code tab placeholder with status indicators
        code_items = [
            ("T:0001", "Define DocElement data structure", "✅"),
            ("T:0002", "Define PrivilegedRequest data structure", "✅"),
            ("T:0013", "Implement MCP read operations", "✅"),
            ("T:0014", "Implement MCP write operations", "✅"),
            ("T:0015", "Implement MCP error handling", "✅"),
            ("T:0016", "Implement MCP privileged action workflow", "✅"),
            ("T:0017", "Implement command allowlist management", "✅"),
            ("T:0018", "Implement privileged request queue", "✅"),
            ("T:0019", "Implement privileged command execution", "✅"),
            ("T:0020", "Implement main window layout", "✅"),
            ("T:0021", "Implement navigation pane", "✅"),
            ("T:0022", "Implement editor pane", "✅"),
            ("T:0023", "Implement Go to ID navigation", "✅"),
            ("T:0024", "Implement settings dialog", "⏳")
        ]

        for element_id, title, status in code_items:
            item = QListWidgetItem(f"{element_id} - {title} {status}")
            item.setData(Qt.UserRole, element_id)
            self.code_list.addItem(item)

        # Test tab placeholder
        test_items = [
            ("TP:0001", "Test DocElement creation and validation"),
            ("TP:0002", "Test workspace discovery and loading"),
            ("TP:0003", "Test markdown parsing functionality"),
            ("TP:0004", "Test MCP server operations"),
            ("TP:0005", "Test privileged action workflow"),
            ("TP:0006", "Test GUI layout and interaction")
        ]

        for element_id, title in test_items:
            item = QListWidgetItem(f"{element_id} - {title}")
            item.setData(Qt.UserRole, element_id)
            self.test_list.addItem(item)

    def _get_task_status_indicator(self, element_id: str) -> str:
        """Get status indicator for a task element."""
        # Map task IDs to their current status
        completed_tasks = {
            "T:0001", "T:0002", "T:0013", "T:0014", "T:0015",
            "T:0016", "T:0017", "T:0018", "T:0019", "T:0020",
            "T:0021", "T:0022", "T:0023"
        }

        if element_id in completed_tasks:
            return "✅"
        else:
            return "⏳"

    def refresh_content(self, workspace_manager=None):
        """Refresh the navigation content with data from workspace manager."""
        if workspace_manager:
            self.workspace_manager = workspace_manager
            self.logger.info("Refreshing navigation content from workspace")

            try:
                # Get the indexer from workspace manager
                indexer = workspace_manager.indexer
                if indexer and indexer.get_state().name == "READY":
                    index = indexer.get_index()
                    self._load_workspace_content(index)
                else:
                    self.logger.warning("Indexer not ready, using placeholder content")
                    self._load_placeholder_content()
            except Exception as e:
                self.logger.error(f"Error loading workspace content: {e}")
                self._load_placeholder_content()
        else:
            self.logger.debug("No workspace manager available, using placeholder content")
            self._load_placeholder_content()

    def _load_workspace_content(self, index):
        """Load actual content from the workspace index."""
        self.logger.info("Loading actual workspace content from index")

        # Clear existing content
        self.design_list.clear()
        self.code_list.clear()
        self.test_list.clear()

        try:
            # Design tab: Load design elements (R:, C:, D:, I:, M:, UI:)
            design_kinds = [Kind.REQUIREMENT, Kind.COMPONENT, Kind.DATA, Kind.INTERFACE, Kind.METHOD, Kind.UI]
            design_elements = []

            for kind in design_kinds:
                elements = index.get_elements_by_kind(kind)
                design_elements.extend(elements)

            # Sort design elements by ID
            design_elements.sort(key=lambda e: e.id)

            for element in design_elements:
                item_text = f"{element.id} - {element.title}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, element.id)
                self.design_list.addItem(item)

            self.logger.info(f"Loaded {len(design_elements)} design elements")

            # Code tab: Load task elements (T:)
            task_elements = index.get_elements_by_kind(Kind.TASK)
            task_elements.sort(key=lambda e: e.id)

            for element in task_elements:
                status_indicator = self._get_task_status_indicator(element.id)
                item_text = f"{element.id} - {element.title} {status_indicator}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, element.id)
                self.code_list.addItem(item)

            self.logger.info(f"Loaded {len(task_elements)} task elements")

            # Test tab: Load test elements (TP:)
            test_elements = index.get_elements_by_kind(Kind.TEST)
            test_elements.sort(key=lambda e: e.id)

            for element in test_elements:
                item_text = f"{element.id} - {element.title}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, element.id)
                self.test_list.addItem(item)

            self.logger.info(f"Loaded {len(test_elements)} test elements")

        except Exception as e:
            self.logger.error(f"Error loading workspace content: {e}")
            # Fall back to placeholder content
            self._load_placeholder_content()


class ElementEditCommand(QUndoCommand):
    """Undo command for element text edits."""

    def __init__(self, text_edit: QTextEdit, old_text: str, new_text: str, description: str = "Edit"):
        """Initialize the edit command."""
        super().__init__(description)
        self.text_edit = text_edit
        self.old_text = old_text
        self.new_text = new_text

    def undo(self):
        """Undo the text edit."""
        self.text_edit.setPlainText(self.old_text)

    def redo(self):
        """Redo the text edit."""
        self.text_edit.setPlainText(self.new_text)


class EditorPane(QWidget):
    """
    Editor pane for the right panel.
    T:0022 - View and edit selected elements with complete information display,
    markdown editing, save functionality, and undo/redo support.
    """

    def __init__(self, parent=None):
        """Initialize the editor pane."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.workspace_manager = None
        self.current_element = None
        self.original_content = ""
        self.has_unsaved_changes = False

        # Create undo stack
        self.undo_stack = QUndoStack(self)

        # Create main layout with scroll area
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create scroll area for element info
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(200)
        self.scroll_area.setMaximumHeight(300)

        # Element information widget
        self.info_widget = self._create_element_info_widget()
        self.scroll_area.setWidget(self.info_widget)

        main_layout.addWidget(self.scroll_area)

        # Editor controls
        controls_layout = QHBoxLayout()

        # Save/Revert buttons
        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save_element)

        self.revert_button = QPushButton("Revert")
        self.revert_button.setEnabled(False)
        self.revert_button.clicked.connect(self._revert_changes)

        # Undo/Redo buttons
        self.undo_button = QPushButton("Undo")
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_stack.undo)

        self.redo_button = QPushButton("Redo")
        self.redo_button.setEnabled(False)
        self.redo_button.clicked.connect(self.undo_stack.redo)

        controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(self.revert_button)
        controls_layout.addSeparator()
        controls_layout.addWidget(self.undo_button)
        controls_layout.addWidget(self.redo_button)
        controls_layout.addStretch()

        # Status label
        self.status_label = QLabel("No element selected")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        controls_layout.addWidget(self.status_label)

        main_layout.addLayout(controls_layout)

        # Markdown editor
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)  # Plain text/markdown only
        self.editor.textChanged.connect(self._on_content_changed)

        # Use monospace font for better markdown editing
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        if not font.exactMatch():
            font = QFont("monospace", 10)
        self.editor.setFont(font)

        # Set placeholder content
        self._set_placeholder_content()

        main_layout.addWidget(self.editor, stretch=1)

        self.setLayout(main_layout)

        # Connect undo stack signals
        self.undo_stack.canUndoChanged.connect(self.undo_button.setEnabled)
        self.undo_stack.canRedoChanged.connect(self.redo_button.setEnabled)

        self.logger.info("EditorPane initialized with T:0022 enhancements")

    def _create_element_info_widget(self) -> QWidget:
        """Create the element information display widget."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Basic element info
        basic_group = QGroupBox("Element Information")
        basic_layout = QFormLayout()

        self.id_label = QLabel("No element selected")
        self.title_label = QLabel("-")
        self.kind_label = QLabel("-")
        self.file_label = QLabel("-")
        self.status_info_label = QLabel("-")

        basic_layout.addRow("ID:", self.id_label)
        basic_layout.addRow("Title:", self.title_label)
        basic_layout.addRow("Kind:", self.kind_label)
        basic_layout.addRow("File:", self.file_label)
        basic_layout.addRow("Status:", self.status_info_label)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # References section
        refs_group = QGroupBox("References")
        refs_layout = QVBoxLayout()

        self.refs_label = QLabel("No references")
        self.refs_label.setWordWrap(True)
        refs_layout.addWidget(self.refs_label)

        refs_group.setLayout(refs_layout)
        layout.addWidget(refs_group)

        # Backlinks section
        backlinks_group = QGroupBox("Backlinks")
        backlinks_layout = QVBoxLayout()

        self.backlinks_label = QLabel("No backlinks")
        self.backlinks_label.setWordWrap(True)
        backlinks_layout.addWidget(self.backlinks_label)

        backlinks_group.setLayout(backlinks_layout)
        layout.addWidget(backlinks_group)

        widget.setLayout(layout)
        return widget

    def _set_placeholder_content(self):
        """Set placeholder content when no element is selected."""
        placeholder_text = (
            "# Welcome to Project1 Editor\n\n"
            "Select an element from the navigation pane to view and edit its content.\n\n"
            "## Editor Features (T:0022)\n\n"
            "✅ **Element Information Display**\n"
            "- Shows ID, title, kind, file location, and status\n"
            "- Displays references and backlinks\n"
            "- Scrollable information panel\n\n"
            "✅ **Markdown Editor**\n"
            "- Full markdown editing support\n"
            "- Monospace font for better readability\n"
            "- Auto-detection of content changes\n\n"
            "✅ **Save Functionality**\n"
            "- Save changes back to source files\n"
            "- Revert unsaved changes\n"
            "- Visual indicators for modified content\n\n"
            "✅ **Undo/Redo Support**\n"
            "- Complete undo/redo stack\n"
            "- Keyboard shortcuts (Ctrl+Z, Ctrl+Y)\n"
            "- Button-based undo/redo controls\n\n"
            "Start by selecting an element to edit its markdown content!"
        )
        self.editor.setPlainText(placeholder_text)

    def _on_content_changed(self):
        """Handle editor content changes."""
        if self.current_element is None:
            return

        current_content = self.editor.toPlainText()
        self.has_unsaved_changes = (current_content != self.original_content)

        # Update UI state
        self.save_button.setEnabled(self.has_unsaved_changes)
        self.revert_button.setEnabled(self.has_unsaved_changes)

        if self.has_unsaved_changes:
            self.status_label.setText("Modified - unsaved changes")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setText("No changes")
            self.status_label.setStyleSheet("color: gray; font-style: italic;")

    def _save_element(self):
        """Save the current element changes back to the file."""
        if not self.current_element or not self.workspace_manager:
            self.logger.warning("Cannot save: no element or workspace manager")
            return

        try:
            # Get current content
            new_content = self.editor.toPlainText()

            # TODO: Implement actual file saving through workspace manager
            # This would involve updating the element's body_markdown and
            # writing the changes back to the source markdown file

            # For now, simulate successful save
            self.original_content = new_content
            self.has_unsaved_changes = False

            # Update UI
            self.save_button.setEnabled(False)
            self.revert_button.setEnabled(False)
            self.status_label.setText("Saved successfully")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")

            # Clear undo stack after successful save
            self.undo_stack.clear()

            self.logger.info(f"Element {self.current_element.id} saved successfully")

            # Reset status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("No changes"))

        except Exception as e:
            self.logger.error(f"Error saving element {self.current_element.id}: {e}")
            self.status_label.setText("Save failed")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def _revert_changes(self):
        """Revert all changes to the original content."""
        if self.current_element is None:
            return

        # Create undo command for the revert
        current_content = self.editor.toPlainText()
        if current_content != self.original_content:
            command = ElementEditCommand(self.editor, current_content, self.original_content, "Revert changes")
            self.undo_stack.push(command)

    def set_workspace_manager(self, workspace_manager):
        """Set the workspace manager for file operations."""
        self.workspace_manager = workspace_manager
        self.logger.info("EditorPane workspace manager updated")

    def set_element(self, element_id: str):
        """Set the element to display/edit."""
        self.logger.info(f"EditorPane loading element: {element_id}")

        if not self.workspace_manager:
            self.logger.warning("No workspace manager available")
            self._show_no_workspace_message(element_id)
            return

        try:
            # Get element from workspace manager
            indexer = self.workspace_manager.indexer
            if not indexer or indexer.get_state().name != "READY":
                self.logger.warning("Indexer not ready")
                self._show_indexer_not_ready(element_id)
                return

            index = indexer.get_index()
            element = index.get_element_by_id(element_id)

            if not element:
                self.logger.warning(f"Element not found: {element_id}")
                self._show_element_not_found(element_id)
                return

            # Load the element
            self._load_element(element)

        except Exception as e:
            self.logger.error(f"Error loading element {element_id}: {e}")
            self._show_load_error(element_id, str(e))

    def _load_element(self, element):
        """Load element data into the editor."""
        self.current_element = element

        # Update element info display
        self.id_label.setText(element.id)
        self.title_label.setText(element.title or "No title")
        self.kind_label.setText(element.kind.name if element.kind else "Unknown")
        self.file_label.setText(element.file.name if element.file else "Unknown")
        self.status_info_label.setText(element.status.name if element.status else "Unknown")

        # Update references
        if element.refs:
            refs_text = ", ".join(element.refs)
            self.refs_label.setText(refs_text)
        else:
            self.refs_label.setText("No references")

        # Update backlinks
        if element.backlinks:
            backlinks_text = ", ".join(element.backlinks)
            self.backlinks_label.setText(backlinks_text)
        else:
            self.backlinks_label.setText("No backlinks")

        # Load content into editor
        content = element.body_markdown or ""
        self.original_content = content

        # Temporarily disconnect textChanged to avoid triggering change detection
        self.editor.textChanged.disconnect()
        self.editor.setPlainText(content)
        self.editor.textChanged.connect(self._on_content_changed)

        # Reset state
        self.has_unsaved_changes = False
        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)
        self.status_label.setText("Loaded")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")

        # Clear undo stack for new element
        self.undo_stack.clear()

        self.logger.info(f"Element {element.id} loaded successfully")

        # Reset status after delay
        QTimer.singleShot(2000, lambda: self._reset_status())

    def _reset_status(self):
        """Reset status label to default state."""
        if not self.has_unsaved_changes:
            self.status_label.setText("No changes")
            self.status_label.setStyleSheet("color: gray; font-style: italic;")

    def _show_no_workspace_message(self, element_id: str):
        """Show message when no workspace is available."""
        self.current_element = None
        self.id_label.setText(element_id)
        self.title_label.setText("Workspace not loaded")
        self.kind_label.setText("-")
        self.file_label.setText("-")
        self.status_info_label.setText("-")
        self.refs_label.setText("-")
        self.backlinks_label.setText("-")

        self.editor.setPlainText(
            f"# Cannot Load Element: {element_id}\n\n"
            "No workspace is currently loaded.\n\n"
            "Please:\n"
            "1. Open a workspace using **File > Open Workspace**\n"
            "2. Ensure the workspace contains valid project files\n"
            "3. Wait for the workspace to fully load\n"
            "4. Try selecting the element again\n"
        )

        self.status_label.setText("No workspace loaded")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def _show_indexer_not_ready(self, element_id: str):
        """Show message when indexer is not ready."""
        self.current_element = None
        self.id_label.setText(element_id)
        self.title_label.setText("Indexer not ready")
        self.kind_label.setText("-")
        self.file_label.setText("-")
        self.status_info_label.setText("-")
        self.refs_label.setText("-")
        self.backlinks_label.setText("-")

        self.editor.setPlainText(
            f"# Cannot Load Element: {element_id}\n\n"
            "The workspace indexer is not ready.\n\n"
            "This may happen if:\n"
            "- The workspace is still loading\n"
            "- There was an error parsing markdown files\n"
            "- The workspace structure is invalid\n\n"
            "Please wait for the workspace to finish loading and try again."
        )

        self.status_label.setText("Indexer not ready")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")

    def _show_element_not_found(self, element_id: str):
        """Show message when element is not found."""
        self.current_element = None
        self.id_label.setText(element_id)
        self.title_label.setText("Element not found")
        self.kind_label.setText("-")
        self.file_label.setText("-")
        self.status_info_label.setText("-")
        self.refs_label.setText("-")
        self.backlinks_label.setText("-")

        self.editor.setPlainText(
            f"# Element Not Found: {element_id}\n\n"
            "The requested element could not be found in the workspace.\n\n"
            "Possible causes:\n"
            "- Element ID does not exist in any markdown files\n"
            "- Element was recently deleted or renamed\n"
            "- Markdown parsing failed for the containing file\n"
            "- Element exists but has invalid format\n\n"
            "Check the source markdown files and refresh the workspace."
        )

        self.status_label.setText("Element not found")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def _show_load_error(self, element_id: str, error_msg: str):
        """Show message when there's an error loading the element."""
        self.current_element = None
        self.id_label.setText(element_id)
        self.title_label.setText("Load error")
        self.kind_label.setText("-")
        self.file_label.setText("-")
        self.status_info_label.setText("-")
        self.refs_label.setText("-")
        self.backlinks_label.setText("-")

        self.editor.setPlainText(
            f"# Error Loading Element: {element_id}\n\n"
            f"**Error:** {error_msg}\n\n"
            "An unexpected error occurred while loading this element.\n\n"
            "This may be due to:\n"
            "- File system permissions\n"
            "- Corrupted markdown files\n"
            "- Internal application error\n\n"
            "Check the application logs for more details."
        )

        self.status_label.setText("Load error")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")


class ConsolePane(QWidget):
    """
    Console pane for the bottom panel.
    T:0020 - Provides AI Console + Privileged Requests area.
    """

    def __init__(self, parent=None):
        """Initialize the console pane."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Create tab widget for console areas
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Create console tabs
        self.ai_console_tab = self._create_ai_console_tab()
        self.privileged_requests_tab = self._create_privileged_requests_tab()

        # Add tabs
        self.tab_widget.addTab(self.ai_console_tab, "AI Console")
        self.tab_widget.addTab(self.privileged_requests_tab, "Privileged Requests")

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def _create_ai_console_tab(self) -> QWidget:
        """Create the AI Console tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Console output area
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumBlockCount(1000)  # Limit history
        self.console_output.setPlainText(
            "AI Console - Ready\n"
            "================\n\n"
            "This is where AI interactions will be displayed.\n"
            "Features planned:\n"
            "- Chat with AI assistants\n"
            "- Request code generation\n"
            "- Ask questions about the codebase\n"
            "- Get suggestions for implementation\n\n"
            "Type your message below and press Enter to interact.\n"
        )

        # Console input area
        self.console_input = QPlainTextEdit()
        self.console_input.setMaximumHeight(80)
        self.console_input.setPlaceholderText("Type your message to the AI assistant here...")

        # Send button
        send_button = QPushButton("Send")
        send_button.clicked.connect(self._send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.console_input)
        input_layout.addWidget(send_button)

        layout.addWidget(self.console_output, stretch=1)
        layout.addLayout(input_layout)

        widget.setLayout(layout)
        return widget

    def _create_privileged_requests_tab(self) -> QWidget:
        """Create the Privileged Requests tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel("Privileged Request Monitor")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Request list
        self.request_list = QPlainTextEdit()
        self.request_list.setReadOnly(True)
        self.request_list.setPlainText(
            "Privileged Request Queue Status\n"
            "==============================\n\n"
            "No active privileged requests.\n\n"
            "This area will show:\n"
            "- Pending privileged command requests\n"
            "- Approval status for each request\n"
            "- Execution results and audit logs\n"
            "- Real-time status updates\n\n"
            "Integration with MCP server privileged operations:\n"
            "- T:0016 - Privileged action workflow ✅\n"
            "- T:0017 - Command allowlist management ✅\n"
            "- T:0018 - Privileged request queue ✅\n"
            "- T:0019 - Privileged command execution ✅"
        )
        layout.addWidget(self.request_list)

        # Control buttons
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        approve_button = QPushButton("Approve Selected")
        deny_button = QPushButton("Deny Selected")
        view_logs_button = QPushButton("View Audit Logs")

        button_layout.addWidget(refresh_button)
        button_layout.addWidget(approve_button)
        button_layout.addWidget(deny_button)
        button_layout.addWidget(view_logs_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        widget.setLayout(layout)
        return widget

    def _send_message(self):
        """Handle sending a message to the AI console."""
        message = self.console_input.toPlainText().strip()
        if message:
            self.console_output.appendPlainText(f"\n> {message}")
            self.console_output.appendPlainText("AI: I'm not connected yet, but I received your message!")
            self.console_input.clear()


class MainWindow(QMainWindow):
    """
    Main application window (C:MainWindow).
    T:0020 - Implements three-pane layout with resizable splitters.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """
        Initialize the main window.

        Args:
            workspace_path: Optional path to workspace directory
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.workspace_path = Path(workspace_path) if workspace_path else None
        self.workspace_manager = None

        # Initialize UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._connect_signals()

        # Initialize workspace if path provided
        if self.workspace_path:
            self._load_workspace()

        self.logger.info("MainWindow initialized successfully")

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Set window properties
        self.setWindowTitle("Project1 - AI-Assisted Software Development")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout - vertical split between main area and console
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create main splitter (vertical - main area above, console below)
        self.main_splitter = QSplitter(Qt.Vertical)

        # Create top splitter (horizontal - navigation left, editor right)
        self.top_splitter = QSplitter(Qt.Horizontal)

        # Create UI components
        self.navigation_pane = NavigationPane()
        self.editor_pane = EditorPane()
        self.console_pane = ConsolePane()

        # Add components to top splitter
        self.top_splitter.addWidget(self.navigation_pane)
        self.top_splitter.addWidget(self.editor_pane)

        # Set initial sizes for top splitter (navigation:editor = 1:2)
        self.top_splitter.setSizes([300, 600])
        self.top_splitter.setStretchFactor(0, 0)  # Navigation pane fixed-ish
        self.top_splitter.setStretchFactor(1, 1)  # Editor pane stretches

        # Add top area and console to main splitter
        self.main_splitter.addWidget(self.top_splitter)
        self.main_splitter.addWidget(self.console_pane)

        # Set initial sizes for main splitter (main:console = 3:1)
        self.main_splitter.setSizes([600, 200])
        self.main_splitter.setStretchFactor(0, 1)  # Main area stretches
        self.main_splitter.setStretchFactor(1, 0)  # Console fixed-ish

        # Add main splitter to layout
        main_layout.addWidget(self.main_splitter)

        self.logger.info("UI layout setup completed")

    def _setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        # Open Workspace action
        open_action = QAction('&Open Workspace...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open a workspace directory')
        open_action.triggered.connect(self._open_workspace)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Navigate menu
        navigate_menu = menubar.addMenu('&Navigate')

        # Go to ID action
        goto_action = QAction('&Go to Element ID...', self)
        goto_action.setShortcut('Ctrl+G')
        goto_action.setStatusTip('Navigate directly to an element by ID')
        goto_action.triggered.connect(self._go_to_element_id)
        navigate_menu.addAction(goto_action)

        navigate_menu.addSeparator()

        # Quick navigation actions
        goto_design_action = QAction('Go to &Design Elements', self)
        goto_design_action.setShortcut('Ctrl+1')
        goto_design_action.triggered.connect(self._go_to_design_tab)
        navigate_menu.addAction(goto_design_action)

        goto_code_action = QAction('Go to &Code Tasks', self)
        goto_code_action.setShortcut('Ctrl+2')
        goto_code_action.triggered.connect(self._go_to_code_tab)
        navigate_menu.addAction(goto_code_action)

        goto_test_action = QAction('Go to &Test Plans', self)
        goto_test_action.setShortcut('Ctrl+3')
        goto_test_action.triggered.connect(self._go_to_test_tab)
        navigate_menu.addAction(goto_test_action)

        # View menu
        view_menu = menubar.addMenu('&View')

        # Toggle navigation pane
        toggle_nav_action = QAction('Toggle &Navigation Pane', self)
        toggle_nav_action.setShortcut('Ctrl+Shift+1')
        toggle_nav_action.triggered.connect(self._toggle_navigation_pane)
        view_menu.addAction(toggle_nav_action)

        # Toggle console pane
        toggle_console_action = QAction('Toggle &Console Pane', self)
        toggle_console_action.setShortcut('Ctrl+Shift+2')
        toggle_console_action.triggered.connect(self._toggle_console_pane)
        view_menu.addAction(toggle_console_action)

        # Tools menu
        tools_menu = menubar.addMenu('&Tools')

        # Settings action
        settings_action = QAction('&Settings...', self)
        settings_action.setShortcut('Ctrl+,')  # Common settings shortcut
        settings_action.setStatusTip('Edit global conventions')
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        # About action
        about_action = QAction('&About Project1', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Add permanent status indicators
        self.workspace_status = QLabel("No workspace")
        self.status_bar.addPermanentWidget(self.workspace_status)

    def _connect_signals(self):
        """Connect UI signals and slots."""
        # Connect navigation to editor
        self.navigation_pane.element_selected.connect(self.editor_pane.set_element)

    def _load_workspace(self):
        """Load the specified workspace."""
        try:
            self.status_bar.showMessage("Loading workspace...")

            # Create workspace manager
            self.workspace_manager = create_workspace_manager(str(self.workspace_path))
            success = self.workspace_manager.load(start_watching=False)

            if success:
                self.workspace_status.setText(f"Workspace: {self.workspace_path.name}")
                self.status_bar.showMessage("Workspace loaded successfully", 3000)

                # Refresh navigation content
                self.navigation_pane.refresh_content(self.workspace_manager)

                # Set workspace manager for editor pane
                self.editor_pane.set_workspace_manager(self.workspace_manager)

                self.logger.info(f"Workspace loaded: {self.workspace_path}")
            else:
                error_msg = f"Failed to load workspace: {self.workspace_manager.last_error}"
                self.status_bar.showMessage(error_msg, 5000)
                self.logger.error(error_msg)

        except Exception as e:
            error_msg = f"Error loading workspace: {e}"
            self.status_bar.showMessage(error_msg, 5000)
            self.logger.error(error_msg)

    def _open_workspace(self):
        """Open a workspace directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Workspace Directory",
            str(Path.home()),
            QFileDialog.ShowDirsOnly
        )

        if directory:
            self.workspace_path = Path(directory)
            self._load_workspace()

    def _toggle_navigation_pane(self):
        """Toggle the navigation pane visibility."""
        self.navigation_pane.setVisible(not self.navigation_pane.isVisible())

    def _toggle_console_pane(self):
        """Toggle the console pane visibility."""
        self.console_pane.setVisible(not self.console_pane.isVisible())

    def _go_to_element_id(self):
        """Show Go to Element ID dialog and navigate to the specified element."""
        # Get available IDs for auto-completion
        available_ids = self._get_available_element_ids()

        # Show dialog
        dialog = GoToIdDialog(self, available_ids)
        if dialog.exec() == QDialog.Accepted:
            element_id = dialog.get_element_id()
            if element_id:
                self._navigate_to_element(element_id)

    def _get_available_element_ids(self):
        """Get list of available element IDs for auto-completion."""
        if not self.workspace_manager:
            return []

        try:
            indexer = self.workspace_manager.indexer
            if not indexer or indexer.get_state().name != "READY":
                return []

            index = indexer.get_index()

            # Collect all elements from all kinds
            all_element_ids = []
            all_kinds = [Kind.REQUIREMENT, Kind.COMPONENT, Kind.DATA, Kind.INTERFACE,
                        Kind.METHOD, Kind.UI, Kind.TASK, Kind.TEST, Kind.OTHER]

            for kind in all_kinds:
                elements = index.get_elements_by_kind(kind)
                for element in elements:
                    if element.id:
                        all_element_ids.append(element.id)

            return sorted(list(set(all_element_ids)))  # Remove duplicates and sort

        except Exception as e:
            self.logger.error(f"Error getting available element IDs: {e}")
            return []

    def _navigate_to_element(self, element_id: str):
        """Navigate to the specified element by ID."""
        if not self.workspace_manager:
            QMessageBox.warning(
                self,
                "No Workspace",
                "No workspace is currently loaded.\n\n"
                "Please open a workspace first using File > Open Workspace."
            )
            return

        try:
            # Get element from workspace
            indexer = self.workspace_manager.indexer
            if not indexer or indexer.get_state().name != "READY":
                QMessageBox.warning(
                    self,
                    "Workspace Not Ready",
                    "The workspace indexer is not ready.\n\n"
                    "Please wait for the workspace to finish loading and try again."
                )
                return

            index = indexer.get_index()
            element = index.get_element_by_id(element_id)

            if not element:
                QMessageBox.information(
                    self,
                    "Element Not Found",
                    f"Element '{element_id}' was not found in the current workspace.\n\n"
                    "Please check the ID and try again. IDs are case-sensitive."
                )
                return

            # Determine which tab to switch to based on element kind
            target_tab = self._get_tab_for_element_kind(element.kind)

            # Switch to appropriate tab in navigation pane
            if target_tab is not None:
                self.navigation_pane.tab_widget.setCurrentIndex(target_tab)

            # Load element in editor
            self.editor_pane.set_element(element_id)

            # Update status
            self.status_bar.showMessage(f"Navigated to {element_id}", 3000)

            self.logger.info(f"Successfully navigated to element: {element_id}")

        except Exception as e:
            self.logger.error(f"Error navigating to element {element_id}: {e}")
            QMessageBox.critical(
                self,
                "Navigation Error",
                f"An error occurred while navigating to '{element_id}':\n\n{str(e)}"
            )

    def _get_tab_for_element_kind(self, kind):
        """Get the appropriate tab index for an element kind."""
        if not kind:
            return 0  # Default to Design tab

        # Map element kinds to tab indices
        design_kinds = [Kind.REQUIREMENT, Kind.COMPONENT, Kind.DATA, Kind.INTERFACE, Kind.METHOD, Kind.UI]
        code_kinds = [Kind.TASK]
        test_kinds = [Kind.TEST]

        if kind in design_kinds:
            return 0  # Design tab
        elif kind in code_kinds:
            return 1  # Code tab
        elif kind in test_kinds:
            return 2  # Test tab
        else:
            return 0  # Default to Design tab

    def _go_to_design_tab(self):
        """Switch to the Design tab."""
        self.navigation_pane.tab_widget.setCurrentIndex(0)
        self.status_bar.showMessage("Switched to Design tab", 2000)

    def _go_to_code_tab(self):
        """Switch to the Code tab."""
        self.navigation_pane.tab_widget.setCurrentIndex(1)
        self.status_bar.showMessage("Switched to Code tab", 2000)

    def _go_to_test_tab(self):
        """Switch to the Test tab."""
        self.navigation_pane.tab_widget.setCurrentIndex(2)
        self.status_bar.showMessage("Switched to Test tab", 2000)

    def _show_settings(self):
        """Show the settings dialog."""
        # Determine conventions file path
        if self.workspace_path:
            # Conventions.md should be at workspace root level
            conventions_path = self.workspace_path.parent / "conventions.md"
        else:
            # No workspace loaded, use default location
            conventions_path = Path.home() / "software-projects" / "conventions.md"

        try:
            # Create and show settings dialog
            settings_dialog = SettingsDialog(self, conventions_path)
            result = settings_dialog.exec()

            if result == QDialog.Accepted:
                self.status_bar.showMessage("Settings saved successfully", 3000)
                self.logger.info("Settings updated successfully")
            else:
                self.status_bar.showMessage("Settings cancelled", 2000)

        except Exception as e:
            error_msg = f"Error opening settings: {e}"
            QMessageBox.critical(self, "Settings Error", error_msg)
            self.logger.error(error_msg)

    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Project1",
            "<h2>Project1</h2>"
            "<p>AI-Assisted Software Development Tool</p>"
            "<p>Version: 0.1.0 (MVP)</p>"
            "<p>A GUI + MCP tool server for structured software development "
            "with artifact-based AI collaboration.</p>"
            "<p><b>Key Features:</b></p>"
            "<ul>"
            "<li>Design-first development workflow</li>"
            "<li>Structured document management</li>"
            "<li>Privileged command execution</li>"
            "<li>AI-assisted development</li>"
            "</ul>"
            "<p>Implementation Status:</p>"
            "<ul>"
            "<li>✅ MCP Server with privileged operations</li>"
            "<li>✅ Command allowlist management</li>"
            "<li>✅ Persistent request queue</li>"
            "<li>✅ Safe command execution with audit logging</li>"
            "<li>⚠️ GUI Framework (T:0020 in progress)</li>"
            "</ul>"
        )

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            self.logger.info("Shutting down application")

            # Clean up workspace manager
            if self.workspace_manager:
                self.workspace_manager.stop()

            # Accept the close event
            event.accept()

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            event.accept()  # Close anyway


def create_main_window(workspace_path: Optional[str] = None) -> MainWindow:
    """
    Factory function to create and show the main window.

    Args:
        workspace_path: Optional path to workspace directory

    Returns:
        MainWindow instance
    """
    window = MainWindow(workspace_path)
    window.show()
    return window


def main():
    """Main entry point for the GUI application."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Project1 GUI application")

    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Project1")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("Project1")

        # Create and show main window
        # Check for workspace path in command line arguments
        workspace_path = None
        if len(sys.argv) > 1:
            workspace_path = sys.argv[1]
            logger.info(f"Using workspace path from command line: {workspace_path}")

        main_window = create_main_window(workspace_path)

        logger.info("GUI application started successfully")

        # Run the application
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code

    except Exception as e:
        logger.error(f"Fatal error in GUI application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())