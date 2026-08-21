from datetime import datetime

from services.google_calendar import GoogleCalendarService
from services.google_tasks import GoogleTasksService
from services.google_calendar_scraper import GoogleCalendarScraperService
from services.google_calendar_api import GoogleCalendarApiService

class CombinedCalendarService:
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        self.tasks_service = GoogleTasksService()
        self.scraper_service = GoogleCalendarScraperService()
        self.days_ahead = self.calendar_service.days_ahead
        self.calendar_api = GoogleCalendarApiService()

    def _item_key(self, item):
        start_time = (
            item.start.strftime("%H:%M")
            if isinstance(item.start, datetime)
            else "ALL_DAY"
        )

        end_time = (
            item.end.strftime("%H:%M")
            if isinstance(item.end, datetime)
            else ""
        )

        return (
            item.summary.strip().lower(),
            item.event_date,
            start_time,
            end_time,
        )

    def get_events(self, days_ahead=None):
        days = (
            days_ahead
            if days_ahead is not None
            else self.days_ahead
        )

        events = self.calendar_service.get_events(days)

        try:
            tasks = self.scraper_service.get_tasks(days)
        except Exception as e:
            print("Task scraper error:", e)
            tasks = []

        items = {}

        # Event/iCal trước
        for event in events:
            items[self._item_key(event)] = event

        # Nếu scraper tìm thấy cùng item,
        # ưu tiên scraper vì biết chắc đây là TASK
        for task in tasks:
            items[self._item_key(task)] = task

        result = list(items.values())

        result.sort(
            key=lambda item: item.sort_key()
        )

        return result

    def create_event(self, event):
        if event.item_type == "task":
            return self.tasks_service.create_task(event)

        return self.calendar_api.create_event(event)