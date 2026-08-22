# Desktop Calendar Architecture

## Product Principle

Desktop Calendar is a glanceable desktop companion, not a replacement for Google Calendar.

The UI should stay small and quiet while network access, OAuth, browser automation, caching and synchronisation remain implementation details.

Google Calendar and Google Tasks are authoritative. Local storage exists for startup speed, resilience and preferences.

## High-Level Architecture

```text
                    Google Account
                         |
          +--------------+---------------+
          |                              |
          v                              v
 Google Calendar API              Google Tasks API
          |                              |
          |                        dated task data
          |                              |
          +--------------+---------------+
                         |
                         v
                CombinedCalendarService
                         ^
                         |
              Playwright task scraper
                         ^
                         |
        app-owned Edge / Chrome / Brave profile
                         |
                         v
               Google Calendar web UI

                         |
                         v
                CalendarController
                 (background worker)
                         |
                         v
                   CalendarWidget
              +----------+----------+
              |                     |
              v                     v
         MonthCalendar        UpcomingEventsPanel
                                     |
                                     v
                                  EventCard
```

## Layers

### `models/`

`CalendarEvent` is the shared application-level representation for both events and tasks.

The UI consumes this model rather than Google API payloads or DOM structures.

### `services/google_calendar_api.py`

Primary Calendar integration.

Responsibilities include:

- reading events in a date range
- recurring event expansion through the Calendar API's normal event listing behaviour
- event metadata conversion into `CalendarEvent`
- event creation

This replaces the older private-iCal read path as the active event source.

### `services/google_tasks.py`

Primary Google Tasks integration.

Responsibilities include:

- listing dated tasks
- including completed tasks where appropriate for calendar history
- creating tasks
- converting Tasks API objects into `CalendarEvent`

The Tasks API does not expose all recurring-task occurrence/time information visible inside Google Calendar.

### `services/google_calendar_scraper.py`

Supplementary task integration.

Responsibilities include:

- connecting to the app-owned Chromium browser over CDP
- opening Google Calendar month views
- reading Calendar-rendered task accessibility text
- extracting task title, date and displayed time
- supplementing/replacing matching API tasks when richer information is available

The scraper deliberately uses semantic/accessibility-oriented information such as `role="button"` and task text rather than Google-generated CSS class names where possible.

Because Google controls the Calendar UI, this service must always be treated as less reliable than the official APIs.

### `services/chrome_calendar_session.py`

Despite the historical filename, this module manages supported Chromium browsers:

- Microsoft Edge
- Google Chrome
- Brave

It:

- detects installed browser executables
- uses a dedicated Desktop Calendar browser profile
- launches the profile visibly during sign-in
- launches it headlessly during normal scraping
- exposes CDP on the local debugging port
- switches between visible and background modes
- detects whether Google Calendar is signed in

Microsoft Edge is the default.

### `services/combined_calendar.py`

Aggregates:

- Calendar API events
- Tasks API tasks
- scraper-enriched tasks

Tasks are deduplicated primarily by normalized title and event date so a scraper result can replace the matching API representation when it contains richer Calendar-visible timing.

This service is also the main target for the planned reliability-hardening work described in `RELIABILITY.md`.

### `services/event_cache.py`

Stores the last successful combined dataset under `%LOCALAPPDATA%\DesktopCalendar`.

Current behaviour provides fast startup and whole-dataset fallback.

Planned hardening will distinguish source-specific health and preserve last-known-good scraper data independently so a partial failure cannot overwrite good recurring-task data.

### `controllers/calendar_controller.py`

Keeps service work off the Qt UI thread by running refresh jobs through `QThreadPool`.

The controller currently emits a combined result or top-level error.

Future reliability work should carry structured per-source sync health in addition to data.

### `ui/dialogs/first_run_setup_dialog.py`

Required setup gate before the normal widget starts.

Flow:

```text
First launch
    |
    v
Google OAuth
    |
    v
Choose Edge / Chrome / Brave
    |
    v
Open app-owned browser profile
    |
    v
Sign in until Google Calendar is visible
    |
    v
Verify browser session
    |
    v
Mark setup complete
    |
    v
Start CalendarWidget
```

If setup is cancelled, the normal widget does not start.

Windows auto-start is registered only after setup succeeds.

### `ui/calendar_widget.py`

Top-level desktop widget.

Responsibilities include:

- immediate cache display
- starting background refresh
- status display
- month/date interaction
- Settings
- browser preference
- lock/unlock position
- opening Google Calendar
- tray visibility integration

The window uses `Qt.Tool | Qt.FramelessWindowHint`, so it behaves as a desktop utility without a normal taskbar button.

### `ui/system_tray.py`

Persistent utility control surface:

- Show Calendar
- Hide Calendar
- Settings
- Quit

The tray remains the natural launcher/control point while the widget itself stays minimal.

### `ui/behaviors/frameless_window.py`

Owns:

- drag
- edge/corner resize
- position lock

When locked, drag and resize are disabled.

### `ui/behaviors/window_position.py`

Persists geometry through `QSettings` and recovers the widget safely when monitor topology or resolution changes.

## Runtime Data

```text
%LOCALAPPDATA%\DesktopCalendar\
├── BrowserProfiles\
│   ├── edge\
│   ├── chrome\
│   └── brave\
├── cache.json
└── token.json
```

Not every browser profile directory necessarily exists; only selected/used browsers create profiles.

Qt preferences are stored separately through `QSettings`.

## Startup Flow

```text
Application starts
      |
      v
Is setup complete?
   |          |
  no         yes
   |          |
   v          |
First-run     |
setup         |
   |          |
success ------+
      |
      v
Create widget
      |
      +------------------+
      |                  |
      v                  v
Restore geometry     Load cache
      |                  |
      +---------+--------+
                |
                v
          Show useful UI
                |
                v
        Background refresh
          /       |       \
         v        v        v
 Calendar API  Tasks API  Scraper
         \        |        /
          \       |       /
           v      v      v
        Combined result
                |
                v
         Update UI/cache
```

## Packaging

Development/release builds use PyInstaller in `--onedir` mode.

Google OAuth client credentials are bundled into the application build while per-user OAuth tokens remain outside the installation directory.

The installer flow uses Inno Setup and packages the contents of:

```text
dist\DesktopCalendar\
```

## Current Reliability Boundary

Calendar API and Tasks API are official integrations.

The scraper depends on a web UI controlled by Google. Therefore:

- a Calendar UI redesign can break parsing
- a browser sign-in can expire
- a CDP/browser startup can fail
- rendering/lazy-loading/viewport changes can affect discovered tasks

The application should never equate “API refresh succeeded” with “all sources are healthy”.

The next architecture phase is source-aware health, anomaly detection and last-known-good scraper preservation.
