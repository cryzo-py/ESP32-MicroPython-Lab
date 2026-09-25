"""
Gestion des thèmes et styles QSS pour ESP32 MicroPython Lab
Thème sombre moderne conforme à la maquette de l'application
"""

DARK_THEME_QSS = """
/* Global Window Styling */
QMainWindow, QDialog {
    background-color: #121826;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 10pt;
}

QWidget#CentralWidget, QWidget#MainContainer {
    background-color: #121826;
}

QLabel {
    background-color: transparent;
    color: #e2e8f0;
}

/* Header Navigation Bar */
#HeaderBar {
    background-color: #1a2234;
    border-bottom: 1px solid #2a3449;
    min-height: 52px;
    max-height: 52px;
    padding: 0 12px;
}

#AppTitle {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
}

#AppTagline {
    font-size: 11px;
    color: #94a3b8;
    margin-left: 8px;
}

/* Nav Tabs in Header */
QToolButton.NavTab {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}

QToolButton.NavTab:hover {
    background-color: #242f46;
    color: #f8fafc;
}

QToolButton.NavTab:checked, QToolButton.NavTab.active {
    background-color: #2563eb;
    color: #ffffff;
}

/* Panels & Cards */
QFrame.Card, QWidget.Panel {
    background-color: #1a2234;
    border: 1px solid #2a3449;
    border-radius: 8px;
}

/* Sidebar Component Library */
#ComponentLibrary {
    background-color: #151c2c;
    border-right: 1px solid #2a3449;
}

#ComponentLibraryTitle {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
}

#ComponentCategoryTitle {
    font-size: 11px;
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
    margin-top: 6px;
}

#ComponentCard, QFrame.ComponentCard, QFrame[class="ComponentCard"] {
    background-color: #1a2234;
    border: 1px solid #2a3449;
    border-radius: 6px;
    padding: 4px;
}

#ComponentCard:hover, QFrame.ComponentCard:hover, QFrame[class="ComponentCard"]:hover {
    background-color: #242f46;
    border: 1px solid #38bdf8;
}

QLabel.ComponentCardLabel, QLabel[class="ComponentCardLabel"] {
    font-size: 10px;
    color: #cbd5e1;
    font-weight: 600;
}

/* Properties Panel */
#PropertiesPanel, QFrame#PropertiesPanel {
    background-color: #151c2c;
    border: 1px solid #2a3449;
    border-radius: 8px;
    padding: 6px;
}

#PropertiesPanelTitle, QLabel#PropertiesPanelTitle {
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
}

#PropertiesEmptyLabel, QLabel#PropertiesEmptyLabel {
    font-size: 11px;
    color: #94a3b8;
}

#SearchBox {
    background-color: #1e283d;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
}

#SearchBox:focus {
    border: 1px solid #3b82f6;
}

/* Action Buttons Toolbar */
QPushButton.PrimaryBtn, QPushButton#BtnSimulate {
    background-color: #16a34a;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
}

QPushButton.PrimaryBtn:hover, QPushButton#BtnSimulate:hover {
    background-color: #22c55e;
}

QPushButton.PrimaryBtn:disabled, QPushButton#BtnSimulate:disabled {
    background-color: #334155;
    color: #64748b;
    border: 1px solid #1e293b;
}

QPushButton.UploadBtn, QPushButton#BtnUpload {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
}

QPushButton.UploadBtn:hover, QPushButton#BtnUpload:hover {
    background-color: #3b82f6;
}

QPushButton.UploadBtn:disabled, QPushButton#BtnUpload:disabled {
    background-color: #334155;
    color: #64748b;
    border: 1px solid #1e293b;
}

QPushButton.SecondaryBtn, QPushButton#BtnReset {
    background-color: #334155;
    color: #e2e8f0;
    font-weight: 500;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
}

QPushButton.SecondaryBtn:hover, QPushButton#BtnReset:hover {
    background-color: #475569;
}

QPushButton.StopBtn, QPushButton#BtnStop {
    background-color: #ef4444;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
}

QPushButton.StopBtn:hover, QPushButton#BtnStop:hover {
    background-color: #dc2626;
}

QPushButton.StopBtn:disabled, QPushButton#BtnStop:disabled {
    background-color: #334155;
    color: #64748b;
    border: 1px solid #1e293b;
}

/* Code Editor */
QPlainTextEdit.CodeEditor {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #2a3449;
    border-radius: 6px;
    font-family: 'Consolas', 'Cascadia Code', 'Fira Code', monospace;
    font-size: 13px;
    padding: 6px;
}

/* Console & REPL */
QPlainTextEdit.Terminal {
    background-color: #0b0f19;
    color: #38bdf8;
    border: 1px solid #1e293b;
    border-radius: 6px;
    font-family: 'Consolas', 'Cascadia Code', 'Fira Code', monospace;
    font-size: 12px;
    padding: 6px;
}

QLineEdit.TerminalInput {
    background-color: #131b2e;
    color: #f8fafc;
    border: 1px solid #2a3449;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: 'Consolas', 'Cascadia Code', monospace;
}

QLineEdit.TerminalInput:focus {
    border: 1px solid #38bdf8;
}

/* Hardware Status Card */
#HardwareCard {
    background-color: #162032;
    border: 1px solid #2a3449;
    border-radius: 8px;
    padding: 10px;
}

#StatusBadgeReady {
    background-color: #064e3b;
    color: #34d399;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 600;
}

#StatusBadgeDisconnected {
    background-color: #3f1d24;
    color: #f87171;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 600;
}

/* Combo Box */
QComboBox {
    background-color: #1e283d;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px 10px;
    color: #f8fafc;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #1e283d;
    border: 1px solid #334155;
    selection-background-color: #2563eb;
    color: #f8fafc;
}

/* Tab Bar & Bottom Tools Tabs */
#BottomToolsTabs QTabWidget::pane, QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 6px;
}

#BottomToolsTabs QTabBar::tab, QTabBar::tab {
    background-color: #1e293b;
    color: #94a3b8;
    border: 1px solid #2a3449;
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: 600;
    font-size: 11px;
}

#BottomToolsTabs QTabBar::tab:selected, QTabBar::tab:selected {
    background-color: #0284c7;
    color: #ffffff;
    border-bottom: 2px solid #38bdf8;
}

#BottomToolsTabs QTabBar::tab:hover:!selected, QTabBar::tab:hover:!selected {
    background-color: #242f46;
    color: #f8fafc;
}

/* Zoom Labels */
#ZoomLabel, QLabel#ZoomLabel, #ZoomValLabel, QLabel#ZoomValLabel {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 500;
}

/* Splitter */
QSplitter::handle {
    background-color: #242f46;
}

QSplitter::handle:horizontal {
    width: 6px;
}

QSplitter::handle:vertical {
    height: 6px;
}

QSplitter::handle:hover {
    background-color: #38bdf8;
}

QSplitter::handle:pressed {
    background-color: #0284c7;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #121826;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #121826;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #475569;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* Menu Bar & Menus */
QMenuBar {
    background-color: #162032;
    color: #cbd5e1;
    border-bottom: 1px solid #2a3449;
    padding: 2px 8px;
    font-size: 12px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 5px 10px;
    border-radius: 4px;
    color: #cbd5e1;
}

QMenuBar::item:selected {
    background-color: #242f46;
    color: #ffffff;
}

QMenuBar::item:pressed {
    background-color: #2563eb;
    color: #ffffff;
}

QMenu {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 28px 6px 14px;
    border-radius: 4px;
    font-size: 12px;
}

QMenu::item:selected {
    background-color: #0284c7;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #64748b;
    background-color: transparent;
}
QToolButton:disabled {
    color: #94a3b8 !important;
}


QMenu::separator {
    height: 1px;
    background-color: #334155;
    margin: 4px 2px;
}
"""

