from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QButtonGroup, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
import db
from widgets import make_logo, keyboard_focus_only, section_label
from music_page import MusicPage
from movies_page import MoviesPage
from games_page import GamesPage, GameCard

TOPBAR_HEIGHT = 64
# (name in the scores table, title on the card, page number inside the Games page)
HOME_GAMES = [("trivia", "Trivia Quiz", 1),
              ("pokemon", "Who's That Pok\u00e9mon?", 2),
              ("flags", "Guess the Flag", 3)]


class HomePage(QScrollArea):
    """The first screen after login: shortcuts, your playlists and your best scores."""

    def __init__(self, user_id, username, open_music, open_movies, open_games,
                 open_library, open_game):
        super().__init__()
        self.user_id = user_id
        self.open_library = open_library

        title = QLabel(f"Welcome back, {username}")
        title.setTextFormat(Qt.TextFormat.PlainText)  # show the name exactly as typed
        title.setObjectName("title")
        subtitle = QLabel("What would you like to do today?")
        subtitle.setObjectName("subtitle")

        shortcuts = QHBoxLayout()
        shortcuts.setSpacing(14)
        for name, description, action in (
                ("Music", "Free songs and popular previews", open_music),
                ("Movies && TV", "Free films and classic shows", open_movies),
                ("Games", "Beat your best score", open_games)):
            card = GameCard(name.replace("&&", "&"), description)
            card.clicked.connect(lambda _=False, go=action: go())
            shortcuts.addWidget(card, 1)

        self.library_row = QVBoxLayout()
        self.library_row.setSpacing(8)

        scores = QHBoxLayout()
        scores.setSpacing(14)
        self.score_cards = {}
        for game, name, number in HOME_GAMES:
            card = GameCard(name, "")
            card.clicked.connect(lambda _=False, n=number: open_game(n))
            self.score_cards[game] = card
            scores.addWidget(card, 1)

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(shortcuts)
        layout.addSpacing(14)
        layout.addWidget(section_label("YOUR MUSIC"))
        layout.addLayout(self.library_row)
        layout.addSpacing(14)
        layout.addWidget(section_label("YOUR BEST SCORES  \u00b7  CLICK TO PLAY"))
        layout.addLayout(scores)
        layout.addStretch()
        content = QWidget()
        content.setLayout(layout)
        self.setWidgetResizable(True)
        self.setWidget(content)
        self.refresh()

    def refresh(self):
        """Playlists and scores change while the app is open, so reload them."""
        for game, card in self.score_cards.items():
            best = db.get_best_score(self.user_id, game)
            card.set_description("Not played yet" if best is None else f"Best score: {best}")

        while self.library_row.count():
            old = self.library_row.takeAt(0).widget()
            old.hide()
            old.deleteLater()
        # 0 is Favorites in the Music page's library list
        for view, name in [(0, "Favorites")] + list(db.get_playlists(self.user_id)):
            button = QPushButton(name.replace("&", "&&"))  # show & as typed
            button.setMinimumHeight(40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, v=view: self.open_library(v))
            self.library_row.addWidget(button)
        keyboard_focus_only(self)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()


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
        self.home_page = HomePage(
            user_id, username,
            open_music=lambda: self.go_to(self.music_page),
            open_movies=lambda: self.go_to(self.movies_page),
            open_games=lambda: self.open_game(0),  # 0 is the games menu
            open_library=self.open_library,
            open_game=self.open_game)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.home_page)    # index 0
        self.pages.addWidget(self.music_page)   # index 1
        self.pages.addWidget(self.movies_page)  # index 2
        self.pages.addWidget(self.games_page)   # index 3

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
        for index, label in enumerate(["Home", "Music", "Movies && TV", "Games"]):  # && shows as one &
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

    # ---------- shortcuts used by the home page ----------
    def go_to(self, page):
        index = self.pages.indexOf(page)
        self.nav_group.button(index).setChecked(True)  # highlight it in the top bar
        self.pages.setCurrentIndex(index)

    def open_library(self, view):
        library = self.music_page.library
        self.go_to(self.music_page)
        library.view_box.setCurrentIndex(max(library.view_box.findData(view), 0))

    def open_game(self, number):
        self.games_page.stack.setCurrentIndex(number)
        self.go_to(self.games_page)

    def on_page_changed(self, index):
        if self.pages.widget(index) is self.movies_page:
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