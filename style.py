from resources import asset_path

# ---------- Cove palette (dark theme) ----------
BG = "#0f1216"          # main background
SIDEBAR = "#0b0e12"     # top nav bar, a bit darker than the main area
SURFACE = "#171c23"     # cards, lists, player bar
SURFACE_2 = "#1f262f"   # inputs, buttons, hover
BORDER = "#2a323d"          # decorative borders (cards, dividers)
CONTROL_BORDER = "#6b7686"  # borders of inputs, buttons and sliders: 3:1+ on every surface (WCAG 1.4.11)
FOCUS = "#ffffff"           # keyboard focus ring
TEXT = "#e9edf1"
MUTED = "#8b95a3"
ACCENT = "#f56e5c"      # coral (from the logo)
ACCENT_HOVER = "#ff8473"
ACCENT_PRESS = "#dd5847"
ACCENT_SOFT = "rgba(245, 110, 92, 0.16)"
TEAL = "#3cc3d6"

# used by the quiz / pokemon answer buttons (set inline when you answer)
CORRECT_STYLE = "background-color: #17844f; border: 1px solid #17844f; color: #ffffff;"  # white text 4.7:1
WRONG_STYLE = "background-color: #c63a33; border: 1px solid #c63a33; color: #ffffff;"  # white text 5.2:1
GOOD_TEXT = "color: #4ade80;"
BAD_TEXT = "color: #f87171;"

_chevron = asset_path("chevron_down.svg").replace("\\", "/")
_check = asset_path("check.svg").replace("\\", "/")

STYLESHEET = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Inter 18pt", "Inter", "Segoe UI Variable Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
}}
QLabel {{
    background-color: transparent;
}}
QLabel#title {{
    font-family: "Outfit", "Inter 18pt", "Inter", "Segoe UI", sans-serif;
    font-size: 28px;
    font-weight: 700;
}}
QLabel#subtitle, QLabel#muted {{
    color: {MUTED};
}}
QLabel#credit {{
    color: {MUTED};
    font-size: 12px;
}}
QLabel#sectionLabel {{
    color: {MUTED};
    font-size: 12px;
    font-weight: 600;
}}
QLabel#nowPlaying {{
    font-family: "Outfit", "Inter 18pt", "Inter", "Segoe UI", sans-serif;
    font-size: 15px;
    font-weight: 600;
}}
QLabel#status {{
    color: {MUTED};
    font-size: 13px;
}}
QLabel#bigScore {{
    font-family: "Outfit", "Inter 18pt", "Inter", "Segoe UI", sans-serif;
    font-size: 48px;
    font-weight: 700;
}}
QLabel#question {{
    font-family: "Outfit", "Inter 18pt", "Inter", "Segoe UI", sans-serif;
    font-size: 22px;
    font-weight: 600;
}}
QLabel#stat {{
    font-size: 16px;
    font-weight: 600;
}}
QLabel#lives {{
    color: {ACCENT};
    font-size: 18px;
    font-weight: 600;
}}

/* ---------- inputs ---------- */
QLineEdit {{
    background-color: {SURFACE_2};
    border: 1px solid {CONTROL_BORDER};
    border-radius: 12px;
    padding: 10px 14px;
    selection-background-color: {ACCENT};
    selection-color: #1b1210;
    placeholder-text-color: {MUTED};
}}
QLineEdit:focus {{
    border: 2px solid {FOCUS};
    padding: 9px 13px;
}}
QComboBox {{
    background-color: {SURFACE_2};
    border: 1px solid {CONTROL_BORDER};
    border-radius: 12px;
    padding: 9px 14px;
}}
QComboBox:hover {{
    border: 1px solid #8a95a5;
}}
QComboBox:focus {{
    border: 2px solid {FOCUS};
    padding: 8px 13px;
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox::down-arrow {{
    image: url("{_chevron}");
    width: 12px;
    height: 12px;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: #ffffff;
    outline: none;
}}

/* ---------- buttons ---------- */
QPushButton {{
    background-color: {SURFACE_2};
    border: 1px solid {CONTROL_BORDER};
    border-radius: 12px;
    padding: 9px 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #29323e;
    border: 1px solid #8a95a5;
}}
QPushButton:focus {{
    border: 2px solid {FOCUS};
    padding: 8px 17px;
}}
QPushButton:pressed {{
    background-color: #151a21;
}}
QPushButton:checked {{
    background-color: {ACCENT_SOFT};
    border: 1px solid {ACCENT};
    color: {ACCENT_HOVER};
}}
QPushButton:disabled {{
    background-color: #14181e;
    border: 1px solid #1d232b;
    color: #566070;
}}
QPushButton#primary {{
    background-color: {ACCENT};
    border: none;
    color: #1b1210;
    font-weight: 700;
}}
QPushButton#primary:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#primary:pressed {{
    background-color: {ACCENT_PRESS};
}}
QPushButton#primary:focus {{
    border: 2px solid {FOCUS};
    padding: 7px 16px;
}}
QPushButton#primary:disabled {{
    background-color: #3a2724;
    color: #7a5a55;
}}
QPushButton#ghost {{
    background-color: transparent;
    border: 1px solid transparent;
    color: {MUTED};
}}
QPushButton#ghost:focus {{
    border: 2px solid {FOCUS};
    padding: 8px 17px;
}}
QPushButton#ghost:hover {{
    background-color: {SURFACE_2};
    color: {TEXT};
}}
QPushButton#answer {{
    background-color: {SURFACE};
    border: 1px solid {CONTROL_BORDER};
    border-radius: 14px;
    padding: 12px 18px;
    text-align: left;
    font-weight: 500;
    font-size: 15px;
}}
QPushButton#answer:hover {{
    background-color: {SURFACE_2};
    border: 1px solid {ACCENT};
}}

