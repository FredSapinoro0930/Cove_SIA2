import threading
from PySide6.QtWidgets import QSlider, QStyle, QLabel, QFrame, QPushButton, QListWidgetItem
from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtGui import QPixmap, QImage, QColor, QRegion
from resources import asset_path

# short service names shown next to each song
LABELS = {"jamendo": "Jamendo", "deezer": "Deezer 30s"}


def format_time(ms):
    seconds = max(ms, 0) // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


def section_label(text):
    label = QLabel(text)
    label.setObjectName("sectionLabel")
    return label


def make_track_item(track):
    """A list row for a song. The full track info is hidden inside the item."""
    text = track["title"]
    if track["artist"]:
        text += f" - {track['artist']}"
    if track["duration"]:
        text += f"  ({format_time(track['duration'] * 1000)})"
    item = QListWidgetItem(f"{text}  ·  {LABELS.get(track['source'], track['source'])}")
    item.setData(Qt.ItemDataRole.UserRole, track)
    return item


def _tidy_logo(pixmap, width):
    """Crop the transparent margin, scale, and brighten the dark teal so it shows on dark.

    The coral play button is left alone, so the logo keeps its brand colors.
    """
    if pixmap.hasAlphaChannel():
        box = QRegion(pixmap.mask()).boundingRect()  # the part that isn't transparent
        if not box.isEmpty():
            pixmap = pixmap.copy(box)
    pixmap = pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)

    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if c.alpha() and c.red() < 120 and c.blue() > c.red():  # teal pixel
                image.setPixelColor(x, y, QColor(
                    min(255, int(c.red() * 1.5)),
                    min(255, int(c.green() * 1.5)),
                    min(255, int(c.blue() * 1.5)),
                    c.alpha(),
                ))
    return QPixmap.fromImage(image)


def make_logo(width, font_size=26):
    """The Cove wordmark as a QLabel, made readable on the dark theme."""
    logo = QLabel()
    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pixmap = QPixmap(asset_path("cove_wordmark.png"))
    if pixmap.isNull():
        logo.setText("Cove")
        logo.setStyleSheet(f"font-family: Outfit; font-size: {font_size}px; font-weight: 800; color: #f56e5c;")
        return logo
    logo.setPixmap(_tidy_logo(pixmap, width))
    return logo


def keyboard_focus_only(root):
    """Buttons show their focus ring only when reached with Tab, not after a mouse click.

    Call it once on a window after all its pages are built.
    """
    for button in root.findChildren(QPushButton):
        button.setFocusPolicy(Qt.FocusPolicy.TabFocus)


def make_card():
    """A rounded panel. Put a layout on it and add widgets as usual."""
    card = QFrame()
    card.setObjectName("card")
    return card


class ClickableSlider(QSlider):
    """A slider that jumps to the spot you click and follows your mouse while dragging."""

    def _jump_to(self, event):
        value = QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), int(event.position().x()), self.width()
        )
        self.setValue(value)
        self.sliderMoved.emit(value)  # tells the player to seek

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.maximum() > 0:
            self.setSliderDown(True)
            self._jump_to(event)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.maximum() > 0:
            self._jump_to(event)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(False)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class BackgroundRunner(QObject):
    """runner.run(key, work, on_done) calls on_done(result, error) back on the UI thread.

    Starting new work with the same key (or calling cancel) makes the older answer be
    ignored, so a slow old search can't overwrite a newer one.
    """

    _finished = Signal(str, int, object, object, object)

    def __init__(self, parent=None, max_threads=6):
        super().__init__(parent)
        self._latest = {}  # key -> number of the newest job
        self._counter = 0
        self._slots = threading.Semaphore(max_threads)
        self._finished.connect(self._deliver)

    def run(self, key, work, on_done):
        self._counter += 1
        number = self._counter
        self._latest[key] = number

        def job():
            result, error = None, None
            with self._slots:
                if self._latest.get(key) != number:
                    return  # cancelled while waiting for a free slot
                try:
                    result = work()
                except Exception as e:
                    error = str(e) or "Something went wrong."
            try:
                self._finished.emit(key, number, on_done, result, error)
            except RuntimeError:
                pass  # the window was closed while we were waiting

        threading.Thread(target=job, daemon=True).start()

    def cancel(self, key):
        """Returns True if there was unfinished work under this key."""
        return self._latest.pop(key, None) is not None

    def cancel_all(self):
        self._latest.clear()

    @Slot(str, int, object, object, object)
    def _deliver(self, key, number, on_done, result, error):
        if self._latest.get(key) != number:
            return  # an outdated answer
        del self._latest[key]
        on_done(result, error)
