# Architecture notes

## Why this structure scales better

### `models/`
Defines data used by the application. UI code no longer knows about raw iCal
dictionaries.

### `services/`
Owns external calendar integrations. The current Google iCal feed is read-only.
A future Google Calendar API service can implement the same interface.

### `controllers/`
Coordinates service operations and UI updates. Calendar downloads are run in a
thread pool so network delays do not freeze the window.

### `ui/components/`
Contains reusable visual components. The month grid and upcoming-event list can
change independently.

### `ui/behaviors/`
Contains window behavior that is unrelated to calendar logic.

### `ui/calendar_widget.py`
Only assembles the application window and connects signals.

## Future event editing flow

```text
CalendarToolbar / EventDialog
          |
          v
 CalendarController
          |
          v
BaseCalendarService
          |
          v
GoogleCalendarApiService
```

For recurring events, keep recurrence rules in `CalendarEvent.recurrence` and
let the API service translate them to Google Calendar API recurrence strings.
