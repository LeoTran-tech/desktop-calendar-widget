import json
import os
from datetime import date, datetime
from pathlib import Path

from models.calendar_event import CalendarEvent


CACHE_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "DesktopCalendar"
)

CACHE_FILE = CACHE_DIR / "cache.json"


class EventCache:

    def __init__(self) -> None:
        CACHE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        events: list[CalendarEvent],
    ) -> None:

        data = {
            "updated_at": datetime.now().astimezone().isoformat(),
            "events": [
                self._event_to_dict(event)
                for event in events
            ],
        }

        CACHE_FILE.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> list[CalendarEvent]:

        if not CACHE_FILE.exists():
            return []

        try:
            data = json.loads(
                CACHE_FILE.read_text(
                    encoding="utf-8"
                )
            )

            return [
                self._dict_to_event(item)
                for item in data.get("events", [])
            ]

        except Exception as exc:
            print("Cache load error:", exc)
            return []

    def _serialize_date(self, value):

        if value is None:
            return None

        if isinstance(value, datetime):
            return {
                "type": "datetime",
                "value": value.isoformat(),
            }

        return {
            "type": "date",
            "value": value.isoformat(),
        }

    def _deserialize_date(self, value):

        if not value:
            return None

        if value["type"] == "datetime":
            return datetime.fromisoformat(
                value["value"]
            )

        return date.fromisoformat(
            value["value"]
        )

    def _event_to_dict(
        self,
        event: CalendarEvent,
    ) -> dict:

        return {
            "summary": event.summary,
            "start": self._serialize_date(event.start),
            "end": self._serialize_date(event.end),

            "event_id": event.event_id,
            "location": event.location,
            "description": event.description,
            "recurrence": event.recurrence,

            "url": event.url,
            "organizer": event.organizer,
            "attendees": event.attendees,
            "reminders": event.reminders,

            "item_type": event.item_type,
        }

    def _dict_to_event(
        self,
        item: dict,
    ) -> CalendarEvent:

        return CalendarEvent(
            summary=item.get(
                "summary",
                "Untitled",
            ),

            start=self._deserialize_date(
                item["start"]
            ),

            end=self._deserialize_date(
                item.get("end")
            ),

            event_id=item.get("event_id"),

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
                "url",
                "",
            ),

            organizer=item.get(
                "organizer",
                "",
            ),

            attendees=item.get(
                "attendees",
                [],
            ),

            reminders=item.get(
                "reminders",
                [],
            ),

            item_type=item.get(
                "item_type",
                "event",
            ),
        )

    def get_updated_at(self) -> datetime | None:
        if not CACHE_FILE.exists():
            return None

        try:
            data = json.loads(
                CACHE_FILE.read_text(encoding="utf-8")
            )

            value = data.get("updated_at")

            if not value:
                return None

            return datetime.fromisoformat(value)

        except Exception:
            return None