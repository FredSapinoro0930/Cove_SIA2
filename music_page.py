import random
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QComboBox, QInputDialog, QMessageBox, QMenu, QTabWidget
)
from PySide6.QtCore import Qt, QUrl, QTimer, Signal, QPoint
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import db
import deezer
import jamendo
from widgets import (
    BackgroundRunner, ClickableSlider, format_time, make_track_item, section_label
)

SOURCES = {"jamendo": jamendo, "deezer": deezer}


def get_fresh_track(source, track_id):
    """The track with a new stream link, or None if it can't be fetched."""
    service = SOURCES.get(source)
    return service.get_track(track_id) if service else None


def lookup(refs, cache):
    """Turn saved (source, track_id) pairs into track details. Run on a background thread.

    `cache` is {(source, id): track}. Returns only the newly fetched entries.
    """
    found = {}
    for name, service in SOURCES.items():
        missing = [tid for src, tid in refs if src == name and (src, tid) not in cache]
        if missing:
            for tid, track in service.get_tracks(missing).items():
                found[(name, tid)] = track
    return found


class SourceTab(QWidget):
    play_requested = Signal(object, int)       # (list of tracks, row to play)
    favorite_requested = Signal(object)        # track
    playlist_requested = Signal(object, object)  # (track, button to open the menu under)
    message = Signal(str)

    def __init__(self, runner, service, key, description,
                 default, default_heading, default_button=None):
        super().__init__()
        self.runner = runner
        self.service = service
        self.key = key          # keeps this tab's searches separate from the other tab's
        self.default = default  # function returning the songs shown without a search
        self.default_heading = default_heading
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
        if default_button:
            button = QPushButton(default_button)
            button.setMinimumHeight(42)
            button.clicked.connect(self.show_default)
            search_row.addWidget(button)

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
        if not self.loaded:  # first visit: show songs before any search
            self.show_default()

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

    def show_default(self):
        self.loaded = True
        self._load(self.default, self.default_heading)

    def do_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.show_default()  # empty search box
            return
        self.loaded = True
        self._load(lambda: self.service.search_tracks(query),
                   "SEARCH RESULTS  ·  DOUBLE-CLICK TO PLAY")

    def _load(self, work, heading):
        self.message.emit("Loading...")

        def done(tracks, error):
            if error:
                self.loaded = False  # try again on the next visit
                self.message.emit(error)
                return
            self.heading.setText(heading)
            self.results_list.clear()
            for track in tracks:
                self.results_list.addItem(make_track_item(track))
            self.message.emit(f"{len(tracks)} songs" if tracks else "No results found")

        self.runner.run(self.key, work, done)


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

        self.runner.run("library", lambda: lookup(refs, cache), done)

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