/* ---------- lists ---------- */
QListWidget {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 12px;
    border-radius: 8px;
}}
QListWidget::item:hover {{
    background-color: {SURFACE_2};
}}
QListWidget::item:selected {{
    background-color: {ACCENT_SOFT};
    color: #ffffff;
}}

/* ---------- sliders ---------- */
QSlider::groove:horizontal {{
    height: 4px;
    background: #6b7686;
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: #ffffff;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT_HOVER};
}}

/* ---------- scrollbars ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #5b6674;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #76808f;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: #5b6674;
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #76808f;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ---------- top navigation bar ---------- */
QFrame#topbar {{
    background-color: {SIDEBAR};
    border: none;
    border-bottom: 1px solid {BORDER};
}}
QFrame#topbar QLabel {{
    background-color: transparent;
}}
QPushButton#navButton {{
    background-color: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    color: {MUTED};
    padding: 10px 18px 7px 18px;
    border-radius: 0px;
    font-size: 15px;
    font-weight: 600;
}}
QPushButton#navButton:hover {{
    background-color: #141920;
    color: {TEXT};
}}
QPushButton#navButton:checked {{
    background-color: {ACCENT_SOFT};
    color: {ACCENT_HOVER};
    border: none;
    border-bottom: 3px solid {ACCENT};
}}
QPushButton#navButton:focus {{
    border: 2px solid {FOCUS};
    padding: 8px 16px 6px 16px;
}}
QFrame#userCard {{
    background-color: transparent;
    border: none;
}}
QFrame#userCard QLabel {{
    background-color: transparent;
}}
QFrame#userCard QLabel#avatar {{
    background-color: {ACCENT};
    color: #1b1210;
    font-weight: 700;
    font-size: 15px;
    border-radius: 18px;
}}
QLabel#userName {{
    font-weight: 600;
}}

/* ---------- cards ---------- */
QFrame#card, QFrame#playerBar {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 18px;
}}
QFrame#card QLabel, QFrame#playerBar QLabel {{
    background-color: transparent;
}}
QFrame#playerBar QPushButton {{
    background-color: transparent;
    border: 1px solid transparent;
}}
QFrame#playerBar QPushButton:hover {{
    background-color: {SURFACE_2};
}}
QFrame#playerBar QPushButton:checked {{
    background-color: {ACCENT_SOFT};
    border: 1px solid {ACCENT};
}}
QFrame#playerBar QPushButton#primary {{
    background-color: {ACCENT};
    color: #1b1210;
    border: none;
}}
QFrame#playerBar QPushButton#primary:hover {{
    background-color: {ACCENT_HOVER};
}}
QFrame#playerBar QSlider {{
    background-color: transparent;
}}

QPushButton#gameCard {{
    background-color: {SURFACE};
    border: 1px solid {CONTROL_BORDER};
    border-radius: 18px;
    padding: 0px;
    text-align: left;
}}
QPushButton#gameCard:hover {{
    background-color: {SURFACE_2};
    border: 1px solid {ACCENT};
}}
QPushButton#gameCard QLabel {{
    background-color: transparent;
}}
QLabel#cardTitle {{
    font-family: "Outfit", "Inter 18pt", "Inter", "Segoe UI", sans-serif;
    font-size: 18px;
    font-weight: 700;
}}
QLabel#cardDesc {{
    color: {MUTED};
}}

/* pokemon picture panel (light, so the dark silhouette stands out) */
QLabel#pokemonPanel {{
    background-color: #e6e9ee;
    border-radius: 24px;
}}

/* ---------- checkbox ---------- */
QCheckBox {{
    background-color: transparent;
    spacing: 8px;
    padding: 4px 2px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {CONTROL_BORDER};
    border-radius: 5px;
    background-color: {SURFACE_2};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border: 1px solid {ACCENT};
    image: url("{_check}");
}}
QCheckBox::indicator:focus {{
    border: 2px solid {FOCUS};
}}

/* ---------- tabs ---------- */
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {BORDER};
}}
QTabBar::tab {{
    background-color: transparent;
    color: {MUTED};
    border: none;
    border-bottom: 3px solid transparent;
    padding: 8px 18px;
    font-weight: 600;
}}
QTabBar::tab:hover {{
    color: {TEXT};
}}
QTabBar::tab:selected {{
    color: {ACCENT_HOVER};
    border-bottom: 3px solid {ACCENT};
}}

/* ---------- menus ---------- */
QMenu {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 18px;
}}
QMenu::item:selected {{
    background-color: {ACCENT_SOFT};
}}
QScrollArea {{
    border: none;
}}
"""
