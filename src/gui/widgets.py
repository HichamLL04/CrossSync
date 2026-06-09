import os
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# WriteRedirector to capture stdout to GUI console
class WriteStream(QObject):
    message = pyqtSignal(str)

    def write(self, text):
        self.message.emit(str(text))

    def flush(self):
        pass

# Drag and drop input fields
class DragDropField(QLineEdit):
    def __init__(self, placeholder, is_dir=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setAcceptDrops(True)
        self.is_dir = is_dir
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                border: 2px dashed #444444;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:hover {
                border-color: #007acc;
                background-color: #252526;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #2d2d30;
                    border: 2px dashed #007acc;
                    border-radius: 6px;
                    padding: 8px;
                    color: #ffffff;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                border: 2px dashed #444444;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self.is_dir:
                if os.path.isdir(file_path):
                    self.setText(file_path)
                else:
                    self.setText(os.path.dirname(file_path))
            else:
                self.setText(file_path)
        self.dragLeaveEvent(None)
