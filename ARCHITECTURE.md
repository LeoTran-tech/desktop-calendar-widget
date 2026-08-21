# Architecture Notes

## Product Architecture Principle

Desktop Calendar is a glanceable desktop companion rather than a full calendar application. Technical complexity should remain behind a simple always-visible widget.

Google Calendar and Google Tasks remain the authoritative sources. Local data exists only for startup speed, resilience and lightweight user preferences.

## Layers

### `models/`

Defines application-level data structures. `CalendarEvent` is the shared representation consumed by the UI.

### `services/`

Owns external data access, including iCal, Google APIs, Tasks, browser automation and local cache.

### `controllers/`

Coordinates service work and keeps network or browser work off the UI thread.

### `ui/components/`

Contains focused presentation components:

- `month_calendar.py` — month grid and wheel navigation
- `upcoming_events.py` — upcoming-list composition and controls
- `event_card.py` — presentation of a single event/task

### `ui/behaviors/`

Contains window behaviour that is independent of calendar data:

- `frameless_window.py` — drag, resize and lock behaviour
- `window_position.py` — saved geometry and multi-monitor recovery

### `ui/system_tray.py`

Owns the Windows system tray interface. Rare actions such as Settings and Quit remain outside the permanent widget UI.

### `ui/dialogs/settings_dialog.py`

Provides the small user preference surface for the upcoming range. The default is 7 days, with 3, 7, 14 and 30-day choices.

### `utils/app_settings.py`

Stores user preferences with Qt `QSettings`. Preferences are not mixed into the private calendar integration configuration.

## Startup Flow

```text
Windows / User launches app
             |
             v
      CalendarWidget starts
             |
       +-----+------+
       |            |
       v            v
Restore window   Load cache
position         immediately
       |            |
       +-----+------+
             |
             v
      Show useful UI
             |
             v
      Background sync
        +----+----+
        |         |
     Success    Failure
        |         |
        v         v
 Update UI     Keep cache
 Save cache    Show warning
```

## Window and Monitor Behaviour

Window geometry and the last screen name are saved through `QSettings`. On startup, the app restores the saved geometry if it is still visible on an attached monitor.

If a previously used monitor is disconnected and the widget would be off-screen, `WindowPositionManager` moves it to an active monitor. The default placement is near the top-right of the preferred or primary monitor.

## Month Navigation

The month grid remains centered on the current month at startup. Mouse-wheel navigation is intentionally bounded to 3 months in the past and 6 months in the future. This supports quick nearby planning without turning the widget into a full calendar browser.

## Upcoming Range

The default upcoming range is 7 days. Users who need a different horizon can select 3, 7, 14 or 30 days through the tray Settings dialog. No range selector is permanently displayed on the widget.

## System Tray

When the Windows system tray is available, closing/hiding the widget does not have to terminate the process. The tray provides:

- Show Calendar
- Hide Calendar
- Settings
- Quit

Clicking the tray icon toggles widget visibility.

## Graceful Failure

A failed refresh must not clear useful cached data. The UI continues displaying the most recent successful cache and communicates freshness with a lightweight status, for example:

```text
⚠ Showing saved events · Updated 18 min ago
```

## Design Decision Test

Before adding a feature, ask:

> Does this reduce the effort required for the user to understand what is coming up?

If not, it probably should not occupy the always-visible widget UI.
