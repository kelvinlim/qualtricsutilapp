# main.py
import sys
import io
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QFileDialog, QMessageBox, QMenuBar, QLineEdit,
    QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QRect, QSize, QSettings
from PySide6.QtGui import QAction, QKeySequence, QPainter, QColor, QFont

# --- Local Imports ---
# Make sure qualtrics_util.py is in the same directory
from qualtrics_util import check_connection

# --- Installation ---
# This application requires PySide6 and ruamel.yaml.
# You can install them using pip:
# pip install PySide6
# pip install ruamel.yaml

# +++ WIDGETS FOR LINE NUMBERS (Used in EditorWindow) +++

class LineNumberArea(QWidget):
    """A widget to display line numbers for a CodeEditor."""
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """A QPlainTextEdit subclass that includes a line number area."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#f0f0f0"))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.GlobalColor.darkGray)
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

# --- YAML Editor Window ---

class EditorWindow(QMainWindow):
    """The standalone YAML editor window with line numbers."""
    def __init__(self, file_path=None):
        super().__init__()
        self.current_file_path = None
        self.init_ui()
        if file_path:
            self.open_file(file_path)

    def init_ui(self):
        self.setWindowTitle("YAML Editor")
        self.setGeometry(150, 150, 800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.text_edit = CodeEditor()
        self.text_edit.setPlaceholderText("Enter YAML content or open a file.")
        font = QFont("Courier New", 14)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet("QPlainTextEdit { background-color: #fdf6e3; color: #657b83; border: 1px solid #eee8d5; }")
        layout.addWidget(self.text_edit)

        self.format_button = QPushButton("Format YAML (Preserve Comments)")
        self.format_button.clicked.connect(self.format_yaml)
        layout.addWidget(self.format_button)
        self.create_menu_bar()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        actions = [
            ("&New", QKeySequence.StandardKey.New, self.new_file),
            ("&Open...", QKeySequence.StandardKey.Open, lambda: self.open_file()),
            ("&Save", QKeySequence.StandardKey.Save, self.save_file),
            ("Save &As...", QKeySequence.StandardKey.SaveAs, self.save_file_as),
            (None, None, None),
            ("E&xit", QKeySequence.StandardKey.Quit, self.close)
        ]
        for title, shortcut, callback in actions:
            if title is None:
                file_menu.addSeparator()
                continue
            action = QAction(title, self)
            if shortcut:
                action.setShortcut(shortcut)
            if callback:
                action.triggered.connect(callback)
            file_menu.addAction(action)

    def new_file(self):
        self.text_edit.clear()
        self.current_file_path = None
        self.setWindowTitle("YAML Editor - New File")

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open YAML File", "", "YAML Files (*.yaml *.yml);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_edit.setPlainText(content)
                    self.current_file_path = file_path
                    self.setWindowTitle(f"Editor - {self.current_file_path}")
            except Exception as e:
                self.show_error_message("Error Opening File", f"Could not read file:\n{e}")

    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_edit.toPlainText())
            except Exception as e:
                self.show_error_message("Error Saving File", f"Could not save file:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save YAML File", "", "YAML Files (*.yaml *.yml);;All Files (*)")
        if file_path:
            if not file_path.endswith(('.yaml', '.yml')):
                file_path += '.yaml'
            self.current_file_path = file_path
            self.save_file()
            self.setWindowTitle(f"Editor - {self.current_file_path}")

    def format_yaml(self):
        current_text = self.text_edit.toPlainText()
        if not current_text.strip(): return
        try:
            yaml = YAML()
            yaml.indent(mapping=2, sequence=4, offset=2)
            data = yaml.load(current_text)
            string_stream = io.StringIO()
            yaml.dump(data, string_stream)
            self.text_edit.setPlainText(string_stream.getvalue())
        except YAMLError as e:
            self.show_error_message("YAML Formatting Error", f"Could not parse YAML.\nError: {e}")

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)

# --- Main Launcher Window ---

class LauncherWindow(QMainWindow):
    """The main application window for selecting files and running tasks."""
    def __init__(self):
        super().__init__()
        # To store editor windows so they aren't garbage collected
        self.editor_windows = []
        self.settings = QSettings("MyCompany", "QualtricsApp")
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("Qualtrics Utility Launcher")
        self.setMinimumSize(600, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- Qualtrics Token File Section ---
        self.token_file_path_edit, self.edit_token_btn = self.create_file_input_group(
            main_layout, "Qualtrics Token File:", self.browse_token_file, self.edit_token_file
        )

        # --- Project Config File Section ---
        self.project_config_path_edit, self.edit_project_btn = self.create_file_input_group(
            main_layout, "Project Config File:", self.browse_project_file, self.edit_project_file
        )
        
        # --- Spacer ---
        main_layout.addStretch(1)

        # --- Action Buttons ---
        actions_frame = QFrame()
        actions_frame.setFrameShape(QFrame.Shape.StyledPanel)
        actions_layout = QHBoxLayout(actions_frame)
        
        self.check_conn_btn = QPushButton("Check Qualtrics Connection")
        self.check_conn_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        self.check_conn_btn.clicked.connect(self.run_check_connection)
        actions_layout.addWidget(self.check_conn_btn)
        
        main_layout.addWidget(actions_frame)

    def create_file_input_group(self, layout, label_text, browse_callback, edit_callback):
        """Helper to create a label, line edit, and two buttons."""
        group_label = QLabel(label_text)
        layout.addWidget(group_label)
        
        hbox = QHBoxLayout()
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Click Browse to select a file...")
        line_edit.setReadOnly(True)
        hbox.addWidget(line_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(browse_callback)
        hbox.addWidget(browse_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(edit_callback)
        edit_btn.setEnabled(False) # Disabled until a file is selected
        hbox.addWidget(edit_btn)
        
        layout.addLayout(hbox)
        return line_edit, edit_btn

    def browse_token_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Token File", "", "YAML Files (*.yaml *.yml)")
        if path:
            self.token_file_path_edit.setText(path)
            self.edit_token_btn.setEnabled(True)
            self.save_settings()

    def browse_project_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Project Config File", "", "YAML Files (*.yaml *.yml)")
        if path:
            self.project_config_path_edit.setText(path)
            self.edit_project_btn.setEnabled(True)
            self.save_settings()

    def edit_token_file(self):
        self.open_editor_for_path(self.token_file_path_edit.text())
        
    def edit_project_file(self):
        self.open_editor_for_path(self.project_config_path_edit.text())

    def open_editor_for_path(self, path):
        if not path:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return
        # Create a new editor window
        editor = EditorWindow(file_path=path)
        self.editor_windows.append(editor) # Keep a reference
        editor.show()

    def run_check_connection(self):
        token_path = self.token_file_path_edit.text()
        config_path = self.project_config_path_edit.text()
        
        success, message = check_connection(token_path, config_path)
        
        if success:
            QMessageBox.information(self, "Connection Success", message)
        else:
            QMessageBox.warning(self, "Connection Failed", message)

    def load_settings(self):
        """Load last used file paths from QSettings."""
        token_path = self.settings.value("qualtrics_token_path", "")
        if token_path:
            self.token_file_path_edit.setText(token_path)
            self.edit_token_btn.setEnabled(True)

        project_path = self.settings.value("project_config_path", "")
        if project_path:
            self.project_config_path_edit.setText(project_path)
            self.edit_project_btn.setEnabled(True)

    def save_settings(self):
        """Save current file paths to QSettings."""
        self.settings.setValue("qualtrics_token_path", self.token_file_path_edit.text())
        self.settings.setValue("project_config_path", self.project_config_path_edit.text())

    def closeEvent(self, event):
        """Ensure settings are saved when the launcher closes."""
        self.save_settings()
        super().closeEvent(event)

def main():
    """The main entry point for the application."""
    app = QApplication(sys.argv)
    # Set organization and application name for QSettings
    app.setOrganizationName("MyCompany")
    app.setApplicationName("QualtricsApp")
    
    launcher = LauncherWindow()
    launcher.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