LIGHT_THEME_QSS = """
/* Global Window Styling - Light Mode (Haute Lisibilité & Fort Contraste) */
QMainWindow, QDialog {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 10pt;
}

QWidget#CentralWidget, QWidget#MainContainer {
    background-color: #f8fafc;
}

QLabel {
    background-color: transparent;
    color: #0f172a;
}

/* Header Navigation Bar */
#HeaderBar {
    background-color: #ffffff;
    border-bottom: 1px solid #cbd5e1;
    min-height: 52px;
    max-height: 52px;
    padding: 0 12px;
}

#AppTitle, QLabel#AppTitle {
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
}

#AppTagline, QLabel#AppTagline {
    font-size: 11px;
    color: #475569;
    margin-left: 8px;
    font-weight: 500;
}

/* Nav Tabs in Header */
QToolButton.NavTab, QToolButton[class="NavTab"] {
    background-color: transparent;
    color: #334155;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}

QToolButton.NavTab:hover, QToolButton[class="NavTab"]:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}

QToolButton.NavTab:checked, QToolButton.NavTab.active, QToolButton[class="NavTab"]:checked {
    background-color: #16a34a;
    color: #ffffff;
}

/* Panels & Cards */
QFrame.Card, QWidget.Panel {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}

/* Sidebar Component Library */
#ComponentLibrary {
    background-color: #f8fafc;
    border-right: 1px solid #cbd5e1;
}

#ComponentLibraryTitle, QLabel#ComponentLibraryTitle {
    font-size: 13px;
    font-weight: 800;
    color: #0f172a;
}

#ComponentCategoryTitle, QLabel#ComponentCategoryTitle {
    font-size: 11px;
    font-weight: 800;
    color: #1e293b;
    margin-top: 8px;
}

#ComponentCard, QFrame.ComponentCard, QFrame[class="ComponentCard"] {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}

#ComponentCard:hover, QFrame.ComponentCard:hover, QFrame[class="ComponentCard"]:hover {
    background-color: #e0f2fe;
    border: 1px solid #0284c7;
}

QLabel.ComponentCardLabel, QLabel[class="ComponentCardLabel"] {
    font-size: 10px;
    color: #0f172a;
    font-weight: 700;
}

/* Properties Panel */
#PropertiesPanel, QFrame#PropertiesPanel {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px;
}

#PropertiesPanelTitle, QLabel#PropertiesPanelTitle {
    font-size: 14px;
    font-weight: 800;
    color: #0f172a;
}

#PropertiesEmptyLabel, QLabel#PropertiesEmptyLabel {
    font-size: 11px;
    color: #334155;
}

#SearchBox, QLineEdit#SearchBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0f172a;
}

#SearchBox:focus, QLineEdit#SearchBox:focus {
    border: 1px solid #2563eb;
}

/* Action Buttons Toolbar */
QPushButton.PrimaryBtn, QPushButton[class="PrimaryBtn"], QPushButton#BtnSimulate {
    background-color: #16a34a;
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
}

QPushButton.PrimaryBtn:hover, QPushButton[class="PrimaryBtn"]:hover, QPushButton#BtnSimulate:hover {
    background-color: #15803d;
}

QPushButton.PrimaryBtn:disabled, QPushButton[class="PrimaryBtn"]:disabled, QPushButton#BtnSimulate:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
    border: 1px solid #cbd5e1;
}

QPushButton.UploadBtn, QPushButton[class="UploadBtn"], QPushButton#BtnUpload {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
}

QPushButton.UploadBtn:hover, QPushButton[class="UploadBtn"]:hover, QPushButton#BtnUpload:hover {
    background-color: #1d4ed8;
}

QPushButton.UploadBtn:disabled, QPushButton[class="UploadBtn"]:disabled, QPushButton#BtnUpload:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
    border: 1px solid #cbd5e1;
}

QPushButton.SecondaryBtn, QPushButton[class="SecondaryBtn"], QPushButton#BtnReset {
    background-color: #e2e8f0;
    color: #0f172a;
    font-weight: 600;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 14px;
}

QPushButton.SecondaryBtn:hover, QPushButton[class="SecondaryBtn"]:hover, QPushButton#BtnReset:hover {
    background-color: #cbd5e1;
}

QPushButton.StopBtn, QPushButton[class="StopBtn"], QPushButton#BtnStop {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
}

QPushButton.StopBtn:hover, QPushButton[class="StopBtn"]:hover, QPushButton#BtnStop:hover {
    background-color: #b91c1c;
}

QPushButton.StopBtn:disabled, QPushButton[class="StopBtn"]:disabled, QPushButton#BtnStop:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
    border: 1px solid #cbd5e1;
}

/* Code Editor */
QPlainTextEdit#CodeEditor, QPlainTextEdit.CodeEditor {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-family: 'Consolas', 'Cascadia Code', 'Fira Code', monospace;
    font-size: 13px;
    padding: 6px;
}

/* Hardware Status Card */
#HardwareCard {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px;
}

#StatusBadgeReady {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 600;
}

#StatusBadgeDisconnected {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 600;
}

/* Combo Box */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    color: #0f172a;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    color: #0f172a;
}

/* Bottom Tab Widget & Tab Bar */
#BottomToolsTabs QTabWidget::pane, QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    border-radius: 6px;
}

#BottomToolsTabs QTabBar::tab, QTabBar::tab {
    background-color: #e2e8f0;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: 600;
    font-size: 11px;
}

#BottomToolsTabs QTabBar::tab:selected, QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0f172a;
    border-bottom: 2px solid #2563eb;
    font-weight: 700;
}

#BottomToolsTabs QTabBar::tab:hover:!selected, QTabBar::tab:hover:!selected {
    background-color: #cbd5e1;
    color: #0f172a;
}

/* Zoom Labels */
#ZoomLabel, QLabel#ZoomLabel, #ZoomValLabel, QLabel#ZoomValLabel {
    color: #1e293b;
    font-size: 11px;
    font-weight: 600;
}

/* Dialogs & Lists */
QDialog {
    background-color: #ffffff;
    color: #0f172a;
}

QDialog QLabel, QDialog QCheckBox {
    color: #0f172a;
}

QDialog QLabel {
    color: #0f172a;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    color: #0f172a;
    font-size: 12px;
}

QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #f1f5f9;
    color: #0f172a;
}

QListWidget::item:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: bold;
}

/* Splitter */
QSplitter::handle {
    background-color: #cbd5e1;
}

QSplitter::handle:horizontal {
    width: 6px;
}

QSplitter::handle:vertical {
    height: 6px;
}

QSplitter::handle:hover {
    background-color: #0284c7;
}

QSplitter::handle:pressed {
    background-color: #0369a1;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #f8fafc;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #f8fafc;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* Menu Bar & Menus */
QMenuBar {
    background-color: #ffffff;
    color: #0f172a;
    border-bottom: 1px solid #cbd5e1;
    padding: 2px 8px;
    font-size: 12px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 5px 10px;
    border-radius: 4px;
    color: #0f172a;
}

QMenuBar::item:selected {
    background-color: #e2e8f0;
    color: #0f172a;
}

QMenuBar::item:pressed {
    background-color: #cbd5e1;
    color: #0f172a;
}

QMenu {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 28px 6px 14px;
    border-radius: 4px;
    font-size: 12px;
    color: #0f172a;
}

QMenu::item:selected {
    background-color: #e0f2fe;
    color: #0284c7;
}

QMenu::item:disabled {
    color: #94a3b8;
    background-color: transparent;
}
QToolButton:disabled {
    color: #94a3b8 !important;
}


QMenu::separator {
    height: 1px;
    background-color: #e2e8f0;
    margin: 4px 2px;
}
"""


def apply_theme(app, theme_name: str = "dark"):
    """Applique le thème (dark ou light) à l'instance QApplication"""
    import PySide6.QtWidgets
    app.setStyle(PySide6.QtWidgets.QStyleFactory.create("Fusion"))
    if theme_name == "light":
        app.setStyleSheet(LIGHT_THEME_QSS)
    else:
        app.setStyleSheet(DARK_THEME_QSS)
