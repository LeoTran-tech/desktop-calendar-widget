import re
from datetime import date, datetime, time, timedelta

import recurring_ical_events
import requests
from icalendar import Calendar

from config import load_config
from models.calendar_event import CalendarEvent
from services.base_calendar import BaseCalendarService


def extract_url(*texts):
    for text_value in texts:
        if not text_value:
            continue

        match = re.search(r"https?://[^\s<>]+", str(text_value))

        if match:
            return match.group(0)

    return ""


class GoogleCalendarService(BaseCalendarService):
    """Read-only Google Calendar service backed by a private iCal feed."""

    supports_write = False

    def __init__(self) -> None:
        config = load_config()
        self.calendar_url = config.get("calendar_url")
        self.days_ahead = int(config.get("days_ahead", 14))

        if not self.calendar_url:
            raise ValueError("calendar_url is not configured in config.json")

    def _download_calendar(self) -> Calendar:
        response = requests.get(
            self.calendar_url,
            timeout=15,
        )
        response.raise_for_status()

        if b"BEGIN:VCALENDAR" not in response.content:
            raise ValueError(
                "The configured URL did not return valid iCal data."
            )

        return Calendar.from_ical(response.content)

    def get_events(
        self,
        days_ahead: int | None = None,
    ) -> list[CalendarEvent]:
        today = datetime.now().astimezone().date()
        days = (
            days_ahead
            if days_ahead is not None
            else self.days_ahead
        )

        return self.get_events_between(
            today,
            today + timedelta(days=days),
        )

    def get_events_between(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:
        """Return events in [start_date, end_date)."""

        if end_date <= start_date:
            return []

        calendar_data = self._download_calendar()
        now = datetime.now().astimezone()
        tzinfo = now.tzinfo

        start = datetime.combine(
            start_date,
            time.min,
            tzinfo=tzinfo,
        )
        end = datetime.combine(
            end_date,
            time.min,
            tzinfo=tzinfo,
        )

        raw_events = recurring_ical_events.of(
            calendar_data
        ).between(start, end)

        events: list[CalendarEvent] = []

        for raw_event in raw_events:
            events.append(
                self._to_calendar_event(
                    raw_event,
                    now,
                )
            )

        events.sort(
            key=lambda event: event.sort_key()
        )
        return events

    def _to_calendar_event(
        self,
        raw_event,
        now: datetime,
    ) -> CalendarEvent:
        dtstart = raw_event.decoded("DTSTART")

        if isinstance(dtstart, datetime):
            if dtstart.tzinfo is None:
                dtstart = dtstart.replace(
                    tzinfo=now.tzinfo
                )
            dtstart = dtstart.astimezone(
                now.tzinfo
            )

        dtend = None

        if raw_event.get("DTEND") is not None:
            dtend = raw_event.decoded("DTEND")

            if isinstance(dtend, datetime):
                if dtend.tzinfo is None:
                    dtend = dtend.replace(
                        tzinfo=now.tzinfo
                    )
                dtend = dtend.astimezone(
                    now.tzinfo
                )

        recurrence = []
        rrule = raw_event.get("RRULE")

        if rrule:
            recurrence = [
                str(
                    rrule.to_ical(),
                    "utf-8",
                )
            ]

        location = str(
            raw_event.get("LOCATION", "")
        )
        description = str(
            raw_event.get("DESCRIPTION", "")
        )
        url = str(
            raw_event.get("URL", "")
        )

        if not url:
            url = extract_url(
                location,
                description,
            )

        organizer = str(
            raw_event.get("ORGANIZER", "")
        ).replace("mailto:", "")

        attendees = []
        raw_attendees = raw_event.get(
            "ATTENDEE",
            [],
        )

        if raw_attendees and not isinstance(
            raw_attendees,
            list,
        ):
            raw_attendees = [raw_attendees]

        for attendee in raw_attendees:
            attendees.append(
                str(attendee).replace(
                    "mailto:",
                    "",
                )
            )

        reminders = []

        for component in raw_event.subcomponents:
            if component.name != "VALARM":
                continue

            trigger = component.decoded(
                "TRIGGER"
            )

            if isinstance(trigger, timedelta):
                minutes = abs(
                    int(
                        trigger.total_seconds()
                        / 60
                    )
                )

                if minutes < 60:
                    reminders.append(
                        f"{minutes} minutes before"
                    )
                else:
                    reminders.append(
                        f"{minutes // 60} hours before"
                    )

        return CalendarEvent(
            event_id=(
                str(raw_event.get("UID", ""))
                or None
            ),
            summary=str(
                raw_event.get(
                    "SUMMARY",
                    "Untitled",
                )
            ),
            start=dtstart,
            end=dtend,
            location=location,
            description=description,
            url=url,
            organizer=organizer,
            attendees=attendees,
            reminders=reminders,
            recurrence=recurrence,
            item_type="event",
        )
