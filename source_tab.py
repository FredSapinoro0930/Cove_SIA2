"""One tab of the Music page: search one service and list what it returns."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget
)
from PySide6.QtCore import Qt, Signal
from widgets import make_track_item, section_label


class SourceTab(QWidget):
    play_requested = Signal(object, int)       # (list of tracks, row to play)
    favorite_requested = Signal(object)        # track
    playlist_requested = Signal(object, object)  # (track, button to open the menu under)
    message = Signal(str)

    def __init__(self, runner, service, key, description, popular=None):
        super().__init__()
        self.runner = runner
        self.service = service
        self.key = key          # keeps this tab's searches separate from the other tab's
        self.popular = popular  # function returning the chart, or None
        self.loaded = False

        note = QLabel(description)
        note.setObjectName("muted")
        note.setWordWrap(True)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs or artists...")
        self.search_input.setAccessibleName("Search songs or artists")
        self.search_input.setMinimumHeight(42)
        search_btn = QPushButton("Search")
        search_btn.setObjectName("primary")
        search_btn.setMinimumHeight(42)
        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(search_btn)
        if popular:
            popular_btn = QPushButton("Popular")
            popular_btn.setMinimumHeight(42)
            popular_btn.clicked.connect(self.show_popular)
            search_row.addWidget(popular_btn)

        self.heading = section_label("SEARCH RESULTS  ·  DOUBLE-CLICK TO PLAY")
        self.results_list = QListWidget()

        favorite_btn = QPushButton("Add to favorites")
        self.playlist_btn = QPushButton("Add to playlist")
        buttons = QHBoxLayout()
        buttons.addWidget(favorite_btn)
        buttons.addWidget(self.playlist_btn)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(note)
        layout.addLayout(search_row)
        layout.addWidget(self.heading)
        layout.addWidget(self.results_list, 1)
        layout.addLayout(buttons)
        self.setLayout(layout)

        search_btn.clicked.connect(self.do_search)
        self.search_input.returnPressed.connect(self.do_search)
        self.results_list.itemDoubleClicked.connect(
            lambda item: self.play_requested.emit(self.tracks(), self.results_list.row(item)))
        favorite_btn.clicked.connect(self._favorite)
        self.playlist_btn.clicked.connect(self._add_to_playlist)

    def showEvent(self, event):
        super().showEvent(event)
        if self.popular and not self.loaded:  # first visit: show the chart
            self.show_popular()

    def tracks(self):
        return [self.results_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.results_list.count())]

    def selected_track(self):
        item = self.results_list.currentItem()
        if item is None:
            self.message.emit("Select a song from the results first")
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _favorite(self):
        track = self.selected_track()
        if track:
            self.favorite_requested.emit(track)

    def _add_to_playlist(self):
        track = self.selected_track()
        if track:
            self.playlist_requested.emit(track, self.playlist_btn)

    def show_popular(self):
        self.loaded = True
        self._load(self.popular, "POPULAR RIGHT NOW  ·  DOUBLE-CLICK TO PLAY")

    def do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.loaded = True
        self._load(lambda: self.service.search_tracks(query),
                   "SEARCH RESULTS  ·  DOUBLE-CLICK TO PLAY")

    def _load(self, work, heading):
        self.message.emit("Loading...")

        def done(tracks, error):
            if error:
                self.loaded = False  # lets the chart try again on the next visit
                self.message.emit(error)
                return
            self.heading.setText(heading)
            self.results_list.clear()
            for track in tracks:
                self.results_list.addItem(make_track_item(track))
            self.message.emit(f"{len(tracks)} songs" if tracks else "No results found")

        self.runner.run(self.key, work, done)
