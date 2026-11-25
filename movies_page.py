from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QComboBox
)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import archive
from widgets import ClickableSlider, format_time

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

class MoviesPage(QWidget):
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
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
        left.addWidget(self.section_label("RESULTS  ·  DOUBLE-CLICK TO OPEN"))
        left.addWidget(self.results_list, 3)
        left.addWidget(self.section_label("EPISODES / PARTS  ·  DOUBLE-CLICK TO PLAY"))
        left.addWidget(self.episodes_list, 2)
        left_panel = QWidget()
        left_panel.setFixedWidth(340)
        left_panel.setLayout(left)

        middle = QHBoxLayout()
        middle.setSpacing(20)
        middle.addWidget(left_panel)
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
        fullscreen_btn = QPushButton("Fullscreen")
        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(120)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        controls_row.addWidget(self.play_btn)
        controls_row.addWidget(stop_btn)
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

        # ----- page header -----
        title = QLabel("Movies & TV")
        title.setObjectName("title")
        subtitle = QLabel("Free public-domain films and classic shows from the Internet Archive")
        subtitle.setObjectName("subtitle")

        # ----- put everything together -----
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addLayout(search_row)
        layout.addLayout(middle, 1)
        layout.addWidget(player_bar)
        layout.addWidget(self.status)
        self.setLayout(layout)

        # ----- connect signals to functions -----
        search_btn.clicked.connect(self.do_search)
        self.search_input.returnPressed.connect(self.do_search)
        self.results_list.itemDoubleClicked.connect(self.open_item)
        self.episodes_list.itemDoubleClicked.connect(self.play_episode)
        self.play_btn.clicked.connect(self.toggle_play)
        stop_btn.clicked.connect(self.player.stop)
        fullscreen_btn.clicked.connect(self.video_widget.enter_fullscreen)  # Esc or double-click exits
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.seek_slider.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status)
        self.player.errorOccurred.connect(self.on_player_error)

    @staticmethod
    def section_label(text):
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    # ---------- called by the app window ----------
    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.pause()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.loaded:  # the first time the page opens, show some popular titles
            self.loaded = True
            QTimer.singleShot(0, self.do_search)

    # ---------- search ----------
    def do_search(self):
        keyword = self.search_input.text().strip()
        collection = self.collection_box.currentData()
        self.status.setText("Searching...")
        QApplication.processEvents()  # lets the label update before the request runs
        try:
            videos = archive.search_videos(collection, keyword)
        except Exception as e:
            self.status.setText(str(e))
            return

        self.results_list.clear()
        self.episodes_list.clear()
        for v in videos:
            text = f"{v['title']} ({v['year']})" if v["year"] else v["title"]
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, v)  # hide the full info in the item
            self.results_list.addItem(item)
        self.status.setText(
            f"{len(videos)} results. Double-click one to open it." if videos else "No results found"
        )

    # ---------- opening a title ----------
    def open_item(self, item):
        video = item.data(Qt.ItemDataRole.UserRole)
        self.status.setText(f"Loading {video['title']}...")
        QApplication.processEvents()
        try:
            files = archive.get_playable_files(video["id"])
        except Exception as e:
            self.status.setText(str(e))
            return

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