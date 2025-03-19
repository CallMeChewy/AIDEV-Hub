import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtCore import Qt

import difflib

class DiffWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Diff Generator")

        self.file1_path = ""
        self.file2_path = ""

        # Widgets
        self.file1_button = QPushButton("Select Original File")
        self.file1_label = QLabel("Original File: Not selected")
        self.file2_button = QPushButton("Select New File")
        self.file2_label = QLabel("New File: Not selected")
        self.generate_button = QPushButton("Generate Diff")
        self.generate_button.setEnabled(False)  # Disable initially

        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.new_text = QTextEdit()
        self.new_text.setReadOnly(True)
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)

        self.original_hide_button = QPushButton("Hide Original")
        self.new_hide_button = QPushButton("Hide New")
        self.diff_hide_button = QPushButton("Hide Diff")

        self.original_visible = True
        self.new_visible = True
        self.diff_visible = True

        # Layout
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file1_button)
        file_layout.addWidget(self.file1_label)
        file_layout.addWidget(self.file2_button)
        file_layout.addWidget(self.file2_label)

        hide_layout = QHBoxLayout()
        hide_layout.addWidget(self.original_hide_button)
        hide_layout.addWidget(self.new_hide_button)
        hide_layout.addWidget(self.diff_hide_button)

        self.text_layout = QHBoxLayout()
        self.text_layout.addWidget(QLabel("Original File"))
        self.text_layout.addWidget(QLabel("New File"))
        self.text_layout.addWidget(QLabel("Diff"))

        self.display_layout = QHBoxLayout()
        self.display_layout.addWidget(self.original_text)
        self.display_layout.addWidget(self.new_text)
        self.display_layout.addWidget(self.diff_text)

        main_layout = QVBoxLayout()
        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.generate_button)
        main_layout.addLayout(hide_layout)
        main_layout.addLayout(self.text_layout)
        main_layout.addLayout(self.display_layout)

        self.setLayout(main_layout)

        # Connections
        self.file1_button.clicked.connect(self.select_file1)
        self.file2_button.clicked.connect(self.select_file2)
        self.generate_button.clicked.connect(self.generate_diff)

        self.original_hide_button.clicked.connect(self.toggle_original)
        self.new_hide_button.clicked.connect(self.toggle_new)
        self.diff_hide_button.clicked.connect(self.toggle_diff)

    def select_file1(self):
        file1_path, _ = QFileDialog.getOpenFileName(self, "Select Original File")
        if file1_path:
            self.file1_path = file1_path
            self.file1_label.setText("Original File: " + self.file1_path)
            self.check_enable_generate()

    def select_file2(self):
        file2_path, _ = QFileDialog.getOpenFileName(self, "Select New File")
        if file2_path:
            self.file2_path = file2_path
            self.file2_label.setText("New File: " + self.file2_path)
            self.check_enable_generate()

    def check_enable_generate(self):
        if self.file1_path and self.file2_path:
            self.generate_button.setEnabled(True)
        else:
            self.generate_button.setEnabled(False)

    def generate_diff(self):
        try:
            with open(self.file1_path, 'r') as f1:
                file1_lines = f1.readlines()
            with open(self.file2_path, 'r') as f2:
                file2_lines = f2.readlines()

            # Display original and new files with specified colors
            self.original_text.setHtml(f"<pre><span style='color: green;'>{''.join(file1_lines)}</span></pre>")
            self.new_text.setHtml(f"<pre><span style='color: red;'>{''.join(file2_lines)}</span></pre>")

            diff = difflib.Differ().compare(file1_lines, file2_lines)
            diff_text = ""
            for line in diff:
                if line.startswith('  '):
                    diff_text += f"<span style='color: white;'>  {line[2:]}</span>"  # Common lines
                elif line.startswith('- '):
                    diff_text += f"<span style='color: red;'>1: {line[2:]}</span>"  # File 1 lines
                elif line.startswith('+ '):
                    diff_text += f"<span style='color: green;'>2: {line[2:]}</span>"  # File 2 lines
                elif line.startswith('? '):
                    diff_text += f"<span style='color: yellow;'>? {line[2:]}</span>"  # Questionable lines
                else:
                    diff_text += f"<span style='color: darkgray;'>{line}</span>" # Other lines (e.g. ---, +++)

            if not diff_text:
                self.diff_text.setText("No differences found.")
            else:
                self.diff_text.setHtml(f"<pre>{diff_text}</pre>")

        except FileNotFoundError:
            self.original_text.setText("Error: One or both files not found.")
            self.new_text.setText("Error: One or both files not found.")
            self.diff_text.setText("Error: One or both files not found.")
        except Exception as e:
            self.diff_text.setText(f"Error: {str(e)}")

    def toggle_original(self):
        self.original_visible = not self.original_visible
        self.original_text.setVisible(self.original_visible)
        self.update_layout()

    def toggle_new(self):
        self.new_visible = not self.new_visible
        self.new_text.setVisible(self.new_visible)
        self.update_layout()

    def toggle_diff(self):
        self.diff_visible = not self.diff_visible
        self.diff_text.setVisible(self.diff_visible)
        self.update_layout()

    def update_layout(self):
        # Remove all widgets from the layout
        for i in reversed(range(self.display_layout.count())):
            widget = self.display_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Add the visible widgets back to the layout
        if self.original_visible:
            self.display_layout.addWidget(self.original_text)
        if self.new_visible:
            self.display_layout.addWidget(self.new_text)
        if self.diff_visible:
            self.display_layout.addWidget(self.diff_text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DiffWindow()
    window.show()
    sys.exit(app.exec())
