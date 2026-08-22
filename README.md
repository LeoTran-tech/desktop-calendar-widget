# Desktop Calendar

A lightweight, glanceable Windows desktop calendar widget built with PySide6.

The goal is simple:

> Open your computer, glance at the desktop, and immediately understand what is coming up.

Desktop Calendar is not intended to replace Google Calendar. Google Calendar and Google Tasks remain the source of truth for creating, editing and managing calendar data.

## Current Features

- Monthly calendar overview
- Mouse-wheel month navigation across the nearby planning window
- Upcoming list with configurable 3, 7, 14 or 30-day range
- Google Calendar event and appointment synchronisation through the Google Calendar API
- Google Tasks synchronisation through the Google Tasks API
- Recurring-task/time enrichment by reading the Google Calendar web UI where the Tasks API does not expose equivalent information
- First-run setup flow for Google OAuth and browser sign-in
- Microsoft Edge, Google Chrome and Brave support for the background Calendar browser
- Microsoft Edge is the default browser
- Dedicated app-owned browser profile; the user's normal browser profile is not modified
- Persistent local cache displayed immediately at startup
- Automatic refresh and manual refresh
- Frameless, draggable and resizable widget
- Lock/unlock position
- Multi-monitor-safe geometry restore
- System tray controls for Show, Hide, Settings and Quit
- No normal taskbar button while the widget is running
- Automatic Windows startup after first-time setup completes
- PyInstaller-compatible Windows build
- Inno Setup-compatible installer flow

## Data Sources

Desktop Calendar combines three sources:

1. **Google Calendar API**
   - Events
   - Appointments
   - Recurring events
   - Time, location, description and other event metadata

2. **Google Tasks API**
   - Dated Google Tasks
   - Completed and uncompleted tasks within the requested date range

3. **Google Calendar web UI scraper**
   - Used only for task information that the Tasks API does not expose equivalently
   - In particular, recurring-task occurrences and Calendar-visible task time information
   - Uses Playwright with a dedicated Chromium-based browser profile

The scraper is intentionally a supplement, not the primary calendar backend.

## First-Time Setup

On first launch, Desktop Calendar requires two one-time sign-ins.

### 1. Google OAuth

The user signs in with Google and grants Calendar and Tasks access.

The OAuth token is stored locally at:

```text
%LOCALAPPDATA%\DesktopCalendar\token.json
```

### 2. Google Calendar browser sign-in

The user chooses:

- Microsoft Edge (recommended/default)
- Google Chrome
- Brave

Desktop Calendar opens the selected browser with a separate app-owned profile. The user signs in until Google Calendar itself is visible, then the app verifies the session.

Normal background operation is headless after setup.

Browser profiles are stored under:

```text
%LOCALAPPDATA%\DesktopCalendar\BrowserProfiles\
```

## Local Data

Persistent runtime data is stored outside the installation/project directory:

```text
%LOCALAPPDATA%\DesktopCalendar\
├── BrowserProfiles\
├── cache.json
└── token.json
```

Window geometry, browser preference, upcoming range and setup state are stored with Qt `QSettings`.

Sensitive runtime data must not be committed to Git.

## Running from Source

Install dependencies:

```powershell
pip install -r requirements.txt
```

Make sure the Google OAuth desktop-client `credentials.json` exists in the project root, then run:

```powershell
python app.py
```

`config.json` / private iCal configuration is no longer part of the active Calendar data path. Calendar events are read through the Google Calendar API.

## Building

A development build can be produced with PyInstaller:

```powershell
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name DesktopCalendar `
    --collect-all playwright `
    --add-data "credentials.json:." `
    app.py
```

The resulting application is:

```text
dist\DesktopCalendar\DesktopCalendar.exe
```

See `BUILD.md` for the release/installer workflow.

## Public Distribution

For arbitrary Google users to sign in without being manually added as OAuth test users, the Google OAuth application must be configured for production/public use and satisfy Google's verification requirements for the requested scopes.

Do not publish personal tokens, browser profiles, caches or other user-specific data.

## Reliability

The Google APIs are the stable integration layer. The Google Calendar UI scraper is inherently less stable because Google can change the Calendar web interface.

The long-term reliability goal is therefore not to assume the scraper can never break. It is to make scraper failure detectable, preserve the last known-good recurring-task data, and never silently present an incomplete calendar as fully up to date.

See `RELIABILITY.md`.

## Non-Goals

Desktop Calendar is not intended to become a full Google Calendar client.

Complex calendar management, advanced scheduling and account administration belong in Google Calendar.

The widget remains focused on one question:

> What do I have coming up?
