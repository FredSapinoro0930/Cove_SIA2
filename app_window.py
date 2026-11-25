from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from widgets import make_logo
from music_page import MusicPage
from movies_page import MoviesPage
from games_page import GamesPage


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

        # ----- sidebar -----
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")  # style.py styles it by this name
        sidebar.setFixedWidth(230)

        logo = make_logo(170)

        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(16, 24, 16, 16)
        side_layout.setSpacing(4)
        side_layout.addWidget(logo)
        side_layout.addSpacing(24)

        # nav buttons: only one can be selected at a time
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for index, label in enumerate(["Music", "Movies && TV", "Games"]):  # && shows as one &
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            self.nav_group.addButton(btn, index)  # the id is the page index
            side_layout.addWidget(btn)
        self.nav_group.button(0).setChecked(True)
        self.nav_group.idClicked.connect(self.pages.setCurrentIndex)
        self.pages.currentChanged.connect(self.on_page_changed)

        side_layout.addStretch()

        # user card: round avatar with the first letter, name, and a logout button
        avatar = QLabel(username[:1].upper() or "?")
        avatar.setObjectName("avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(36, 36)
        name_label = QLabel(username)
        name_label.setObjectName("userName")
        logout_btn = QPushButton("Log out")
        logout_btn.setObjectName("ghost")
        logout_btn.clicked.connect(self.handle_logout)

        user_card = QFrame()
        user_card.setObjectName("userCard")
        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(10)
        card_layout.addWidget(avatar)
        card_layout.addWidget(name_label, 1)
        card_layout.addWidget(logout_btn)
        user_card.setLayout(card_layout)
        side_layout.addWidget(user_card)
        sidebar.setLayout(side_layout)

        # ----- sidebar on the left, pages on the right -----
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages)
        self.setLayout(layout)

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