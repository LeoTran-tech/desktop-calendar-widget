from datetime import date, datetime, time, timedelta, timezone

from googleapiclient.discovery import build

from models.calendar_event import CalendarEvent
from services.google_auth import get_google_credentials


class GoogleTasksService:
    def __init__(self):
        credentials = get_google_credentials()

        self.service = build(
            "tasks",
            "v1",
            credentials=credentials,
        )

    def get_tasks(
        self,
        days_ahead: int = 14,
    ) -> list[CalendarEvent]:
        today = datetime.now().date()

        return self.get_tasks_between(
            today,
            today + timedelta(days=days_ahead),
        )

    def get_tasks_between(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:
        """Return dated tasks in [start_date, end_date).

        Completed tasks are included so the previous-month view can still
        show that a task existed on that date. The UI deliberately does not
        display completion/past badges.
        """

        if end_date <= start_date:
            return []

        items: list[CalendarEvent] = []

        due_min = datetime.combine(
            start_date,
            time.min,
            tzinfo=timezone.utc,
        ).isoformat().replace(
            "+00:00",
            "Z",
        )

        due_max = datetime.combine(
            end_date,
            time.min,
            tzinfo=timezone.utc,
        ).isoformat().replace(
            "+00:00",
            "Z",
        )

        task_lists = self._all_task_lists()

        for task_list in task_lists:
            page_token = None

            while True:
                response = (
                    self.service.tasks()
                    .list(
                        tasklist=task_list["id"],
                        showCompleted=True,
                        showHidden=True,
                        dueMin=due_min,
                        dueMax=due_max,
                        pageToken=page_token,
                        maxResults=100,
                    )
                    .execute()
                )

                for task in response.get(
                    "items",
                    [],
                ):
                    due = task.get("due")

                    if not due:
                        continue

                    due_date = datetime.fromisoformat(
                        due.replace(
                            "Z",
                            "+00:00",
                        )
                    ).date()

                    if not (
                        start_date
                        <= due_date
                        < end_date
                    ):
                        continue

                    items.append(
                        CalendarEvent(
                            summary=task.get(
                                "title",
                                "Untitled task",
                            ),
                            start=due_date,
                            event_id=task.get("id"),
                            description=task.get(
                                "notes",
                                "",
                            ),
                            item_type="task",
                        )
                    )

                page_token = response.get(
                    "nextPageToken"
                )

                if not page_token:
                    break

        items.sort(
            key=lambda item: item.sort_key()
        )
        return items

    def _all_task_lists(self) -> list[dict]:
        task_lists: list[dict] = []
        page_token = None

        while True:
            response = (
                self.service.tasklists()
                .list(
                    pageToken=page_token,
                    maxResults=100,
                )
                .execute()
            )

            task_lists.extend(
                response.get(
                    "items",
                    [],
                )
            )

            page_token = response.get(
                "nextPageToken"
            )

            if not page_token:
                break

        return task_lists

    def create_task(
        self,
        task: CalendarEvent,
    ):
        body = {
            "title": task.summary,
        }

        if task.description:
            body["notes"] = task.description

        due = datetime.combine(
            task.event_date,
            time.min,
        ).astimezone()

        body["due"] = due.isoformat()

        result = (
            self.service.tasks()
            .insert(
                tasklist="@default",
                body=body,
            )
            .execute()
        )

        task.event_id = result["id"]
        return task
