"""Movies & TV, "Watchlist" tab."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal
import db


class WatchlistTab(QWidget):
    open_requested = Signal(object)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.items = QListWidget()
        open_btn = QPushButton("Open")
        open_btn.setObjectName("primary")
        remove_btn = QPushButton("Remove from watchlist")
        buttons = QHBoxLayout()
        buttons.addWidget(open_btn)
        buttons.addWidget(remove_btn)
        buttons.addStretch()
        self.status = QLabel("")
        self.status.setObjectName("status")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.items, 1)
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        self.setLayout(layout)

        open_btn.clicked.connect(self.open_selected)
        remove_btn.clicked.connect(self.remove_selected)
        self.items.itemDoubleClicked.connect(lambda _: self.open_selected())
        self.refresh()

    def refresh(self):
        self.items.clear()
        for entry in db.get_watchlist(self.user_id):
            if entry["source"] != "archive":
                continue  # only Internet Archive titles can be opened
            title = f"{entry['title']} ({entry['year']})" if entry["year"] else entry["title"]
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.items.addItem(item)
        self.status.setText("" if self.items.count() else
                            "Your watchlist is empty. Add titles from the Watch free tab.")

    def _selected(self):
        item = self.items.currentItem()
        if item is None:
            self.status.setText("Select a title first")
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def open_selected(self):
        entry = self._selected()
        if entry:
            self.open_requested.emit(entry)

    def remove_selected(self):
        entry = self._selected()
        if entry:
            db.remove_from_watchlist(self.user_id, entry["source"], entry["media_type"],
                                     entry["id"])
            self.refresh()
