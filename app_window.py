from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from widgets import make_logo, keyboard_focus_only
from music_page import MusicPage
from movies_page import MoviesPage
from games_page import GamesPage

TOPBAR_HEIGHT = 64


class AppWindow(QWidget):
    def __init__(self, user_id, username, on_logout):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.on_logout = on_logout  # function from main.py that shows the login window again
        self.setWindowTitle("Cove")

        # fit the window to the screen so the bottom controls are never cut off
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(min(1200, screen.width() - 40), min(720, screen.height() - 80))

        # ----- the pages (only one is visible at a time) -----
        self.music_page = MusicPage(user_id, username)
        self.movies_page = MoviesPage(user_id, username)
        self.games_page = GamesPage(user_id, username)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.music_page)   # index 0
        self.pages.addWidget(self.movies_page)  # index 1
        self.pages.addWidget(self.games_page)   # index 2

        # ----- top navigation bar -----
        topbar = QFrame()
        topbar.setObjectName("topbar")  # style.py styles it by this name
        topbar.setFixedHeight(TOPBAR_HEIGHT)

        logo = make_logo(100)
        logo.setAccessibleName("Cove")

        # nav buttons: only one can be selected at a time
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        nav_row = QHBoxLayout()
        nav_row.setSpacing(4)
        for index, label in enumerate(["Music", "Movies && TV", "Games"]):  # && shows as one &
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setFixedHeight(TOPBAR_HEIGHT - 2)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setAccessibleName(label.replace("&&", "and") + " page")
            self.nav_group.addButton(btn, index)  # the id is the page index
            nav_row.addWidget(btn)
        self.nav_group.button(0).setChecked(True)
        self.nav_group.idClicked.connect(self.pages.setCurrentIndex)
        self.pages.currentChanged.connect(self.on_page_changed)

        # account: round avatar with the first letter, name, and a logout button
        avatar = QLabel(username[:1].upper() or "?")
        avatar.setObjectName("avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(36, 36)
        name_label = QLabel(username)
        name_label.setObjectName("userName")
        logout_btn = QPushButton("Log out")
        logout_btn.setObjectName("ghost")
        logout_btn.setMinimumHeight(36)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setAccessibleName("Log out")
        logout_btn.clicked.connect(self.handle_logout)

        user_card = QFrame()
        user_card.setObjectName("userCard")
        user_row = QHBoxLayout()
        user_row.setContentsMargins(0, 0, 0, 0)
        user_row.setSpacing(10)
        user_row.addWidget(avatar)
        user_row.addWidget(name_label)
        user_row.addSpacing(6)
        user_row.addWidget(logout_btn)
        user_card.setLayout(user_row)

        bar_layout = QHBoxLayout()
        bar_layout.setContentsMargins(24, 0, 24, 0)
        bar_layout.setSpacing(28)
        bar_layout.addWidget(logo)
        bar_layout.addLayout(nav_row)
        bar_layout.addStretch()
        bar_layout.addWidget(user_card)
        topbar.setLayout(bar_layout)

        # ----- nav bar on top, pages underneath -----
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(topbar)
        layout.addWidget(self.pages, 1)
        self.setLayout(layout)

        keyboard_focus_only(self)  # focus ring appears for Tab, not for mouse clicks
        # start with no button focused, so no focus ring shows until the user presses Tab
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setFocus()

    def on_page_changed(self, index):
        if index == 1:
            self.music_page.pause()    # don't play music under a movie
        else:
            self.movies_page.pause()   # leaving the movies page pauses the video

    def stop_everything(self):
        self.music_page.stop()
        self.movies_page.stop()

    def handle_logout(self):
        self.stop_everything()
        self.on_logout()   # show the login window again (defined in main.py)
        self.close()

    def closeEvent(self, event):
        self.stop_everything()  # also stops playback if you close with the X
        event.accept()