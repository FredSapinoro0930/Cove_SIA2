from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QStackedWidget, QListWidget, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer
import db
import trivia
from style import CORRECT_STYLE, WRONG_STYLE, GOOD_TEXT, BAD_TEXT

GAME_NAME = "trivia"
QUESTIONS_PER_ROUND = 10


class TriviaGame(QWidget):
    def __init__(self, user_id, username, on_back):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.on_back = on_back  # function from games_page.py that returns to the games menu
        self.categories_loaded = False
        self.questions = []
        self.index = 0
        self.score = 0
        self.answered = False

        # three screens inside this widget: setup, quiz, result
        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_setup_view())   # 0
        self.stack.addWidget(self.build_quiz_view())    # 1
        self.stack.addWidget(self.build_result_view())  # 2

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    # ---------- building the screens ----------
    def build_setup_view(self):
        view = QWidget()

        title = QLabel("Trivia Quiz")
        title.setObjectName("title")
        subtitle = QLabel("10 multiple-choice questions. Your score is saved to the leaderboard.")
        subtitle.setObjectName("subtitle")

        self.category_box = QComboBox()
        self.category_box.addItem("Any category", None)
        self.difficulty_box = QComboBox()
        self.difficulty_box.addItem("Any difficulty", None)
        self.difficulty_box.addItem("Easy", "easy")
        self.difficulty_box.addItem("Medium", "medium")
        self.difficulty_box.addItem("Hard", "hard")

        start_btn = QPushButton("Start quiz")
        start_btn.setObjectName("primary")
        start_btn.setMinimumHeight(46)
        back_btn = QPushButton("Back to games")
        back_btn.setObjectName("ghost")
        for box in (self.category_box, self.difficulty_box):
            box.setMinimumHeight(42)

        self.best_label = QLabel("")
        self.leaderboard = QListWidget()
        self.leaderboard.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.leaderboard.setMaximumHeight(170)

        self.setup_status = QLabel("")
        credit = QLabel("Questions from Open Trivia DB (opentdb.com), CC BY-SA 4.0")
        credit.setObjectName("credit")
        self.setup_status.setObjectName("status")
        self.best_label.setObjectName("stat")

        start_btn.clicked.connect(self.start_round)
        back_btn.clicked.connect(self.back_to_games)

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.section_label("CATEGORY"))
        layout.addWidget(self.category_box)
        layout.addWidget(self.section_label("DIFFICULTY"))
        layout.addWidget(self.difficulty_box)
        layout.addSpacing(8)
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

    def build_quiz_view(self):
        view = QWidget()

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("sectionLabel")
        self.score_label = QLabel("")
        self.score_label.setObjectName("stat")
        top = QHBoxLayout()
        top.addWidget(self.progress_label)
        top.addStretch()
        top.addWidget(self.score_label)

        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        self.question_label.setObjectName("question")

        self.answer_buttons = []
        answers_layout = QVBoxLayout()
        answers_layout.setSpacing(10)
        for i in range(4):
            btn = QPushButton("")
            btn.setObjectName("answer")
            btn.setMinimumHeight(52)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=i: self.on_answer(i))
            self.answer_buttons.append(btn)
            answers_layout.addWidget(btn)

        self.feedback_label = QLabel("")
        self.feedback_label.setWordWrap(True)

        self.next_btn = QPushButton("Next question")
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
        layout.addSpacing(16)
        layout.addWidget(self.question_label)
        layout.addSpacing(16)
        layout.addLayout(answers_layout)
        layout.addWidget(self.feedback_label)
        layout.addStretch()
        layout.addLayout(bottom)
        view.setLayout(layout)
        return view

    def build_result_view(self):
        view = QWidget()

        heading = QLabel("Round complete")
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
    @staticmethod
    def section_label(text):
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def showEvent(self, event):
        super().showEvent(event)
        if self.stack.currentIndex() == 0:
            self.refresh_scores()
            if not self.categories_loaded:
                QTimer.singleShot(0, self.load_categories)  # run just after the page appears

    def load_categories(self):
        self.setup_status.setText("Loading categories...")
        QApplication.processEvents()
        try:
            categories = trivia.get_categories()
        except Exception as e:
            self.setup_status.setText(str(e))
            return
        for c in categories:
            self.category_box.addItem(c["name"], c["id"])
        self.categories_loaded = True
        self.setup_status.setText("")

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
        self.go_to_setup()  # reset first, so the quiz opens on the setup screen next time
        self.on_back()

    # ---------- playing a round ----------
    def start_round(self):
        category = self.category_box.currentData()
        difficulty = self.difficulty_box.currentData()
        self.setup_status.setText("Loading questions...")
        QApplication.processEvents()  # lets the label update before the request runs
        try:
            questions = trivia.get_questions(QUESTIONS_PER_ROUND, category, difficulty)
        except Exception as e:
            self.setup_status.setText(str(e))
            return
        if not questions:
            self.setup_status.setText(
                "No questions found for that choice. Try another category or difficulty."
            )
            return

        self.setup_status.setText("")
        self.questions = questions
        self.index = 0
        self.score = 0
        self.stack.setCurrentIndex(1)
        self.show_question()

    def show_question(self):
        q = self.questions[self.index]
        self.progress_label.setText(f"Question {self.index + 1} of {len(self.questions)}")
        self.score_label.setText(f"Score: {self.score}")
        self.question_label.setText(q["question"])

        self.answered = False
        for i, btn in enumerate(self.answer_buttons):
            if i < len(q["answers"]):
                btn.setText(q["answers"][i])
                btn.setStyleSheet("")  # clear the green/red from the last question
                btn.setVisible(True)
            else:
                btn.setVisible(False)

        self.feedback_label.setText("")
        self.next_btn.setVisible(False)

    def on_answer(self, i):
        if self.answered:
            return  # ignore extra clicks after answering
        self.answered = True

        q = self.questions[self.index]
        chosen = self.answer_buttons[i]
        correct_text = q["correct"]

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
            self.feedback_label.setStyleSheet(BAD_TEXT)
            self.feedback_label.setText(f"Wrong. The answer was: {correct_text}")

        self.score_label.setText(f"Score: {self.score}")
        is_last = self.index == len(self.questions) - 1
        self.next_btn.setText("See results" if is_last else "Next question")
        self.next_btn.setVisible(True)

    def next_question(self):
        self.index += 1
        if self.index >= len(self.questions):
            self.finish_round()
        else:
            self.show_question()

    def quit_round(self):
        self.go_to_setup()  # nothing is saved if you quit early

    def finish_round(self):
        total = len(self.questions)
        previous = db.get_best_score(self.user_id, GAME_NAME)  # read before saving this one
        db.save_score(self.user_id, GAME_NAME, self.score, total)

        self.result_title.setText(f"{self.score} / {total}")
        if previous is None:
            note = "First score saved!"
        elif self.score > previous:
            note = f"New personal best! (previous best: {previous})"
        else:
            note = f"Your best is {previous}"
        self.result_note.setText(note)
        self.stack.setCurrentIndex(2)