from datetime import date, datetime, time, timedelta

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

    def get_events_between(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:

        if end_date <= start_date:
            return []

        tzinfo = datetime.now().astimezone().tzinfo

        time_min = datetime.combine(
            start_date,
            time.min,
            tzinfo=tzinfo,
        ).isoformat()

        time_max = datetime.combine(
            end_date,
            time.min,
            tzinfo=tzinfo,
        ).isoformat()

        events = []
        page_token = None

        while True:
            response = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=2500,
                    pageToken=page_token,
                )
                .execute()
            )

            for item in response.get("items", []):
                events.append(
                    self._to_calendar_event(item)
                )

            page_token = response.get(
                "nextPageToken"
            )

            if not page_token:
                break

        events.sort(
            key=lambda event: event.sort_key()
        )

        return events

    def _to_calendar_event(
        self,
        item: dict,
    ) -> CalendarEvent:

        start_data = item.get("start", {})
        end_data = item.get("end", {})

        if "dateTime" in start_data:
            start = datetime.fromisoformat(
                start_data["dateTime"].replace(
                    "Z",
                    "+00:00",
                )
            ).astimezone()

            end = None

            if "dateTime" in end_data:
                end = datetime.fromisoformat(
                    end_data["dateTime"].replace(
                        "Z",
                        "+00:00",
                    )
                ).astimezone()

        else:
            start = date.fromisoformat(
                start_data["date"]
            )

            end = (
                date.fromisoformat(end_data["date"])
                if "date" in end_data
                else None
            )

        organizer_data = item.get(
            "organizer",
            {},
        )

        organizer = organizer_data.get(
            "email",
            "",
        )

        attendees = [
            attendee.get("email", "")
            for attendee in item.get(
                "attendees",
                [],
            )
            if attendee.get("email")
        ]

        reminders = []

        reminder_data = item.get(
            "reminders",
            {},
        )

        for reminder in reminder_data.get(
            "overrides",
            [],
        ):
            minutes = reminder.get(
                "minutes"
            )

            if minutes is not None:
                reminders.append(
                    f"{minutes} minutes before"
                )

        return CalendarEvent(
            event_id=item.get("id"),
            summary=item.get(
                "summary",
                "Untitled",
            ),
            start=start,
            end=end,
            location=item.get(
                "location",
                "",
            ),
            description=item.get(
                "description",
                "",
            ),
            recurrence=item.get(
                "recurrence",
                [],
            ),
            url=item.get(
                "htmlLink",
                "",
            ),
            organizer=organizer,
            attendees=attendees,
            reminders=reminders,
            item_type="event",
        )

    def create_event(
        self,
        event: CalendarEvent,
    ):
        body = {
            "summary": event.summary,
            "description": event.description,
            "location": event.location,
        }

        if isinstance(
            event.start,
            datetime,
        ):
            end = event.end

            if not isinstance(
                end,
                datetime,
            ):
                end = (
                    event.start
                    + timedelta(hours=1)
                )

            body["start"] = {
                "dateTime":
                    event.start
                    .astimezone()
                    .isoformat()
            }

            body["end"] = {
                "dateTime":
                    end
                    .astimezone()
                    .isoformat()
            }

        else:
            body["start"] = {
                "date":
                    event.start.isoformat()
            }

            body["end"] = {
                "date": (
                    event.start
                    + timedelta(days=1)
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