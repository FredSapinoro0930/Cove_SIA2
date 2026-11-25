from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QStackedWidget, QListWidget, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor
import db
import pokemon
from style import CORRECT_STYLE, WRONG_STYLE, GOOD_TEXT, BAD_TEXT

GAME_NAME = "pokemon"
STARTING_LIVES = 3
IMAGE_SIZE = 280


def make_silhouette(pixmap):
    """Same shape as the picture, but solid dark, so only the outline shows."""
    silhouette = QPixmap(pixmap.size())
    silhouette.fill(Qt.GlobalColor.transparent)
    painter = QPainter(silhouette)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(silhouette.rect(), QColor("#1b1b1b"))
    painter.end()
    return silhouette


class PokemonGame(QWidget):
    def __init__(self, user_id, username, on_back):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.on_back = on_back  # function from games_page.py that returns to the games menu
        self.max_id = 151
        self.lives = STARTING_LIVES
        self.score = 0
        self.rounds = 0
        self.current = None
        self.reveal_pixmap = None
        self.answered = True
        self.next_action = self.load_round  # what the "Next" button does right now

        # three screens inside this widget: setup, play, result
        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_setup_view())   # 0
        self.stack.addWidget(self.build_play_view())    # 1
        self.stack.addWidget(self.build_result_view())  # 2

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    # ---------- building the screens ----------
    def build_setup_view(self):
        view = QWidget()

        title = QLabel("Who's That Pokémon?")
        title.setObjectName("title")
        rules = QLabel(
            "Guess the Pokémon from its silhouette. You have 3 lives, "
            "and your score is how many you get right before they run out."
        )
        rules.setWordWrap(True)
        rules.setObjectName("subtitle")

        self.generation_box = QComboBox()
        for label, max_id in pokemon.GENERATIONS.items():
            self.generation_box.addItem(label, max_id)

        start_btn = QPushButton("Start game")
        start_btn.setObjectName("primary")
        start_btn.setMinimumHeight(46)
        back_btn = QPushButton("Back to games")
        back_btn.setObjectName("ghost")
        self.generation_box.setMinimumHeight(42)

        self.setup_status = QLabel("")
        self.best_label = QLabel("")
        self.leaderboard = QListWidget()
        self.leaderboard.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.leaderboard.setMaximumHeight(170)

        credit = QLabel("Data and artwork from PokéAPI (pokeapi.co). Pokémon is a trademark of its owners.")
        credit.setObjectName("credit")
        self.setup_status.setObjectName("status")
        self.best_label.setObjectName("stat")
        credit.setWordWrap(True)

        start_btn.clicked.connect(self.start_game)
        back_btn.clicked.connect(self.back_to_games)

        sec = QLabel("GENERATION")
        sec.setObjectName("sectionLabel")
        sec2 = QLabel("LEADERBOARD  ·  TOP 5")
        sec2.setObjectName("sectionLabel")

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addWidget(rules)
        layout.addSpacing(10)
        layout.addWidget(sec)
        layout.addWidget(self.generation_box)
        layout.addSpacing(8)
        layout.addWidget(start_btn)
        layout.addWidget(self.setup_status)
        layout.addSpacing(8)
        layout.addWidget(self.best_label)
        layout.addWidget(sec2)
        layout.addWidget(self.leaderboard)
        layout.addStretch()
        layout.addWidget(credit)
        layout.addWidget(back_btn)
        view.setLayout(layout)
        return view

    def build_play_view(self):
        view = QWidget()

        self.lives_label = QLabel("")
        self.lives_label.setObjectName("lives")
        self.score_label = QLabel("")
        self.score_label.setObjectName("stat")
        top = QHBoxLayout()
        top.addWidget(self.lives_label)
        top.addStretch()
        top.addWidget(self.score_label)

        # light panel behind the picture, so the dark silhouette is visible on the dark theme
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(IMAGE_SIZE + 24, IMAGE_SIZE + 24)
        self.image_label.setObjectName("pokemonPanel")

        prompt = QLabel("Who's that Pokémon?")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prompt.setObjectName("question")

        self.answer_buttons = []
        grid = QGridLayout()
        grid.setSpacing(10)
        for i in range(4):
            btn = QPushButton("")
            btn.setObjectName("answer")
            btn.setMinimumHeight(52)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=i: self.on_answer(i))
            self.answer_buttons.append(btn)
            grid.addWidget(btn, i // 2, i % 2)

        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setWordWrap(True)

        self.end_btn = QPushButton("End game")
        self.end_btn.setObjectName("ghost")
        self.end_btn.clicked.connect(self.end_game)
        self.next_btn = QPushButton("Next Pokémon")
        self.next_btn.setObjectName("primary")
        self.next_btn.setMinimumHeight(44)
        self.next_btn.clicked.connect(lambda: self.next_action())
        bottom = QHBoxLayout()
        bottom.addWidget(self.end_btn)
        bottom.addStretch()
        bottom.addWidget(self.next_btn)

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(10)
        layout.addLayout(top)
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(prompt)
        layout.addLayout(grid)
        layout.addWidget(self.feedback_label)
        layout.addStretch()
        layout.addLayout(bottom)
        view.setLayout(layout)
        return view

    def build_result_view(self):
        view = QWidget()

        heading = QLabel("Game over")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setObjectName("subtitle")

        self.result_title = QLabel("")
        self.result_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_title.setObjectName("bigScore")

        self.result_note = QLabel("")
        self.result_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_note.setObjectName("subtitle")

        again_btn = QPushButton("Play again")
        again_btn.setObjectName("primary")
        again_btn.setMinimumHeight(46)
        again_btn.clicked.connect(self.go_to_setup)
        back_btn = QPushButton("Back to games")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self.back_to_games)

        layout = QVBoxLayout()
        layout.setContentsMargins(120, 28, 120, 20)
        layout.addStretch()
        layout.addWidget(heading)
        layout.addWidget(self.result_title)
        layout.addWidget(self.result_note)
        layout.addSpacing(16)
        layout.addWidget(again_btn)
        layout.addWidget(back_btn)
        layout.addStretch()
        view.setLayout(layout)
        return view

    # ---------- setup screen ----------
    def showEvent(self, event):
        super().showEvent(event)
        if self.stack.currentIndex() == 0:
            self.refresh_scores()

    def refresh_scores(self):
        best = db.get_best_score(self.user_id, GAME_NAME)
        if best is None:
            self.best_label.setText("You haven't played yet")
        else:
            self.best_label.setText(f"Your best score: {best}")

        self.leaderboard.clear()
        rows = db.get_leaderboard(GAME_NAME)
        if not rows:
            self.leaderboard.addItem("No scores yet. Be the first!")
        for rank, (name, score) in enumerate(rows, start=1):
            self.leaderboard.addItem(f"{rank}. {name} - {score}")

    def go_to_setup(self):
        self.stack.setCurrentIndex(0)
        self.setup_status.setText("")
        self.refresh_scores()

    def back_to_games(self):
        self.go_to_setup()  # reset first, so the game opens on the setup screen next time
        self.on_back()

    # ---------- playing ----------
    def start_game(self):
        self.max_id = self.generation_box.currentData()
        self.lives = STARTING_LIVES
        self.score = 0
        self.rounds = 0
        self.update_labels()
        self.image_label.clear()
        self.stack.setCurrentIndex(1)
        self.load_round()

    def update_labels(self):
        self.lives_label.setText("Lives: " + "♥ " * self.lives)
        self.score_label.setText(f"Score: {self.score}")

    def show_load_error(self, message):
        self.feedback_label.setStyleSheet(BAD_TEXT)
        self.feedback_label.setText(message)
        self.next_btn.setText("Try again")
        self.next_action = self.load_round
        self.next_btn.setVisible(True)
        self.end_btn.setEnabled(True)

    def load_round(self):
        self.answered = True  # blocks clicks until the new round is ready
        self.next_btn.setVisible(False)
        self.end_btn.setEnabled(False)
        self.feedback_label.setStyleSheet("")
        self.feedback_label.setText("Loading the next Pokémon...")
        for btn in self.answer_buttons:
            btn.setEnabled(False)
        QApplication.processEvents()  # lets the screen update before the requests run

        try:
            rnd = pokemon.make_round(self.max_id)
        except Exception as e:
            self.show_load_error(str(e))
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(rnd["image"]):
            self.show_load_error("Could not read the Pokémon image. Try again.")
            return
        pixmap = pixmap.scaled(
            IMAGE_SIZE, IMAGE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.reveal_pixmap = pixmap
        self.image_label.setPixmap(make_silhouette(pixmap))
        self.current = rnd
        for i, btn in enumerate(self.answer_buttons):
            btn.setText(rnd["choices"][i])
            btn.setStyleSheet("")  # clear the green/red from the last round
            btn.setEnabled(True)
        self.feedback_label.setText("")
        self.end_btn.setEnabled(True)
        self.answered = False

    def on_answer(self, i):
        if self.answered:
            return  # ignore extra clicks after answering
        self.answered = True
        self.rounds += 1

        correct = self.current["name"]
        chosen = self.answer_buttons[i]
        for btn in self.answer_buttons:
            if btn.text() == correct:
                btn.setStyleSheet(CORRECT_STYLE)
            elif btn is chosen:
                btn.setStyleSheet(WRONG_STYLE)

        self.image_label.setPixmap(self.reveal_pixmap)  # show the real artwork

        if chosen.text() == correct:
            self.score += 1
            self.feedback_label.setStyleSheet(GOOD_TEXT)
            self.feedback_label.setText(f"Correct! It's {correct}!")
        else:
            self.lives -= 1
            self.feedback_label.setStyleSheet(BAD_TEXT)
            self.feedback_label.setText(f"Wrong! It was {correct}.")

        self.update_labels()
        if self.lives <= 0:
            self.next_btn.setText("See results")
            self.next_action = self.finish_game
        else:
            self.next_btn.setText("Next Pokémon")
            self.next_action = self.load_round
        self.next_btn.setVisible(True)

    def end_game(self):
        if self.rounds == 0:
            self.go_to_setup()  # nothing to save yet
        else:
            self.finish_game()  # cash out: saves the score you have so far

    def finish_game(self):
        previous = db.get_best_score(self.user_id, GAME_NAME)  # read before saving this one
        db.save_score(self.user_id, GAME_NAME, self.score, self.rounds)

        self.result_title.setText(f"Score: {self.score}")
        if previous is None:
            note = "First score saved!"
        elif self.score > previous:
            note = f"New personal best! (previous best: {previous})"
        else:
            note = f"Your best is {previous}"
        self.result_note.setText(note)
        self.stack.setCurrentIndex(2)