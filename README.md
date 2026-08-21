# Desktop Calendar

A lightweight PySide6 desktop calendar widget for Windows.

The goal is simple:

> Open your computer, glance at the widget, and immediately understand what is coming up.

Desktop Calendar is intentionally not a replacement for Google Calendar. Google Calendar remains the source of truth for creating, editing and managing calendar data.

## Current Features

- Monthly calendar overview
- Mouse-wheel month navigation: up to 3 months back and 6 months forward
- Upcoming list with a 7-day default
- Optional upcoming ranges of 3, 7, 14 or 30 days through Settings
- Google Calendar event synchronisation
- Google Tasks support
- Persistent background browser session where scraping is required
- Automatic periodic refresh and manual refresh
- Local event/task cache displayed immediately at startup
- Last-updated / synchronisation status
- Graceful fallback to saved events when refresh fails
- Open Google Calendar directly from the widget
- Lock/unlock widget position
- Frameless draggable and resizable window
- Multi-monitor-safe position restore
- Automatic recovery if a previously used monitor is disconnected
- System tray icon with Show, Hide, Settings and Quit
- Automatic Windows startup support

## UX Principles

The widget prioritizes glanceability, minimal interaction, quiet background behaviour and graceful failure. Primary information such as date, time, title and sync freshness should be understandable without opening menus or navigating screens.

Rare controls belong outside the always-visible interface. For example, the upcoming-range preference is available through the system tray Settings dialog instead of adding another permanent control to the widget.

## Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your private configuration from the example:

```powershell
Copy-Item config.example.json config.json
```

Then run:

```powershell
python app.py
```

## Configuration and Private Data

`config.json` contains private calendar configuration and must not be committed to Git. OAuth files such as `credentials.json` and `token.json` must also remain local.

Persistent application data is stored outside the repository. The event cache and Chrome profile use `%LOCALAPPDATA%\DesktopCalendar\`. User preferences such as the upcoming range and window geometry are stored through Qt's `QSettings` mechanism.

## Background Browser Integration

Some Google Calendar information is obtained through a dedicated persistent Chrome profile and Playwright. The browser is launched headlessly and should remain an implementation detail during normal use.

## Non-Goals

Desktop Calendar is not intended to become a complete Google Calendar client. Complex event management, appointment schedules and advanced calendar configuration continue to belong in Google Calendar.

The widget remains focused on one question:

> What do I have coming up?
