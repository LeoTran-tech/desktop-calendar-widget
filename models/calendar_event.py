from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Union

DateLike = Union[date, datetime]


@dataclass(slots=True)
class CalendarEvent:
    """Application-level event model.

    UI code depends on this model rather than the Google/iCal payload format.
    That keeps the UI independent from whichever calendar backend is used.
    """
    
    summary: str
    start: DateLike

    end: Optional[DateLike] = None
    event_id: Optional[str] = None
    location: str = ""
    description: str = ""
    recurrence: list[str] = field(default_factory=list)

    url: str = ""
    organizer: str = ""
    attendees: list[str] = field(default_factory=list)
    reminders: list[str] = field(default_factory=list)

    item_type: str = "event"

    @property
    def all_day(self) -> bool:
        return not isinstance(self.start, datetime)

    @property
    def event_date(self) -> date:
        if isinstance(self.start, datetime):
            return self.start.date()
        return self.start

    @property
    def time_text(self) -> str:
        if isinstance(self.start, datetime):
            return self.start.strftime("%H:%M")
        return "All day"

    @property
    def time_range_text(self) -> str:
        if not isinstance(self.start, datetime):
            return "All day"

        start_text = self.start.strftime("%H:%M")

        if isinstance(self.end, datetime):
            end_text = self.end.strftime("%H:%M")
            return f"{start_text} - {end_text}"

        return start_text

    def sort_key(self) -> tuple:
        return (
            self.event_date,
            self.all_day,
            self.time_text,
            self.summary.lower(),
        )
