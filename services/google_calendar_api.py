from datetime import date, datetime, timedelta

from googleapiclient.discovery import build

from models.calendar_event import CalendarEvent
from services.google_auth import get_google_credentials


class GoogleCalendarApiService:
    supports_write = True

    def __init__(self):
        credentials = get_google_credentials()

        self.service = build(
            "calendar",
            "v3",
            credentials=credentials,
        )

    def create_event(self, event: CalendarEvent):
        body = {
            "summary": event.summary,
            "description": event.description,
            "location": event.location,
        }

        if isinstance(event.start, datetime):
            end = event.end

            if not isinstance(end, datetime):
                end = event.start + timedelta(hours=1)

            body["start"] = {
                "dateTime": event.start.astimezone().isoformat()
            }

            body["end"] = {
                "dateTime": end.astimezone().isoformat()
            }

        else:
            body["start"] = {
                "date": event.start.isoformat()
            }

            body["end"] = {
                "date": (
                    event.start + timedelta(days=1)
                ).isoformat()
            }

        result = (
            self.service.events()
            .insert(
                calendarId="primary",
                body=body,
            )
            .execute()
        )

        event.event_id = result["id"]

        return event