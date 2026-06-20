"""日志面板"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QColor
from datetime import datetime


class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self._max_lines = 1000
        # initial style; will be overridden by MainWindow.set_theme if present
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #eaeaea;
                color: #000000;
                border: 1px solid #cccccc;
                font-family: Consolas;
                font-size: 9pt;
                padding: 8px;
                selection-background-color: #007acc;
                selection-color: #eaeaea;
            }
        """)
        layout.addWidget(self.text_edit)

    def set_theme(self, theme: str):
        """Apply 'dark' or 'light' theme to the log panel."""
        if theme == "dark":
            sheet = '''
            QTextEdit {
                background-color: #1a1a1a;
                color: #eaeaea;
                border: 1px solid #333333;
                font-family: Consolas;
                font-size: 9pt;
                padding: 8px;
                selection-background-color: #2d2d2d;
                selection-color: #eaeaea;
            }
            '''
        else:
            sheet = '''
            QTextEdit {
                background-color: #eaeaea;
                color: #000000;
                border: 1px solid #cccccc;
                font-family: Consolas;
                font-size: 9pt;
                padding: 8px;
                selection-background-color: #007acc;
                selection-color: #eaeaea;
            }
            '''
        self.text_edit.setStyleSheet(sheet)
    
    def append(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_edit.append(f"[{timestamp}] {message}")
    
        # 手动限制行数
        doc = self.text_edit.document()
        if doc.blockCount() > self._max_lines:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
    
        # 滚动到底
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    
    def clear(self):
        self.text_edit.clear()
    
    def get_text(self) -> str:
        return self.text_edit.toPlainText()
