from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from models.calendar_event import CalendarEvent
from services.base_calendar import BaseCalendarService


class _WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()


class _Worker(QRunnable):
    def __init__(self, job: Callable[[], object]) -> None:
        super().__init__()
        self.job = job
        self.signals = _WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.job()
        except Exception as exc:
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class CalendarController(QObject):
    """Coordinates UI and services and keeps network work off the UI thread."""

    events_updated = Signal(list)
    error = Signal(str)
    busy_changed = Signal(bool)

    def __init__(
        self,
        service: BaseCalendarService,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.thread_pool = QThreadPool.globalInstance()
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def refresh(self) -> None:
        if self._busy:
            return

        self._set_busy(True)

        worker = _Worker(self.service.get_events)
        worker.signals.result.connect(self._on_events_loaded)
        worker.signals.error.connect(self.error.emit)
        worker.signals.finished.connect(self._finish_task)
        self.thread_pool.start(worker)

    def create_event(self, event: CalendarEvent) -> None:
        self._run_mutation(lambda: self.service.create_event(event))

    def delete_event(self, event_id: str) -> None:
        self._run_mutation(lambda: self.service.delete_event(event_id))

    def _run_mutation(self, job: Callable[[], object]) -> None:
        if self._busy:
            return

        self._set_busy(True)

        worker = _Worker(job)
        worker.signals.error.connect(self.error.emit)
        worker.signals.finished.connect(self._finish_mutation)
        self.thread_pool.start(worker)

    @Slot(object)
    def _on_events_loaded(self, result: object) -> None:
        self.events_updated.emit(list(result))

    @Slot()
    def _finish_mutation(self) -> None:
        self._set_busy(False)
        self.refresh()

    @Slot()
    def _finish_task(self) -> None:
        self._set_busy(False)

    def _set_busy(self, value: bool) -> None:
        if self._busy == value:
            return

        self._busy = value
        self.busy_changed.emit(value)