class MusicPage(QWidget):
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.queue = []       # the songs that were listed when playback started
        self.queue_index = -1
        self.runner = BackgroundRunner(self)

        # ----- audio engine -----
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)

        # ----- page header -----
        title = QLabel("Music")
        title.setObjectName("title")
        subtitle = QLabel("Full free songs from Jamendo, popular hits as previews from Deezer")
        subtitle.setObjectName("subtitle")

        # ----- left: one tab per service -----
        self.jamendo_tab = SourceTab(
            self.runner, jamendo, "jamendo",
            "Full-length free tracks. Search with an empty box for a new random mix.",
            default=jamendo.random_tracks,
            default_heading="RANDOM PICKS  ·  DOUBLE-CLICK TO PLAY")
        self.deezer_tab = SourceTab(
            self.runner, deezer, "deezer",
            "Popular charts and search. Deezer provides 30-second previews only.",
            default=deezer.chart_tracks,
            default_heading="POPULAR RIGHT NOW  ·  DOUBLE-CLICK TO PLAY",
            default_button="Popular")
        self.tabs = QTabWidget()
        self.tabs.addTab(self.jamendo_tab, "Jamendo")
        self.tabs.addTab(self.deezer_tab, "Deezer")

        # ----- right: favorites and playlists -----
        self.library = LibraryPanel(self.runner, user_id)

        lists_row = QHBoxLayout()
        lists_row.setSpacing(20)
        lists_row.addWidget(self.tabs, 1)
        lists_row.addWidget(self.library, 1)

        # ----- now playing -----
        self.now_playing = QLabel("Nothing playing")
        self.now_playing.setObjectName("nowPlaying")

        # ----- seek bar -----
        self.current_time = QLabel("0:00")
        self.total_time = QLabel("0:00")
        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        seek_row = QHBoxLayout()
        seek_row.addWidget(self.current_time)
        seek_row.addWidget(self.seek_slider)
        seek_row.addWidget(self.total_time)

        # ----- controls -----
        prev_btn = QPushButton("Prev")
        self.play_btn = QPushButton("Play")
        self.play_btn.setObjectName("primary")  # coral pill
        self.play_btn.setMinimumWidth(92)
        next_btn = QPushButton("Next")
        stop_btn = QPushButton("Stop")
        self.shuffle_btn = QPushButton("Shuffle")
        self.shuffle_btn.setCheckable(True)  # stays pressed when ON
        self.repeat_btn = QPushButton("Repeat")
        self.repeat_btn.setCheckable(True)
        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(120)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        controls_row.addWidget(prev_btn)
        controls_row.addWidget(self.play_btn)
        controls_row.addWidget(next_btn)
        controls_row.addWidget(stop_btn)
        controls_row.addWidget(self.shuffle_btn)
        controls_row.addWidget(self.repeat_btn)
        controls_row.addStretch()
        controls_row.addWidget(QLabel("Volume"))
        controls_row.addWidget(self.volume_slider)

        # ----- status line -----
        self.status = QLabel("Ready")
        self.status.setObjectName("status")

        # ----- player bar: a rounded panel holding now playing, seek bar and controls -----
        player_bar = QFrame()
        player_bar.setObjectName("playerBar")
        bar_layout = QVBoxLayout()
        bar_layout.setContentsMargins(20, 14, 20, 14)
        bar_layout.setSpacing(8)
        bar_layout.addWidget(self.now_playing)
        bar_layout.addLayout(seek_row)
        bar_layout.addLayout(controls_row)
        player_bar.setLayout(bar_layout)

        # ----- put everything together -----
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(lists_row, 1)
        layout.addWidget(player_bar)
        layout.addWidget(self.status)
        self.setLayout(layout)

        # ----- connect signals to functions -----
        for tab in (self.jamendo_tab, self.deezer_tab):
            tab.play_requested.connect(self.play_from)
            tab.favorite_requested.connect(self.library.add_favorite)
            tab.playlist_requested.connect(self.library.choose_playlist)
            tab.message.connect(self.status.setText)
        self.library.play_requested.connect(self.play_from)
        self.library.message.connect(self.status.setText)
        prev_btn.clicked.connect(self.play_previous)
        next_btn.clicked.connect(self.play_next)
        self.play_btn.clicked.connect(self.toggle_play)
        stop_btn.clicked.connect(self.stop)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.seek_slider.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status)
        self.player.errorOccurred.connect(self.on_player_error)


    # ---------- called by the main window ----------
    def stop(self):
        self._cancel_loading()  # a song still loading must not start after Stop or Log out
        self.player.stop()

    def pause(self):
        self._cancel_loading()
        self.player.pause()

    def _cancel_loading(self):
        if self.runner.cancel("play"):
            self.now_playing.setText("Nothing playing")

    # ---------- playback ----------
    def play_from(self, tracks, row):
        self.queue = list(tracks)
        self.play_index(row)

    def play_index(self, index):
        if not 0 <= index < len(self.queue):
            return
        self.queue_index = index
        track = self.queue[index]
        self.runner.cancel("play")
        self.player.stop()
        self.player.setSource(QUrl())

        # Deezer links expire, and saved songs have no link, so fetch a new one
        if track["source"] != "deezer" and track["stream_url"]:
            self._start(track)
            return

        self.now_playing.setText("Loading...")

        def done(fresh, error):
            if fresh:
                self._start(fresh)
            else:
                self.now_playing.setText("Nothing playing")
                self.status.setText(error or "That song can't be played right now. Try again.")

        self.runner.run(
            "play", lambda: get_fresh_track(track["source"], track["id"]), done)

    def _start(self, track):
        self.player.setSource(QUrl(track["stream_url"]))
        self.player.play()
        preview = "  (30s preview, Deezer)" if track["source"] == "deezer" else ""
        self.now_playing.setText(f"{track['title']} - {track['artist']}{preview}")

    def play_next(self):
        if not self.queue:
            return
        row = self.queue_index
        if self.shuffle_btn.isChecked() and len(self.queue) > 1:
            new_row = random.choice([r for r in range(len(self.queue)) if r != row])
        else:
            new_row = row + 1
            if new_row >= len(self.queue):
                if self.repeat_btn.isChecked():
                    new_row = 0  # wrap around
                else:
                    self.player.stop()  # end of the list
                    return
        self.play_index(new_row)

    def play_previous(self):
        if not self.queue:
            return
        if self.player.position() > 3000:
            self.player.setPosition(0)  # more than 3 seconds in: restart the song
            return
        new_row = self.queue_index - 1
        if new_row < 0:
            new_row = len(self.queue) - 1 if self.repeat_btn.isChecked() else 0
        self.play_index(new_row)

    def toggle_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif not self.player.source().isEmpty():
            self.player.play()
        elif self.queue:
            self.play_index(self.queue_index)
        else:
            for lst in (self.tabs.currentWidget().results_list, self.library.track_list):
                if lst.currentRow() >= 0:
                    tracks = [lst.item(i).data(Qt.ItemDataRole.UserRole)
                              for i in range(lst.count())]
                    self.play_from(tracks, lst.currentRow())
                    break

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100)

    # ---------- keeping the UI in sync ----------
    def on_position_changed(self, position):
        if not self.seek_slider.isSliderDown():  # don't fight the user's dragging
            self.seek_slider.setValue(position)
        self.current_time.setText(format_time(position))

    def on_duration_changed(self, duration):
        self.seek_slider.setRange(0, duration)
        self.total_time.setText(format_time(duration))

    def on_state_changed(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_btn.setText("Pause" if playing else "Play")

    def on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            QTimer.singleShot(0, self.play_next)  # song finished: auto-advance

    def on_player_error(self, error, message):
        self.status.setText(f"Playback error: {message}")