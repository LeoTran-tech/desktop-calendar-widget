from datetime import datetime, timedelta

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

    def get_tasks(self, days_ahead=14):
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)

        items = []

        task_lists = (
            self.service.tasklists()
            .list()
            .execute()
            .get("items", [])
        )

        for task_list in task_lists:
            tasks = (
                self.service.tasks()
                .list(
                    tasklist=task_list["id"],
                    showCompleted=False,
                    showHidden=False,
                )
                .execute()
                .get("items", [])
            )

            for task in tasks:
                due = task.get("due")

                if not due:
                    continue

                due_date = datetime.fromisoformat(
                    due.replace("Z", "+00:00")
                ).date()

                if not (today <= due_date < end_date):
                    continue

                items.append(
                    CalendarEvent(
                        summary=task.get("title", "Untitled task"),
                        start=due_date,
                        event_id=task.get("id"),
                        description=task.get("notes", ""),
                        item_type="task",
                    )
                )

        return items