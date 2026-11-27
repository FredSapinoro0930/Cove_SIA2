"""The right side of the Music page: Favorites and playlists (both services mixed)."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QComboBox,
    QInputDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal, QPoint
import db
import music_sources
from widgets import make_track_item, section_label

FAVORITES = 0  # combo value for Favorites (real playlist ids start at 1)


class LibraryPanel(QWidget):
    play_requested = Signal(object, int)
    message = Signal(str)

    def __init__(self, runner, user_id):
        super().__init__()
        self.runner = runner
        self.user_id = user_id
        self.cache = {}  # (source, id) -> track details, kept only while the app is open
        self.loaded = False

        self.view_box = QComboBox()
        self.view_box.setAccessibleName("Favorites or playlist")
        self.view_box.setMinimumHeight(42)
        new_btn = QPushButton("New playlist")
        new_btn.setMinimumHeight(42)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setMinimumHeight(42)
        top = QHBoxLayout()
        top.addWidget(self.view_box, 1)
        top.addWidget(new_btn)
        top.addWidget(self.delete_btn)

        self.track_list = QListWidget()
        remove_btn = QPushButton("Remove song")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(section_label("MY LIBRARY"))
        layout.addLayout(top)
        layout.addWidget(self.track_list, 1)
        layout.addWidget(remove_btn)
        self.setLayout(layout)

        new_btn.clicked.connect(lambda: self.new_playlist())
        self.delete_btn.clicked.connect(self.delete_playlist)
        remove_btn.clicked.connect(self.remove_selected)
        self.track_list.itemDoubleClicked.connect(
            lambda item: self.play_requested.emit(self.tracks(), self.track_list.row(item)))

        self.reload_views(FAVORITES)
        self.view_box.currentIndexChanged.connect(lambda _: self.refresh())

    def showEvent(self, event):
        super().showEvent(event)
        if not self.loaded:
            self.loaded = True
            self.refresh()

    def tracks(self):
        return [self.track_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.track_list.count())]

    def current_view(self):
        value = self.view_box.currentData()
        return FAVORITES if value is None else value

    def reload_views(self, select):
        self.view_box.blockSignals(True)
        self.view_box.clear()
        self.view_box.addItem("Favorites", FAVORITES)
        for playlist_id, name in db.get_playlists(self.user_id):
            self.view_box.addItem(name, playlist_id)
        self.view_box.setCurrentIndex(max(self.view_box.findData(select), 0))
        self.view_box.blockSignals(False)

    # ---------- showing songs ----------
    def refs(self):
        view = self.current_view()
        if view == FAVORITES:
            return db.get_favorites(self.user_id)
        return db.get_playlist_tracks(self.user_id, view)

    def refresh(self):
        self.delete_btn.setEnabled(self.current_view() != FAVORITES)
        refs = self.refs()
        self._fill(refs, loading=True)
        if all(tuple(ref) in self.cache for ref in refs):
            self.runner.cancel("library")
            return

        # the database only holds source + track ID, so ask each service for the details
        cache = dict(self.cache)

        def done(found, error):
            if found:
                self.cache.update(found)
            self._fill(self.refs(), loading=False)
            if error:
                self.message.emit(error)

        self.runner.run("library", lambda: music_sources.lookup(refs, cache), done)

    def _fill(self, refs, loading):
        row = self.track_list.currentRow()
        self.track_list.clear()
        for source, track_id in refs:
            track = self.cache.get((source, track_id))
            if track is None:
                # a placeholder can still be played (retried) or removed
                title = "Loading..." if loading else "Unavailable right now"
                track = {"source": source, "id": track_id, "title": title,
                         "artist": "", "duration": 0, "stream_url": ""}
            item = make_track_item(track)
            # saved songs always get a new stream link before playing
            item.setData(Qt.ItemDataRole.UserRole, {**track, "stream_url": ""})
            self.track_list.addItem(item)
        if 0 <= row < self.track_list.count():
            self.track_list.setCurrentRow(row)

    # ---------- changing the library ----------
    def add_favorite(self, track):
        self.cache[(track["source"], track["id"])] = track
        if db.add_favorite(self.user_id, track["source"], track["id"]):
            self.message.emit(f"Added to favorites: {track['title']}")
            if self.current_view() == FAVORITES:
                self.refresh()
        else:
            self.message.emit("That song is already in your favorites")

    def choose_playlist(self, track, button):
        """Opens a menu under `button` listing the playlists."""
        menu = QMenu(self)
        actions = {}
        for playlist_id, name in db.get_playlists(self.user_id):
            action = menu.addAction(name.replace("&", "&&"))  # show & as typed
            actions[action] = (playlist_id, name)
        if actions:
            menu.addSeparator()
        create = menu.addAction("New playlist...")
        chosen = menu.exec(button.mapToGlobal(QPoint(0, button.height())))
        if chosen is None:
            return
        if chosen == create:
            created = self.new_playlist()
            if created is None:
                return
            playlist_id, name = created
        else:
            playlist_id, name = actions[chosen]

        self.cache[(track["source"], track["id"])] = track
        if db.add_to_playlist(self.user_id, playlist_id, track["source"], track["id"]):
            self.message.emit(f"Added to {name}: {track['title']}")
            if self.current_view() == playlist_id:
                self.refresh()
        else:
            self.message.emit(f"That song is already in {name}")

    def new_playlist(self):
        """Asks for a name. Returns (id, name), or None."""
        name, ok = QInputDialog.getText(self, "New playlist", "Playlist name:")
        name = name.strip()
        if not ok or not name:
            return None
        playlist_id = db.create_playlist(self.user_id, name)
        if playlist_id is None:
            self.message.emit("You already have a playlist with that name")
            return None
        self.reload_views(playlist_id)
        self.refresh()
        return playlist_id, name

    def delete_playlist(self):
        view = self.current_view()
        if view == FAVORITES:
            return
        answer = QMessageBox.question(
            self, "Delete playlist", f'Delete the playlist "{self.view_box.currentText()}"?')
        if answer != QMessageBox.StandardButton.Yes:
            return
        db.delete_playlist(self.user_id, view)
        self.reload_views(FAVORITES)
        self.refresh()
        self.message.emit("Playlist deleted")

    def remove_selected(self):
        item = self.track_list.currentItem()
        if item is None:
            self.message.emit("Select a song from your library first")
            return
        track = item.data(Qt.ItemDataRole.UserRole)
        view = self.current_view()
        if view == FAVORITES:
            db.remove_favorite(self.user_id, track["source"], track["id"])
        else:
            db.remove_from_playlist(self.user_id, view, track["source"], track["id"])
        self.refresh()
        self.message.emit("Removed")
