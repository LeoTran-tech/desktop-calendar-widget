import re
from datetime import datetime, timedelta

import recurring_ical_events
import requests
from icalendar import Calendar

from config import load_config
from models.calendar_event import CalendarEvent
from services.base_calendar import BaseCalendarService

def extract_url(*texts):
    for text in texts:
        if not text:
            continue

        match = re.search(r"https?://[^\s<>]+", str(text))

        if match:
            return match.group(0)

    return ""

class GoogleCalendarService(BaseCalendarService):
    """Read-only Google Calendar service backed by a private iCal feed.

    This is deliberately isolated behind BaseCalendarService. Later, it can be
    replaced by a Google Calendar API implementation without changing the UI.
    """

    supports_write = False

    def __init__(self) -> None:
        config = load_config()
        self.calendar_url = config.get("calendar_url")
        self.days_ahead = int(config.get("days_ahead", 14))

        if not self.calendar_url:
            raise ValueError("calendar_url is not configured in config.json")

    def _download_calendar(self) -> Calendar:
        response = requests.get(self.calendar_url, timeout=15)
        response.raise_for_status()

        if b"BEGIN:VCALENDAR" not in response.content:
            raise ValueError("The configured URL did not return valid iCal data.")

        return Calendar.from_ical(response.content)

    def get_events(self, days_ahead: int | None = None) -> list[CalendarEvent]:
        calendar_data = self._download_calendar()

        now = datetime.now().astimezone()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        days = days_ahead if days_ahead is not None else self.days_ahead
        end = start + timedelta(days=days)

        raw_events = recurring_ical_events.of(calendar_data).between(start, end)
        events: list[CalendarEvent] = []

        for raw_event in raw_events:
            dtstart = raw_event.decoded("DTSTART")

            if isinstance(dtstart, datetime):
                if dtstart.tzinfo is None:
                    dtstart = dtstart.replace(tzinfo=now.tzinfo)
                dtstart = dtstart.astimezone(now.tzinfo)

            dtend = None
            if raw_event.get("DTEND") is not None:
                dtend = raw_event.decoded("DTEND")
                if isinstance(dtend, datetime):
                    if dtend.tzinfo is None:
                        dtend = dtend.replace(tzinfo=now.tzinfo)
                    dtend = dtend.astimezone(now.tzinfo)

            recurrence = []
            rrule = raw_event.get("RRULE")
            if rrule:
                recurrence = [str(rrule.to_ical(), "utf-8")]

            location = str(raw_event.get("LOCATION", ""))
            description = str(raw_event.get("DESCRIPTION", ""))
            url = str(raw_event.get("URL", ""))

            if not url:
                url = extract_url(location, description)

            organizer = str(raw_event.get("ORGANIZER", ""))
            organizer = organizer.replace("mailto:", "")

            attendees = []

            for attendee in raw_event.get("ATTENDEE", []):
                attendees.append(
                    str(attendee).replace("mailto:", "")
                )

            reminders = []

            for component in raw_event.subcomponents:
                if component.name == "VALARM":
                    trigger = component.decoded("TRIGGER")

                    if isinstance(trigger, timedelta):
                        minutes = abs(int(trigger.total_seconds() / 60))

                        if minutes < 60:
                            reminders.append(f"{minutes} minutes before")
                        else:
                            reminders.append(f"{minutes // 60} hours before")

            events.append(
                CalendarEvent(
                    event_id=str(raw_event.get("UID", "")) or None,
                    summary=str(raw_event.get("SUMMARY", "Untitled")),
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
            )

        events.sort(key=lambda event: event.sort_key())
        return events
