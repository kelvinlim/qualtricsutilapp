# main.py
import sys
import io
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, 
    QWidget, QPushButton, QFileDialog, QMessageBox,
    QMenuBar
)
from PySide6.QtGui import QAction, QKeySequence

# --- Installation ---
# This application requires PySide6 and ruamel.yaml.
# You can install them using pip:
# pip install PySide6
# pip install ruamel.yaml

class YAMLEditor(QMainWindow):
    """
    A simple YAML editor application built with PySide6.
    
    Allows users to create, open, edit, format, and save YAML files,
    with support for preserving comments.
    """
    def __init__(self):
        """Initializes the application window and UI components."""
        super().__init__()
        self.current_file_path = None
        self.init_ui()

    def init_ui(self):
        """Sets up the user interface of the main window."""
        # --- Main Window Configuration ---
        self.setWindowTitle("YAML Editor")
        self.setGeometry(100, 100, 800, 600)

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Text Editor ---
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter your YAML content here, or open a file.")
        self.text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 14px;
                background-color: #fdf6e3; /* Solarized Light */
                color: #657b83;
                border: 1px solid #eee8d5;
            }
        """)
        layout.addWidget(self.text_edit)

        # --- Format Button ---
        self.format_button = QPushButton("Format YAML (Preserve Comments)")
        self.format_button.clicked.connect(self.format_yaml)
        self.format_button.setStyleSheet("""
            QPushButton {
                background-color: #268bd2;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2aa198;
            }
        """)
        layout.addWidget(self.format_button)

        # --- Menu Bar ---
        self.create_menu_bar()

    def create_menu_bar(self):
        """Creates the main menu bar with File actions."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        # --- New Action ---
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        # --- Open Action ---
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # --- Save Action ---
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # --- Save As Action ---
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # --- Exit Action ---
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def new_file(self):
        """Clears the editor and resets the current file path."""
        self.text_edit.clear()
        self.current_file_path = None
        self.setWindowTitle("YAML Editor - New File")

    def open_file(self):
        """Opens a YAML file and loads its content into the editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open YAML File", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_edit.setText(content)
                    self.current_file_path = file_path
                    self.setWindowTitle(f"YAML Editor - {self.current_file_path}")
            except Exception as e:
                self.show_error_message("Error Opening File", f"Could not read file:\n{e}")

    def save_file(self):
        """Saves the current content to the existing file path."""
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_edit.toPlainText())
            except Exception as e:
                self.show_error_message("Error Saving File", f"Could not save file:\n{e}")
        else:
            # If no file path exists, trigger "Save As"
            self.save_file_as()

    def save_file_as(self):
        """Saves the current content to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save YAML File", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if file_path:
            # Ensure the file has a .yaml or .yml extension
            if not file_path.endswith(('.yaml', '.yml')):
                file_path += '.yaml'
            self.current_file_path = file_path
            self.save_file()
            self.setWindowTitle(f"YAML Editor - {self.current_file_path}")

    def format_yaml(self):
        """
        Parses and re-serializes the YAML content for proper formatting,
        preserving comments.
        """
        current_text = self.text_edit.toPlainText()
        if not current_text.strip():
            self.show_info_message("Nothing to Format", "The editor is empty.")
            return

        try:
            yaml = YAML()
            # Set indentation options for standard formatting
            yaml.indent(mapping=2, sequence=4, offset=2)
            
            # Load the YAML from the text editor. ruamel.yaml preserves comments by default.
            data = yaml.load(current_text)

            # Dump the data back to a string while preserving comments and structure
            string_stream = io.StringIO()
            yaml.dump(data, string_stream)
            formatted_text = string_stream.getvalue()
            
            self.text_edit.setText(formatted_text)

        except YAMLError as e:
            # If parsing fails, show an error with details
            self.show_error_message("YAML Formatting Error", f"Could not parse YAML. Please check your syntax.\n\nError: {e}")

    def show_error_message(self, title, message):
        """Displays a critical error message box."""
        QMessageBox.critical(self, title, message)

    def show_info_message(self, title, message):
        """Displays an informational message box."""
        QMessageBox.information(self, title, message)

def main():
    """The main entry point for the application."""
    app = QApplication(sys.argv)
    editor = YAMLEditor()
    editor.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
