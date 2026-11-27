from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt
from trivia_game import TriviaGame
from pokemon_game import PokemonGame
from flag_game import FlagGame


class GameCard(QPushButton):
    """A big clickable card with a title and a short description."""

    def __init__(self, title, description):
        super().__init__()
        self.setObjectName("gameCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(110)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        desc_label = QLabel(description)
        self.desc_label = desc_label
        desc_label.setObjectName("cardDesc")
        desc_label.setWordWrap(True)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.addStretch()
        text.addWidget(title_label)
        text.addWidget(desc_label)
        text.addStretch()

        row = QHBoxLayout()
        row.setContentsMargins(24, 16, 24, 16)
        row.addLayout(text, 1)
        self.setLayout(row)

        # let clicks pass through the labels to the button underneath
        for label in (title_label, desc_label):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_description(self, text):
        self.desc_label.setText(text)


class GamesPage(QWidget):
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username

        # ----- games menu -----
        menu = QWidget()
        title = QLabel("Games")
        title.setObjectName("title")
        subtitle = QLabel("Pick a game, beat your best score and climb the leaderboard")
        subtitle.setObjectName("subtitle")

        trivia_card = GameCard("Trivia Quiz", "Test your knowledge and climb the leaderboard")
        trivia_card.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        pokemon_card = GameCard("Who's That Pok\u00E9mon?", "Guess from the silhouette. You have 3 lives")
        pokemon_card.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        flag_card = GameCard("Guess the Flag", "Name the country from its flag. You have 3 lives")
        flag_card.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        menu_layout = QVBoxLayout()
        menu_layout.setContentsMargins(32, 28, 32, 20)
        menu_layout.setSpacing(12)
        menu_layout.addWidget(title)
        menu_layout.addWidget(subtitle)
        menu_layout.addSpacing(10)
        menu_layout.addWidget(trivia_card)
        menu_layout.addWidget(pokemon_card)
        menu_layout.addWidget(flag_card)
        menu_layout.addStretch()
        menu.setLayout(menu_layout)

        # ----- the games themselves -----
        back_to_menu = lambda: self.stack.setCurrentIndex(0)
        self.trivia = TriviaGame(user_id, username, on_back=back_to_menu)
        self.pokemon = PokemonGame(user_id, username, on_back=back_to_menu)
        self.flags = FlagGame(user_id, username, on_back=back_to_menu)

        self.stack = QStackedWidget()
        self.stack.addWidget(menu)           # 0
        self.stack.addWidget(self.trivia)    # 1
        self.stack.addWidget(self.pokemon)   # 2
        self.stack.addWidget(self.flags)     # 3

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)