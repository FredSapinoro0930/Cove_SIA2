from resources import asset_path

# ---------- Cove palette (dark theme) ----------
BG = "#0f1216"          # main background
SIDEBAR = "#0b0e12"     # sidebar, a bit darker than the main area
SURFACE = "#171c23"     # cards, lists, player bar
SURFACE_2 = "#1f262f"   # inputs, buttons, hover
BORDER = "#2a323d"
TEXT = "#e9edf1"
MUTED = "#8b95a3"
ACCENT = "#f56e5c"      # coral (from the logo)
ACCENT_HOVER = "#ff8473"
ACCENT_PRESS = "#dd5847"
ACCENT_SOFT = "rgba(245, 110, 92, 0.16)"
TEAL = "#3cc3d6"

# used by the quiz / pokemon answer buttons (set inline when you answer)
CORRECT_STYLE = "background-color: #1f9d61; border: 1px solid #1f9d61; color: #ffffff;"
WRONG_STYLE = "background-color: #d6453d; border: 1px solid #d6453d; color: #ffffff;"
GOOD_TEXT = "color: #4ade80;"
BAD_TEXT = "color: #f87171;"

_chevron = asset_path("chevron_down.svg").replace("\\", "/")

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
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 10px 14px;
    selection-background-color: {ACCENT};
    selection-color: #1b1210;
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}
QComboBox {{
    background-color: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 9px 14px;
}}
QComboBox:hover {{
    border: 1px solid #3a4452;
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
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 9px 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #29323e;
    border: 1px solid #3a4452;
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
QPushButton#primary:disabled {{
    background-color: #3a2724;
    color: #7a5a55;
}}
QPushButton#ghost {{
    background-color: transparent;
    border: 1px solid transparent;
    color: {MUTED};
}}
QPushButton#ghost:hover {{
    background-color: {SURFACE_2};
    color: {TEXT};
}}
QPushButton#answer {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
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
    background: #2a323d;
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
    background: #323b47;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #46515f;
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
    background: #323b47;
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #46515f;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ---------- sidebar ---------- */
QFrame#sidebar {{
    background-color: {SIDEBAR};
    border: none;
    border-right: 1px solid #181d24;
}}
QFrame#sidebar QLabel {{
    background-color: transparent;
}}
QPushButton#navButton {{
    background-color: transparent;
    border: none;
    color: {MUTED};
    text-align: left;
    padding: 12px 16px;
    border-radius: 12px;
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
}}
QFrame#userCard {{
    background-color: {SURFACE};
    border: 1px solid #1d232b;
    border-radius: 14px;
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
    border: 1px solid {BORDER};
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
    font-size: 18px;
    font-weight: 700;
}}
QLabel#cardDesc {{
    color: {MUTED};
}}
QPushButton#gameCard QLabel#cardIcon {{
    background-color: {ACCENT_SOFT};
    border-radius: 14px;
    font-size: 26px;
}}

/* pokemon picture panel (light, so the dark silhouette stands out) */
QLabel#pokemonPanel {{
    background-color: #e6e9ee;
    border-radius: 24px;
}}
"""
