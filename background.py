"""Runs slow work (internet requests) on a second thread so the window never freezes."""
import threading
from PySide6.QtCore import QObject, Signal, Slot


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
