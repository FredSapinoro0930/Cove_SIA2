from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QListWidget, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import db
import flags
from style import CORRECT_STYLE, WRONG_STYLE, GOOD_TEXT, BAD_TEXT

GAME_NAME = "flags"
LIVES = 3


class FlagGame(QWidget):
    def __init__(self, user_id, username, on_back):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.on_back = on_back  # function from games_page.py that returns to the games menu
        self.countries = []
        self.question = None
        self.score = 0
        self.lives = LIVES
        self.shown = 0       # how many flags were shown this round
        self.answered = False

        # three screens: setup, play, result
        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_setup_view())   # 0
        self.stack.addWidget(self.build_play_view())    # 1
        self.stack.addWidget(self.build_result_view())  # 2

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    # ---------- building the screens ----------
    @staticmethod
    def section_label(text):
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def build_setup_view(self):
        view = QWidget()

        title = QLabel("Guess the Flag")
        title.setObjectName("title")
        subtitle = QLabel("Name the country from its flag. You have 3 lives.")
        subtitle.setObjectName("subtitle")

        start_btn = QPushButton("Start game")
        start_btn.setObjectName("primary")
        start_btn.setMinimumHeight(46)
        back_btn = QPushButton("Back to games")
        back_btn.setObjectName("ghost")

        self.best_label = QLabel("")
        self.best_label.setObjectName("stat")
        self.leaderboard = QListWidget()
        self.leaderboard.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.leaderboard.setMaximumHeight(170)

        self.setup_status = QLabel("")
        self.setup_status.setObjectName("status")
        credit = QLabel("Flags and country names from FlagCDN (flagcdn.com)")
        credit.setObjectName("credit")

        start_btn.clicked.connect(self.start_round)
        back_btn.clicked.connect(self.back_to_games)

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)
        layout.addWidget(start_btn)
        layout.addWidget(self.setup_status)
        layout.addSpacing(8)
        layout.addWidget(self.best_label)
        layout.addWidget(self.section_label("LEADERBOARD  ·  TOP 5"))
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

        # light panel so every flag (even white ones) stands out on the dark theme
        self.flag_label = QLabel("")
        self.flag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flag_label.setFixedSize(400, 250)
        self.flag_label.setStyleSheet("background-color: #e6e9ee; border-radius: 24px;")

        question_label = QLabel("Which country does this flag belong to?")
        question_label.setObjectName("sectionLabel")

        self.answer_buttons = []
        answers_layout = QVBoxLayout()
        answers_layout.setSpacing(10)
        for i in range(4):
            btn = QPushButton("")
            btn.setObjectName("answer")
            btn.setMinimumHeight(48)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=i: self.on_answer(i))
            self.answer_buttons.append(btn)
            answers_layout.addWidget(btn)

        self.feedback_label = QLabel("")
        self.feedback_label.setWordWrap(True)

        self.next_btn = QPushButton("Next flag")
        self.next_btn.setObjectName("primary")
        self.next_btn.setMinimumHeight(44)
        self.next_btn.clicked.connect(self.next_question)
        quit_btn = QPushButton("Quit round")
        quit_btn.setObjectName("ghost")
        quit_btn.clicked.connect(self.quit_round)
        bottom = QHBoxLayout()
        bottom.addWidget(quit_btn)
        bottom.addStretch()
        bottom.addWidget(self.next_btn)

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.addLayout(top)
        layout.addSpacing(10)
        layout.addWidget(self.flag_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(10)
        layout.addWidget(question_label)
        layout.addLayout(answers_layout)
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
        self.refresh_scores()

    def back_to_games(self):
        self.go_to_setup()  # reset first, so the game opens on the setup screen next time
        self.on_back()

    # ---------- playing a round ----------
    def start_round(self):
        self.setup_status.setText("Loading flags...")
        QApplication.processEvents()  # lets the label update before the request runs
        try:
            self.countries = flags.get_countries()
        except Exception as e:
            self.setup_status.setText(str(e))
            return

        self.score = 0
        self.lives = LIVES
        self.shown = 0
        if self.show_question():
            self.setup_status.setText("")
            self.stack.setCurrentIndex(1)

    def show_question(self):
        """Loads the next flag. Returns False if the image could not be loaded."""
        error = "Could not load the flag image."
        for _ in range(3):  # try a few different flags before giving up
            q = flags.make_question(self.countries)
            try:
                data = flags.get_flag_image(q["flag_url"])
            except Exception as e:
                error = str(e)
                continue
            pixmap = QPixmap()
            if not pixmap.loadFromData(data):
                continue

            self.question = q
            self.shown += 1
            self.flag_label.setPixmap(pixmap.scaled(
                380, 230,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
            self.answered = False
            for i, btn in enumerate(self.answer_buttons):
                btn.setText(q["answers"][i])
                btn.setStyleSheet("")  # clear the green/red from the last flag
            self.feedback_label.setText("")
            self.next_btn.setVisible(False)
            self.update_status_labels()
            return True

        self.setup_status.setText(error)
        return False

    def update_status_labels(self):
        self.lives_label.setText("\u2665 " * self.lives)
        self.score_label.setText(f"Score: {self.score}")

    def on_answer(self, i):
        if self.answered:
            return  # ignore extra clicks after answering
        self.answered = True

        chosen = self.answer_buttons[i]
        correct_text = self.question["correct"]

        for btn in self.answer_buttons:
            if btn.text() == correct_text:
                btn.setStyleSheet(CORRECT_STYLE)
            elif btn is chosen:
                btn.setStyleSheet(WRONG_STYLE)

        if chosen.text() == correct_text:
            self.score += 1
            self.feedback_label.setStyleSheet(GOOD_TEXT)
            self.feedback_label.setText("Correct!")
        else:
            self.lives -= 1
            self.feedback_label.setStyleSheet(BAD_TEXT)
            self.feedback_label.setText(f"Wrong. It was: {correct_text}")

        self.update_status_labels()
        self.next_btn.setText("See results" if self.lives == 0 else "Next flag")
        self.next_btn.setVisible(True)

    def next_question(self):
        if self.lives == 0:
            self.finish_round()
        elif not self.show_question():
            self.finish_round()  # flag failed to load: end the round and keep the score

    def quit_round(self):
        self.go_to_setup()  # nothing is saved if you quit early

    def finish_round(self):
        previous = db.get_best_score(self.user_id, GAME_NAME)  # read before saving this one
        db.save_score(self.user_id, GAME_NAME, self.score, self.shown)

        self.result_title.setText(f"{self.score} flags")
        if previous is None:
            note = "First score saved!"
        elif self.score > previous:
            note = f"New personal best! (previous best: {previous})"
        else:
            note = f"Your best is {previous}"
        self.result_note.setText(note)
        self.stack.setCurrentIndex(2)