# Desktop Calendar

A small PySide6 desktop calendar widget.

## Architecture

```text
app.py
config.py
models/
  calendar_event.py
services/
  base_calendar.py
  google_calendar.py
controllers/
  calendar_controller.py
ui/
  calendar_widget.py
  styles.py
  behaviors/
    frameless_window.py
  components/
    month_calendar.py
    upcoming_events.py
utils/
  date_utils.py
```

`ui/calendar_widget.py` is only the top-level composition layer.

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Configuration

`config.json` contains a private Google Calendar iCal URL and should not be
committed to Git. A safe template is included as `config.example.json`.

## Future Add / Delete support

The current iCal URL is read-only. To create, update, or delete events, add a
new writable service using the Google Calendar API with OAuth 2.0.

Recommended future files:

```text
services/
  google_calendar_api.py

ui/dialogs/
  event_editor_dialog.py
  recurrence_dialog.py

ui/components/
  event_card.py
  calendar_toolbar.py
```

The existing `BaseCalendarService`, `CalendarEvent`, and `CalendarController`
already provide the separation needed for this migration.
