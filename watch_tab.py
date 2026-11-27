"""Movies & TV, "Watch free" tab: Internet Archive films and shows, played in the app."""
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QComboBox
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import archive
import db
from background import BackgroundRunner
from widgets import ClickableSlider, format_time, section_label


class VideoWidget(QVideoWidget):
    """Video area: Esc leaves fullscreen, double-click toggles it."""

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def enter_fullscreen(self):
        self.setFullScreen(True)
        self.setFocus()  # so Esc goes to the video

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.setFullScreen(False)
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.isFullScreen():
            self.setFullScreen(False)
        else:
            self.enter_fullscreen()
        event.accept()


class WatchTab(QWidget):
    theater_changed = Signal(bool)
    watchlist_changed = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.runner = BackgroundRunner(self)
        self.loaded = False  # becomes True after the first automatic search

        # ----- video engine -----
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)
        self.video_widget = VideoWidget()
        self.video_widget.setStyleSheet("background-color: #000000; border-radius: 14px;")
        self.video_widget.setMinimumSize(420, 240)
        self.player.setVideoOutput(self.video_widget)

        # ----- search row -----
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies and shows (leave empty to browse)...")
        self.search_input.setMinimumHeight(42)
        self.collection_box = QComboBox()
        self.collection_box.setMinimumHeight(42)
        for label, collection in archive.COLLECTIONS.items():
            self.collection_box.addItem(label, collection)
        search_btn = QPushButton("Search")
        search_btn.setObjectName("primary")
        search_btn.setMinimumHeight(42)
        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.collection_box)
        search_row.addWidget(search_btn)

        # ----- left panel: results and episodes -----
        self.results_list = QListWidget()
        self.episodes_list = QListWidget()
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.addWidget(section_label("RESULTS  ·  DOUBLE-CLICK TO OPEN"))
        left.addWidget(self.results_list, 3)
        watchlist_btn = QPushButton("Add to watchlist")
        left.addWidget(watchlist_btn)
        left.addWidget(section_label("EPISODES / PARTS  ·  DOUBLE-CLICK TO PLAY"))
        left.addWidget(self.episodes_list, 2)
        self.left_panel = QWidget()  # hidden in theater mode
        self.left_panel.setFixedWidth(340)
        self.left_panel.setLayout(left)

        middle = QHBoxLayout()
        middle.setSpacing(20)
        middle.addWidget(self.left_panel)
        middle.addWidget(self.video_widget, 1)

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
        self.play_btn = QPushButton("Play")
        self.play_btn.setObjectName("primary")  # coral pill
        self.play_btn.setMinimumWidth(92)
        stop_btn = QPushButton("Stop")
        self.theater_btn = QPushButton("Theater")
        self.theater_btn.setToolTip("Hide the search panel and enlarge the video (T)")
        fullscreen_btn = QPushButton("Fullscreen")
        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(120)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        controls_row.addWidget(self.play_btn)
        controls_row.addWidget(stop_btn)
        controls_row.addWidget(self.theater_btn)
        controls_row.addWidget(fullscreen_btn)
        controls_row.addStretch()
        controls_row.addWidget(QLabel("Volume"))
        controls_row.addWidget(self.volume_slider)

        # ----- status line -----
        self.status = QLabel("Ready")
        self.status.setObjectName("status")

        # ----- player bar -----
        player_bar = QFrame()
        player_bar.setObjectName("playerBar")
        bar_layout = QVBoxLayout()
        bar_layout.setContentsMargins(20, 14, 20, 14)
        bar_layout.setSpacing(8)
        bar_layout.addWidget(self.now_playing)
        bar_layout.addLayout(seek_row)
        bar_layout.addLayout(controls_row)
        player_bar.setLayout(bar_layout)

        # ----- header + search live in one box so theater mode can hide them together -----
        subtitle = QLabel("Free public-domain films and classic shows from the Internet Archive")
        subtitle.setObjectName("subtitle")
        self.header_box = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        header_layout.addWidget(subtitle)
        header_layout.addLayout(search_row)
        self.header_box.setLayout(header_layout)

        # ----- put everything together -----
        self.theater = False
        self.page_layout = QVBoxLayout()
        self.page_layout.setContentsMargins(0, 12, 0, 0)
        self.page_layout.setSpacing(10)
        self.page_layout.addWidget(self.header_box)
        self.page_layout.addLayout(middle, 1)
        self.page_layout.addWidget(player_bar)
        self.page_layout.addWidget(self.status)
        self.setLayout(self.page_layout)

        # T toggles theater mode, Esc leaves it (Esc only works while theater mode is on)
        QShortcut(QKeySequence(Qt.Key.Key_T), self, activated=self.toggle_theater)
        self.exit_theater_key = QShortcut(QKeySequence(Qt.Key.Key_Escape), self,
                                          activated=lambda: self.set_theater(False))
        self.exit_theater_key.setEnabled(False)

        # ----- connect signals to functions -----
        search_btn.clicked.connect(self.do_search)
        self.search_input.returnPressed.connect(self.do_search)
        self.results_list.itemDoubleClicked.connect(self.open_item)
        self.episodes_list.itemDoubleClicked.connect(self.play_episode)
        self.play_btn.clicked.connect(self.toggle_play)
        stop_btn.clicked.connect(self.stop)
        watchlist_btn.clicked.connect(self.add_to_watchlist)
        self.theater_btn.clicked.connect(self.toggle_theater)
        fullscreen_btn.clicked.connect(self.video_widget.enter_fullscreen)  # Esc or double-click exits
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.seek_slider.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status)
        self.player.errorOccurred.connect(self.on_player_error)

    # ---------- theater mode ----------
    def toggle_theater(self):
        if not self.isVisible():
            return  # T does nothing while another tab or page is shown
        self.set_theater(not self.theater)

    def set_theater(self, on):
        """Theater mode: the video takes the whole page. The nav bar and player controls stay."""
        self.theater = on
        self.header_box.setVisible(not on)
        self.left_panel.setVisible(not on)
        self.page_layout.setContentsMargins(0, 0 if on else 12, 0, 0)
        self.theater_changed.emit(on)
        self.theater_btn.setText("Exit theater" if on else "Theater")
        self.exit_theater_key.setEnabled(on)

    # ---------- called by the Movies page ----------
    def stop(self):
        self._cancel_loading()  # a film still loading must not start after Stop or Log out
        self.player.stop()

    def pause(self):
        self._cancel_loading()
        self.player.pause()

    def _cancel_loading(self):
        if self.runner.cancel("open"):
            self.status.setText("")

    def showEvent(self, event):
        super().showEvent(event)
        if not self.loaded:  # the first time the tab opens, show some popular titles
            self.do_search()

    # ---------- search ----------
    def do_search(self):
        keyword = self.search_input.text().strip()
        collection = self.collection_box.currentData()
        self.loaded = True
        self.status.setText("Searching...")

        def done(videos, error):
            if error:
                self.status.setText(error)
                return
            self.results_list.clear()
            for v in videos:
                text = f"{v['title']} ({v['year']})" if v["year"] else v["title"]
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, v)  # hide the full info in the item
                self.results_list.addItem(item)
            self.status.setText(
                f"{len(videos)} results. Double-click one to open it." if videos
                else "No results found")

        self.runner.run("search", lambda: archive.search_videos(collection, keyword), done)

    def add_to_watchlist(self):
        item = self.results_list.currentItem()
        if item is None:
            self.status.setText("Select a title from the results first")
            return
        video = item.data(Qt.ItemDataRole.UserRole)
        if db.add_to_watchlist(self.user_id, "archive", "video", video["id"],
                               video["title"], video["year"]):
            self.status.setText(f"Added to watchlist: {video['title']}")
            self.watchlist_changed.emit()
        else:
            self.status.setText("That title is already on your watchlist")

    # ---------- opening a title ----------
    def open_item(self, item):
        self.open_video(item.data(Qt.ItemDataRole.UserRole))

    def open_video(self, video):
        self.status.setText(f"Loading {video['title']}...")

        def done(files, error):
            if error:
                self.status.setText(error)
            else:
                self.show_files(video, files)

        self.runner.run("open", lambda: archive.get_playable_files(video["id"]), done)

    def show_files(self, video, files):
        self.episodes_list.clear()
        if not files:
            self.status.setText("No playable video file for this one. Try another.")
            return

        for f in files:
            text = f"{f['label']}  ({f['size_mb']} MB)" if f["size_mb"] else f["label"]
            ep = QListWidgetItem(text)
            ep.setData(Qt.ItemDataRole.UserRole, {"video": video, "file": f})
            self.episodes_list.addItem(ep)

        self.status.setText(f"{len(files)} file(s) found")
        if len(files) == 1:  # a single movie: just play it
            self.episodes_list.setCurrentRow(0)
            self.play_episode(self.episodes_list.item(0))

    # ---------- playback ----------
    def play_episode(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        video, f = data["video"], data["file"]
        self.player.setSource(QUrl(f["url"]))
        self.player.play()
        if f["label"] == video["title"]:
            self.now_playing.setText(video["title"])
        else:
            self.now_playing.setText(f"{video['title']} - {f['label']}")

    def play_next_episode(self):
        row = self.episodes_list.currentRow() + 1
        if 0 < row < self.episodes_list.count():  # auto-play the next episode
            self.episodes_list.setCurrentRow(row)
            self.play_episode(self.episodes_list.item(row))

    def toggle_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.source().isEmpty():
            ep = self.episodes_list.currentItem()
            if ep:
                self.play_episode(ep)
            elif self.results_list.currentItem():
                self.open_item(self.results_list.currentItem())
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
        s = QMediaPlayer.MediaStatus
        if status == s.EndOfMedia:
            self.play_next_episode()
        elif status in (s.LoadingMedia, s.StalledMedia, s.BufferingMedia):
            self.status.setText("Buffering...")
        elif status in (s.LoadedMedia, s.BufferedMedia):
            self.status.setText("")
        elif status == s.InvalidMedia:
            self.status.setText("This video can't be played (unsupported format or bad link).")

    def on_player_error(self, error, message):
        self.status.setText(f"Playback error: {message}")