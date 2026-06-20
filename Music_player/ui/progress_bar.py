"""进度条"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from language import i18n


class DownloadProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 状态文本
        self.status_label = QLabel(f"{i18n.tr('ready')} ({i18n.tr('progress_hint')})")
        self.status_label.setStyleSheet("color: #666666; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        layout.addWidget(self.progress)
        
        # 详情
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("color: #666666; font-size: 9px;")
        layout.addWidget(self.detail_label)
    
    def set_progress(self, current: int, total: int):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress.setValue(percent)
        
            # 进度条颜色：未填充=黑色，已填充=白色
            # 文字颜色：根据进度切换
            if percent < 48:
                # 进度少，文字在黑色背景上 → 白色
                self.progress.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #333333;
                        border-radius: 3px;
                        background-color: #1a1a1a;
                        text-align: center;
                        color: #ffffff;
                    }
                    QProgressBar::chunk {
                        background-color: #ffffff;
                        border-radius: 2px;
                    }
                """)
            else:
                # 进度多，文字在白色块上 → 黑色
                self.progress.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #333333;
                        border-radius: 3px;
                        background-color: #1a1a1a;
                        text-align: center;
                        color: #0a0a0a;
                    }
                    QProgressBar::chunk {
                        background-color: #ffffff;
                        border-radius: 2px;
                    }
                """)
        
            self.status_label.setText(f"{current} / {total}")
            self.detail_label.setText(f"{percent}%")

    
    def refresh_texts(self):
        """刷新状态文本（仅在显示默认文本时更新）"""
        current = self.status_label.text()
        # 只在显示初始状态或纯就绪文本时更新
        if current == i18n.tr("ready") or current.startswith(i18n.tr("ready")) or current == "":
            self.status_label.setText(f"{i18n.tr('ready')} ({i18n.tr('progress_hint')})")
    
    def set_status(self, text: str):
        self.status_label.setText(text)
        self.detail_label.setText("")
    
    def set_song_name(self, name: str):
        self.detail_label.setText(name)
    
    def reset(self):
        self.progress.setValue(0)
        self.status_label.setText(i18n.tr("ready"))
        self.detail_label.setText("")


class CircularProgressIndicator(QWidget):
    """API状态"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._color = "#ff4444"
    
    def set_color(self, color: str):
        self._color = color
        self.update()
    
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 12, 12)
