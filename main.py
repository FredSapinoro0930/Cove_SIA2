import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFontDatabase
import db
from app_window import AppWindow
from style import STYLESHEET
from resources import asset_path
from widgets import make_logo


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cove - Login")
        self.setFixedSize(380, 500)

        logo = make_logo(220, font_size=34)

        welcome = QLabel("Welcome back")
        welcome.setObjectName("title")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline = QLabel("Log in to your music, movies and games")
        tagline.setObjectName("subtitle")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_btn = QPushButton("Login")
        login_btn.setObjectName("primary")  # style.py gives it the teal look
        register_btn = QPushButton("Create account")

        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        login_btn.clicked.connect(self.handle_login)
        register_btn.clicked.connect(self.handle_register)
        self.password_input.returnPressed.connect(self.handle_login)

        for w in (self.username_input, self.password_input, login_btn, register_btn):
            w.setMinimumHeight(44)

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
        layout.addWidget(register_btn)
        layout.addWidget(self.message)
        layout.addStretch()
        self.setLayout(layout)

    def show_message(self, text, ok=False):
        color = "#4ade80" if ok else "#f87171"  # light green/red so they're readable on dark
        self.message.setStyleSheet(f"color: {color};")
        self.message.setText(text)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        user_id = db.login_user(username, password)
        if user_id is None:
            self.show_message("Wrong username or password")
            return

        # on_logout tells the app window which function to call when Logout is clicked
        self.main_window = AppWindow(user_id, username, on_logout=self.return_to_login)
        self.main_window.show()
        self.close()

    def return_to_login(self):
        """Called by the app window when the user logs out."""
        self.username_input.clear()
        self.password_input.clear()
        self.show_message("Logged out", ok=True)
        self.show()

    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        ok, msg = db.register_user(username, password)
        self.show_message(msg, ok)

def load_fonts():
    folder = asset_path("fonts")
    if not os.path.isdir(folder):
        return
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
    load_fonts()
    print([f for f in QFontDatabase.families() if "Inter" in f or "Outfit" in f])
    app.setStyleSheet(STYLESHEET)
    app.setWindowIcon(QIcon(asset_path("cove_icon.png")))  # applies to every window
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())