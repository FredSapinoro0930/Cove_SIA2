from PySide6.QtWidgets import QSlider, QStyle, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QColor, QRegion
from resources import asset_path


def format_time(ms):
    seconds = max(ms, 0) // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


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
        logo.setStyleSheet(f"font-size: {font_size}px; font-weight: 800; color: #f56e5c;")
        return logo
    logo.setPixmap(_tidy_logo(pixmap, width))
    return logo


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