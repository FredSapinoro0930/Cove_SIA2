import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFontDatabase
import db
from app_window import AppWindow
from style import STYLESHEET
from resources import asset_path
from widgets import make_logo, keyboard_focus_only


MIN_USERNAME = 3
MIN_PASSWORD = 8
LOGIN_SIZE = (380, 500)
REGISTER_SIZE = (380, 590)


class LoginWindow(QWidget):
    """One window with two views: Login and Create account. They swap in place."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cove - Login")

        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_login_view())      # index 0
        self.stack.addWidget(self.build_register_view())   # index 1

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)

        keyboard_focus_only(self)
        self.show_login()

    # ---------- small helpers ----------
    @staticmethod
    def make_input(placeholder, password=False):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setAccessibleName(placeholder)  # screen readers need a name, not just a placeholder
        field.setMinimumHeight(44)
        if password:
            field.setEchoMode(QLineEdit.EchoMode.Password)
        return field

    @staticmethod
    def make_button(text, primary=False):
        btn = QPushButton(text)
        btn.setMinimumHeight(44)
        if primary:
            btn.setObjectName("primary")  # style.py gives it the coral look
        return btn

    @staticmethod
    def make_header(title_text, tagline_text):
        logo = make_logo(220, font_size=34)
        title = QLabel(title_text)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline = QLabel(tagline_text)
        tagline.setObjectName("subtitle")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setWordWrap(True)
        return logo, title, tagline

    @staticmethod
    def show_message(label, text, ok=False):
        color = "#4ade80" if ok else "#f87171"  # light green/red so they're readable on dark
        label.setStyleSheet(f"color: {color};")
        label.setText(text)

    # ---------- login view ----------
    def build_login_view(self):
        logo, welcome, tagline = self.make_header(
            "Welcome back", "Log in to your music, movies and games")

        self.username_input = self.make_input("Username")
        self.password_input = self.make_input("Password", password=True)
        login_btn = self.make_button("Login", primary=True)
        to_register_btn = self.make_button("Create account")

        self.login_message = QLabel("")
        self.login_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_message.setWordWrap(True)

        login_btn.clicked.connect(self.handle_login)
        to_register_btn.clicked.connect(self.show_register)
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 36, 40, 28)
        layout.setSpacing(10)
        layout.addWidget(logo)
        layout.addSpacing(12)
        layout.addWidget(welcome)
        layout.addWidget(tagline)
        layout.addSpacing(16)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addSpacing(4)
        layout.addWidget(login_btn)
        layout.addWidget(to_register_btn)
        layout.addWidget(self.login_message)
        layout.addStretch()
        view = QWidget()
        view.setLayout(layout)
        return view

    # ---------- create account view ----------
    def build_register_view(self):
        logo, title, tagline = self.make_header(
            "Create your account", "Save your playlist and game scores")

        self.new_username_input = self.make_input("Choose a username")
        self.new_password_input = self.make_input(
            f"Password (at least {MIN_PASSWORD} characters)", password=True)
        self.confirm_input = self.make_input("Confirm password", password=True)
        create_btn = self.make_button("Create account", primary=True)
        back_btn = self.make_button("Back to login")

        self.register_message = QLabel("")
        self.register_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.register_message.setWordWrap(True)

        create_btn.clicked.connect(self.handle_register)
        back_btn.clicked.connect(self.show_login)
        self.new_username_input.returnPressed.connect(self.new_password_input.setFocus)
        self.new_password_input.returnPressed.connect(self.confirm_input.setFocus)
        self.confirm_input.returnPressed.connect(self.handle_register)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 36, 40, 28)
        layout.setSpacing(10)
        layout.addWidget(logo)
        layout.addSpacing(12)
        layout.addWidget(title)
        layout.addWidget(tagline)
        layout.addSpacing(16)
        layout.addWidget(self.new_username_input)
        layout.addWidget(self.new_password_input)
        layout.addWidget(self.confirm_input)
        layout.addSpacing(4)
        layout.addWidget(create_btn)
        layout.addWidget(back_btn)
        layout.addWidget(self.register_message)
        layout.addStretch()
        view = QWidget()
        view.setLayout(layout)
        return view

    # ---------- switching views ----------
    def show_login(self):
        self.setWindowTitle("Cove - Login")
        self.setFixedSize(*LOGIN_SIZE)
        self.stack.setCurrentIndex(0)
        for field in (self.new_username_input, self.new_password_input, self.confirm_input):
            field.clear()
        self.register_message.clear()
        self.password_input.clear()
        if self.username_input.text():
            self.password_input.setFocus()
        else:
            self.username_input.setFocus()

    def show_register(self):
        self.setWindowTitle("Cove - Create account")
        self.setFixedSize(*REGISTER_SIZE)
        self.stack.setCurrentIndex(1)
        self.login_message.clear()
        self.new_username_input.clear()
        self.new_password_input.clear()
        self.confirm_input.clear()
        self.register_message.clear()
        self.new_username_input.setFocus()

    # ---------- actions ----------
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        user_id = db.login_user(username, password)
        if user_id is None:
            self.show_message(self.login_message, "Wrong username or password")
            return

        # on_logout tells the app window which function to call when Logout is clicked
        self.main_window = AppWindow(user_id, username, on_logout=self.return_to_login)
        self.main_window.show()
        self.close()

    def return_to_login(self):
        """Called by the app window when the user logs out."""
        self.username_input.clear()
        self.show_login()
        self.show_message(self.login_message, "Logged out", ok=True)
        self.show()

    def handle_register(self):
        username = self.new_username_input.text().strip()
        password = self.new_password_input.text()
        confirm = self.confirm_input.text()

        if len(username) < MIN_USERNAME:
            self.show_message(self.register_message,
                              f"Username must be at least {MIN_USERNAME} characters")
            return
        if len(password) < MIN_PASSWORD:
            self.show_message(self.register_message,
                              f"Password must be at least {MIN_PASSWORD} characters")
            return
        if password != confirm:
            self.show_message(self.register_message, "Passwords do not match")
            return

        ok, msg = db.register_user(username, password)
        if not ok:
            self.show_message(self.register_message, msg)
            return

        # success: go back to the login view with the username already filled in
        self.username_input.setText(username)
        self.show_login()
        self.show_message(self.login_message, "Account created. Enter your password to log in.", ok=True)


def load_fonts():
    """Load every .ttf/.otf in assets/fonts so the stylesheet can use Inter and Outfit."""
    folder = asset_path("fonts")
    if not os.path.isdir(folder):
        return  # no fonts folder: the app falls back to the system fonts
    for name in os.listdir(folder):
        if name.lower().endswith((".ttf", ".otf")):
            QFontDatabase.addApplicationFont(os.path.join(folder, name))


if __name__ == "__main__":
    # makes Windows show our icon in the taskbar instead of the Python icon
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("cove.app")

    db.init_db()
    app = QApplication(sys.argv)
    load_fonts()  # must run before the stylesheet is applied
    # print([f for f in QFontDatabase.families() if "Inter" in f or "Outfit" in f])  # uncomment to check names
    app.setStyleSheet(STYLESHEET)
    app.setWindowIcon(QIcon(asset_path("cove_icon.png")))  # applies to every window
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())