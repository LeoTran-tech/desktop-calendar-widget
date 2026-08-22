import json
import os

from datetime import date, datetime
from pathlib import Path

from models.calendar_event import CalendarEvent


APP_DATA_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "DesktopCalendar"
)

CACHE_FILE = (
    APP_DATA_DIR
    / "scraper_cache.json"
)

TEMP_CACHE_FILE = (
    APP_DATA_DIR
    / "scraper_cache.tmp"
)


class ScraperCache:
    def save(
        self,
        tasks: list[CalendarEvent],
    ) -> None:
        APP_DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "updated_at": (
                datetime.now()
                .astimezone()
                .isoformat()
            ),
            "tasks": [
                self._serialize(task)
                for task in tasks
            ],
        }

        serialized = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )

        try:
            # Write everything to a temporary
            # file first.
            with TEMP_CACHE_FILE.open(
                "w",
                encoding="utf-8",
            ) as file:
                file.write(
                    serialized
                )

                # Make Python flush its buffer.
                file.flush()

                # Ask the OS to flush the file
                # to disk before replacing the
                # known-good cache.
                os.fsync(
                    file.fileno()
                )

            # Atomic replacement.
            # The old cache stays untouched until
            # the new file has been fully written.
            os.replace(
                TEMP_CACHE_FILE,
                CACHE_FILE,
            )

        except Exception:
            # Never leave a broken temp file
            # behind.
            try:
                if TEMP_CACHE_FILE.exists():
                    TEMP_CACHE_FILE.unlink()
            except Exception:
                pass

            raise

    def load(
        self,
    ) -> list[CalendarEvent]:
        if not CACHE_FILE.exists():
            return []

        try:
            data = json.loads(
                CACHE_FILE.read_text(
                    encoding="utf-8"
                )
            )

            return [
                self._deserialize(item)
                for item in data.get(
                    "tasks",
                    [],
                )
            ]

        except Exception as exc:
            print(
                "Scraper cache error:",
                repr(exc),
            )

            return []

    def _serialize(
        self,
        task: CalendarEvent,
    ) -> dict:
        return {
            "summary":
                task.summary,

            "start":
                task.start.isoformat(),

            "start_is_datetime":
                isinstance(
                    task.start,
                    datetime,
                ),

            "end": (
                task.end.isoformat()
                if task.end
                else None
            ),

            "end_is_datetime":
                isinstance(
                    task.end,
                    datetime,
                ),

            "event_id":
                task.event_id,

            "location":
                task.location,

            "description":
                task.description,

            "recurrence":
                task.recurrence,

            "url":
                task.url,

            "organizer":
                task.organizer,

            "attendees":
                task.attendees,

            "reminders":
                task.reminders,

            "item_type":
                task.item_type,
        }

    def _deserialize(
        self,
        item: dict,
    ) -> CalendarEvent:

        start = (
            datetime.fromisoformat(
                item["start"]
            )
            if item.get(
                "start_is_datetime"
            )
            else date.fromisoformat(
                item["start"]
            )
        )

        end = None

        if item.get("end"):
            end = (
                datetime.fromisoformat(
                    item["end"]
                )
                if item.get(
                    "end_is_datetime"
                )
                else date.fromisoformat(
                    item["end"]
                )
            )

        return CalendarEvent(
            summary=item[
                "summary"
            ],

            start=start,
            end=end,

            event_id=item.get(
                "event_id"
            ),

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
                "task",
            ),
        )