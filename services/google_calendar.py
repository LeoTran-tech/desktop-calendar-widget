from datetime import datetime, timedelta
import requests
from icalendar import Calendar
import recurring_ical_events

from config import load_config


class GoogleCalendarService:
    def __init__(self):
        config = load_config()
        self.calendar_url = config.get("calendar_url")
        self.days_ahead = int(config.get("days_ahead", 14))

        if not self.calendar_url:
            raise ValueError("calendar_url chưa được cấu hình trong config.json")

    def _download_calendar(self):
        response = requests.get(self.calendar_url, timeout=15)
        response.raise_for_status()

        if b"BEGIN:VCALENDAR" not in response.content:
            raise ValueError("URL không trả về dữ liệu iCal hợp lệ.")

        return Calendar.from_ical(response.content)

    def get_events(self, days_ahead=None):
        cal = self._download_calendar()

        now = datetime.now().astimezone()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        days = days_ahead if days_ahead is not None else self.days_ahead
        end = start + timedelta(days=days)

        raw_events = recurring_ical_events.of(cal).between(start, end)
        events = []

        for event in raw_events:
            summary = str(event.get("SUMMARY", "Untitled"))
            dtstart = event.decoded("DTSTART")

            if isinstance(dtstart, datetime):
                if dtstart.tzinfo is None:
                    dtstart = dtstart.replace(tzinfo=now.tzinfo)
                dtstart = dtstart.astimezone(now.tzinfo)

                event_date = dtstart.date()
                event_time = dtstart.strftime("%H:%M")
                start_iso = dtstart.isoformat()
                all_day = False
            else:
                event_date = dtstart
                event_time = "All day"
                start_iso = None
                all_day = True

            events.append({
                "summary": summary,
                "date": event_date,
                "time": event_time,
                "start": start_iso,
                "all_day": all_day,
            })

        events.sort(
            key=lambda e: (
                e["date"],
                e["all_day"],
                e["start"] or ""
            )
        )
        return events
