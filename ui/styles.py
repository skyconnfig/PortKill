DARK_QSS = r'''
QMainWindow, QWidget {
    background: #0D1117;
    color: #F0F6FC;
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
}
QFrame#topbar {
    background: rgba(13, 17, 23, 0.96);
    border-bottom: 1px solid #21262D;
}
QFrame#inputCard, QFrame#resultCard, QFrame#emptyCard, QFrame#historyCard {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
}
QFrame#resultCard:hover {
    border-color: #484F58;
}
QLabel#appTitle { font-size: 16px; font-weight: 700; color: #F0F6FC; }
QLabel#appSubtitle { font-size: 11px; color: #8B949E; }
QLabel#sectionTitle { font-size: 15px; font-weight: 700; color: #F0F6FC; }
QLabel#eyebrow { font-size: 11px; font-weight: 700; color: #8B949E; }
QLabel#helper { color: #8B949E; font-size: 11px; }
QLabel#pathLabel { color: #8B949E; font-family: "Cascadia Mono", Consolas, monospace; font-size: 11px; }
QLabel#processName { font-size: 15px; font-weight: 700; color: #F0F6FC; }
QLabel#metaLabel { color: #8B949E; font-size: 11px; }
QLabel#valueLabel { color: #F0F6FC; font-size: 12px; font-weight: 600; }
QLabel#statusLabel { font-size: 14px; font-weight: 700; }
QLabel#statusLabel[status="free"] { color: #3FB950; }
QLabel#statusLabel[status="busy"] { color: #D29922; }
QLabel#statusLabel[status="occupied"] { color: #F85149; }
QLabel#statusLabel[status="error"] { color: #F85149; }
QLineEdit {
    background: #0D1117;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 10px 12px;
    color: #F0F6FC;
    font-size: 18px;
    selection-background-color: #2F81F7;
}
QLineEdit:focus { border: 1px solid #2F81F7; }
QPushButton {
    background: #21262D;
    border: 1px solid #30363D;
    border-radius: 7px;
    padding: 7px 12px;
    color: #F0F6FC;
}
QPushButton:hover { background: #30363D; border-color: #484F58; }
QPushButton:pressed { background: #161B22; }
QPushButton:disabled { color: #484F58; background: #161B22; border-color: #21262D; }
QPushButton#primaryButton {
    background: #2F81F7;
    border-color: #2F81F7;
    color: white;
    font-weight: 700;
    padding: 9px 18px;
}
QPushButton#primaryButton:hover { background: #388BFD; }
QPushButton#dangerButton {
    background: #3A1F24;
    border-color: #6E2B35;
    color: #FF7B72;
    font-weight: 700;
}
QPushButton#dangerButton:hover { background: #54252C; }
QPushButton#forceButton {
    background: #F85149;
    border-color: #F85149;
    color: #FFFFFF;
    font-weight: 700;
}
QPushButton#forceButton:hover { background: #FF6A63; border-color: #FF6A63; }
QPushButton#forceButton:disabled { background: #3A1F24; border-color: #6E2B35; color: #8B949E; }
QPushButton#iconButton {
    border: none;
    background: transparent;
    padding: 6px;
}
QPushButton#iconButton:hover { background: #21262D; }
QPushButton#historyChip {
    border-radius: 13px;
    padding: 4px 10px;
    background: #21262D;
    color: #8B949E;
}
QPushButton#historyChip:hover { color: #58A6FF; border-color: #2F81F7; }
QLabel#badge {
    background: #1F3047;
    color: #58A6FF;
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
}
QLabel#serviceBadge {
    background: #2D2415;
    color: #D29922;
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 11px;
}
QLabel#protectedBadge {
    background: #3A1F24;
    color: #FF7B72;
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 11px;
}
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 4px 0; }
QScrollBar::handle:vertical { background: #30363D; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QFrame#toast {
    background: #1F2937;
    border: 1px solid #3B4858;
    border-radius: 9px;
}
QLabel#toastText { color: #F0F6FC; font-weight: 600; }
QDialog { background: #161B22; }
QDialog QLabel { color: #F0F6FC; }
'''

