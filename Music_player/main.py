#!/usr/bin/env python3
import os

import version

os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.ffmpeg=false")
import sys
import locale
from language import i18n
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QPalette, QColor
from ui.main_window import MainWindow

print(version.version)
print(version.build_date)

def main():
    # 语言设置：优先使用 QSettings 中保存的，否则按系统语言检测
    settings = QSettings("netease_downloader", "settings")
    saved_lang = settings.value("lang", "")
    if saved_lang in ("zh_cn", "en_us"):
        i18n.set_lang(saved_lang)
    else:
        system_lang = locale.getlocale()[0]  # e.g. 'Chinese (Simplified)_China' or 'English_United States'
        if system_lang and ('English' in system_lang or 'en_' in system_lang):
            i18n.set_lang('en_us')
        else:
            i18n.set_lang('zh_cn')
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 主题：跟随系统/暗色/亮色（默认跟随系统）
    settings = QSettings("netease_downloader", "settings")
    theme_pref = settings.value("theme", "system")

    DARK_STYLESHEET = """
QMainWindow, QWidget, QDialog {
    background-color: #0a0a0a;
    color: #ffffff;
}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QTableWidget {
    background-color: #141414;
    color: #ffffff;
    border: 1px solid #333333;
    padding: 5px;
    border-radius: 3px;
    selection-background-color: #00ff88;
    selection-color: #0a0a0a;
}
QLineEdit:focus, QComboBox:focus { border-color: #555555; }
QPushButton { background-color: #1a1a1a; color: #ffffff; border: 1px solid #333333; padding: 8px 16px; border-radius: 3px; }
QPushButton:hover { background-color: #2d2d2d; border-color: #555555; }
QPushButton:pressed { background-color: #333333; }
QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }
QRadioButton, QCheckBox, QLabel { color: #ffffff; }
QRadioButton::indicator, QCheckBox::indicator { width: 16px; height: 16px; background-color: #141414; border: 2px solid #333333; border-radius: 8px; }
QRadioButton::indicator:checked { background-color: #ffffff; border-color: #ffffff; }
QGroupBox { border: 1px solid #333333; margin-top: 10px; padding-top: 10px; color: #ffffff; font-weight: bold; }
QProgressBar { border: 1px solid #333333; border-radius: 3px; background-color: #0a0a0a; text-align: center; color: #ffffff; }
QProgressBar::chunk { background-color: #ffffff; border-radius: 2px; }
QScrollBar:vertical { background: #0a0a0a; width: 12px; border: none; }
QScrollBar::handle:vertical { background: #333333; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #555555; }
QHeaderView::section { background-color: #1a1a1a; color: #ffffff; padding: 5px; border: 1px solid #333333; }
QMenu { background-color: #1a1a1a; color: #ffffff; border: 1px solid #333333; }
QMenu::item:selected { background-color: #333333; }
QStatusBar { background-color: #0a0a0a; color: #888888; }
QToolTip { background-color: #1a1a1a; color: #ffffff; border: 1px solid #333333; }
"""

    LIGHT_STYLESHEET = """
QMainWindow, QWidget, QDialog { background-color: #fafafa; color: #0a0a0a; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QTableWidget { background-color: #ffffff; color: #0a0a0a; border: 1px solid #cccccc; padding: 5px; border-radius: 3px; selection-background-color: #007acc; selection-color: #ffffff; }
QPushButton { background-color: #eaeaea; color: #0a0a0a; border: 1px solid #cccccc; padding: 8px 16px; border-radius: 3px; }
QPushButton:hover { background-color: #dedede; }
QPushButton:pressed { background-color: #d0d0d0; }
QPushButton:disabled { background-color: #f5f5f5; color: #999999; border-color: #eeeeee; }
QRadioButton, QCheckBox, QLabel { color: #0a0a0a; }
QRadioButton::indicator, QCheckBox::indicator { width: 16px; height: 16px; background-color: #ffffff; border: 2px solid #cccccc; border-radius: 8px; }
QRadioButton::indicator:checked { background-color: #007acc; border-color: #007acc; }
QGroupBox { border: 1px solid #dedede; margin-top: 10px; padding-top: 10px; color: #0a0a0a; font-weight: bold; }
QProgressBar { border: 1px solid #cccccc; border-radius: 3px; background-color: #ffffff; text-align: center; color: #0a0a0a; }
QProgressBar::chunk { background-color: #007acc; border-radius: 2px; }
QScrollBar:vertical { background: #f5f5f5; width: 12px; border: none; }
QScrollBar::handle:vertical { background: #d0d0d0; border-radius: 6px; min-height: 30px; }
QHeaderView::section { background-color: #f0f0f0; color: #0a0a0a; padding: 5px; border: 1px solid #e0e0e0; }
QMenu { background-color: #ffffff; color: #0a0a0a; border: 1px solid #e0e0e0; }
QMenu::item:selected { background-color: #e6f2ff; }
QStatusBar { background-color: #f5f5f5; color: #666666; }
QToolTip { background-color: #ffffff; color: #0a0a0a; border: 1px solid #cccccc; }
"""

    if theme_pref == "system":
        pal = app.palette()
        color = pal.color(QPalette.ColorRole.Window)
        r, g, b, _ = color.getRgb()
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        theme_to_apply = "dark" if luminance < 0.5 else "light"
    else:
        theme_to_apply = theme_pref

    app.setStyleSheet(DARK_STYLESHEET if theme_to_apply == "dark" else LIGHT_STYLESHEET)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
