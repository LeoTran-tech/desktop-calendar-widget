from abc import ABC, abstractmethod

from models.calendar_event import CalendarEvent


class BaseCalendarService(ABC):
    """Backend contract used by the rest of the application."""

    supports_write = False

    @abstractmethod
    def get_events(self, days_ahead: int | None = None) -> list[CalendarEvent]:
        raise NotImplementedError

    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        raise NotImplementedError(
            "This calendar backend is read-only. "
            "Creating events requires the Google Calendar API + OAuth."
        )

    def delete_event(self, event_id: str) -> None:
        raise NotImplementedError(
            "This calendar backend is read-only. "
            "Deleting events requires the Google Calendar API + OAuth."
        )
