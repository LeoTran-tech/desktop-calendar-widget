# Desktop Calendar

A lightweight PySide6 desktop calendar widget for Windows.

The goal is simple:

> Open your computer, glance at the widget, and immediately understand what is coming up.

Desktop Calendar is intentionally not a replacement for Google Calendar. Google Calendar remains the main interface for creating, editing and managing calendar data.

The desktop widget focuses on fast, low-effort awareness of upcoming events and tasks.

## Product Philosophy

The application is designed around reducing cognitive load.

The user should not need to:

- open Google Calendar just to check what is coming up
- click through multiple screens
- manually refresh data
- start Chrome or PowerShell scripts
- wait for network requests before seeing anything
- inspect technical errors

Important information should be understandable within a few seconds.

The widget prioritizes:

- glanceability
- minimal interaction
- quiet background behaviour
- fast startup
- graceful offline behaviour
- simple visual hierarchy

## Current Features

- Monthly calendar overview
- Upcoming events for the next configurable number of days
- Google Calendar event synchronisation
- Google Tasks support
- Background task scraping where additional Google Calendar UI information is required
- Persistent Google browser session
- Headless Chrome background integration
- Automatic periodic refresh
- Manual refresh button
- Local event/task cache
- Cached data displayed immediately at startup
- Last-updated / synchronisation status
- Graceful fallback to saved events when refresh fails
- Open Google Calendar directly from the widget
- Lock/unlock widget position
- Frameless draggable and resizable window
- Automatic Windows startup support

## UX Principles

### Glanceability first

The most important information is:

- date
- time
- event/task title
- synchronisation freshness

Primary information should not require interaction to discover.

### Low cognitive load

Always-visible controls and text should earn their place.

Rare or complex operations should not occupy permanent space in the widget.

### Google Calendar is the source of truth

Creating, editing and deleting events remains the responsibility of Google Calendar.

The widget provides quick access to Google Calendar when management is required.

### Quiet background behaviour

Normal background work should remain invisible.

Chrome, Playwright, OAuth, caching and network requests are implementation details and should not interrupt the user.

### Graceful failure

If Google Calendar cannot be refreshed, the application keeps showing the most recently cached events instead of presenting an empty widget.

Example status:

```text
⚠ Showing saved events · Updated 12 min ago

Run

Install dependencies:

pip install -r requirements.txt

Run:

python app.py
Configuration

config.json contains private calendar configuration and must not be committed to Git.

Create it from:

config.example.json

Sensitive files such as the following must remain local:

config.json
credentials.json
token.json
Local Application Data

Persistent application data should be stored outside the repository under the user's local Windows application data directory.

For example:

%LOCALAPPDATA%\DesktopCalendar\

This can contain:

cache.json
ChromeProfile\

The Chrome profile allows the background calendar session to remain authenticated between application launches.

These files must not be committed to Git.

Background Browser Integration

Some Google Calendar information cannot be obtained with sufficient detail through the available API.

Where browser automation is required, Desktop Calendar launches a dedicated Chrome profile in the background and connects to it using Playwright.

Normal users should not need to manually run Chrome with remote debugging.

The browser session is an implementation detail and should remain invisible during normal operation.

Non-Goals

Desktop Calendar is not intended to become a complete Google Calendar client.

Features that generally belong in Google Calendar include:

creating events
editing events
deleting events
appointment schedule management
complex calendar configuration

The widget should remain focused on answering one question:

What do I have coming up?