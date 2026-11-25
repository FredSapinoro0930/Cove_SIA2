import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import jamendo
import db
from widgets import ClickableSlider, format_time


class MusicPage(QWidget):
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.queue_list = None  # the list the current song was played from

        # ----- audio engine -----
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)

        # ----- search row -----
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs or artists...")
        self.search_input.setMinimumHeight(42)
        search_btn = QPushButton("Search")
        search_btn.setObjectName("primary")
        search_btn.setMinimumHeight(42)
        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(search_btn)

        # ----- page header -----
        title = QLabel("Music")
        title.setObjectName("title")
        subtitle = QLabel("Search free music from Jamendo and build your own playlist")
        subtitle.setObjectName("subtitle")

        # ----- left: search results -----
        self.results_list = QListWidget()
        add_btn = QPushButton("Add to playlist")
        left = QVBoxLayout()
        left.addWidget(self.section_label("SEARCH RESULTS"))
        left.addWidget(self.results_list)
        left.addWidget(add_btn)

        # ----- right: my playlist -----
        self.playlist_list = QListWidget()
        remove_btn = QPushButton("Remove from playlist")
        right = QVBoxLayout()
        right.addWidget(self.section_label("MY PLAYLIST"))
        right.addWidget(self.playlist_list)
        right.addWidget(remove_btn)

        lists_row = QHBoxLayout()
        lists_row.setSpacing(20)
        lists_row.addLayout(left)
        lists_row.addLayout(right)

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
        layout.addSpacing(6)
        layout.addLayout(search_row)
        layout.addLayout(lists_row, 1)
        layout.addWidget(player_bar)
        layout.addWidget(self.status)
        self.setLayout(layout)

        # ----- connect signals to functions -----
        search_btn.clicked.connect(self.do_search)
        self.search_input.returnPressed.connect(self.do_search)
        add_btn.clicked.connect(self.add_to_playlist)
        remove_btn.clicked.connect(self.remove_from_playlist)
        self.results_list.itemDoubleClicked.connect(
            lambda item: self.play_row(self.results_list, self.results_list.row(item))
        )
        self.playlist_list.itemDoubleClicked.connect(
            lambda item: self.play_row(self.playlist_list, self.playlist_list.row(item))
        )
        prev_btn.clicked.connect(self.play_previous)
        next_btn.clicked.connect(self.play_next)
        self.play_btn.clicked.connect(self.toggle_play)
        stop_btn.clicked.connect(self.player.stop)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.seek_slider.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status)
        self.player.errorOccurred.connect(self.on_player_error)

        # load this user's saved playlist
        self.refresh_playlist()

    # ---------- called by the main window ----------
    def stop(self):
        self.player.stop()
    def pause(self):
        self.player.pause()

    # ---------- list helpers ----------
    @staticmethod
    def section_label(text):
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def make_item(self, track):
        text = f"{track['title']} - {track['artist']}  ({format_time(track['duration'] * 1000)})"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, track)  # hide the full track info in the item
        return item

    def refresh_playlist(self):
        self.playlist_list.clear()
        for track in db.get_playlist(self.user_id):
            self.playlist_list.addItem(self.make_item(track))

    # ---------- search ----------
    def do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.status.setText("Searching...")
        QApplication.processEvents()  # lets the label update before the request runs
        try:
            tracks = jamendo.search_tracks(query)
        except Exception as e:
            self.status.setText(str(e))
            return

        self.results_list.clear()
        for t in tracks:
            self.results_list.addItem(self.make_item(t))
        self.status.setText(f"{len(tracks)} results" if tracks else "No results found")

    # ---------- playlist ----------
    def add_to_playlist(self):
        item = self.results_list.currentItem()
        if item is None:
            self.status.setText("Select a song from the search results first")
            return
        track = item.data(Qt.ItemDataRole.UserRole)
        if db.add_to_playlist(self.user_id, track):
            self.refresh_playlist()
            self.status.setText(f"Added: {track['title']}")
        else:
            self.status.setText("That song is already in your playlist")

    def remove_from_playlist(self):
        item = self.playlist_list.currentItem()
        if item is None:
            self.status.setText("Select a song from your playlist first")
            return
        track = item.data(Qt.ItemDataRole.UserRole)
        db.remove_from_playlist(self.user_id, track["id"])
        self.refresh_playlist()
        self.status.setText(f"Removed: {track['title']}")

    # ---------- playback ----------
    def play_row(self, list_widget, row):
        item = list_widget.item(row)
        if item is None:
            return
        self.queue_list = list_widget
        list_widget.setCurrentRow(row)
        track = item.data(Qt.ItemDataRole.UserRole)

        url = track["stream_url"]
        if list_widget is self.playlist_list:
            # saved links may expire, so ask Jamendo for a fresh one (falls back to the saved one)
            fresh = jamendo.get_track(track["id"])
            if fresh:
                url = fresh["stream_url"]

        self.player.setSource(QUrl(url))
        self.player.play()
        self.now_playing.setText(f"{track['title']} - {track['artist']}")

    def play_next(self):
        lst = self.queue_list
        if lst is None or lst.count() == 0:
            return
        row = lst.currentRow()
        if self.shuffle_btn.isChecked() and lst.count() > 1:
            new_row = random.choice([r for r in range(lst.count()) if r != row])
        else:
            new_row = row + 1
            if new_row >= lst.count():
                if self.repeat_btn.isChecked():
                    new_row = 0  # wrap around
                else:
                    self.player.stop()  # end of the list
                    return
        self.play_row(lst, new_row)

    def play_previous(self):
        lst = self.queue_list
        if lst is None or lst.count() == 0:
            return
        if self.player.position() > 3000:
            self.player.setPosition(0)  # more than 3 seconds in: restart the song
            return
        new_row = lst.currentRow() - 1
        if new_row < 0:
            new_row = lst.count() - 1 if self.repeat_btn.isChecked() else 0
        self.play_row(lst, new_row)

    def toggle_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.source().isEmpty():
            for lst in (self.results_list, self.playlist_list):
                if lst.currentRow() >= 0:
                    self.play_row(lst, lst.currentRow())
                    break
        else:
            self.player.play()

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
            self.play_next()  # song finished: auto-advance

    def on_player_error(self, error, message):
        self.status.setText(f"Playback error: {message}")