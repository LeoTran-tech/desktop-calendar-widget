
---

# 4. Thay toàn bộ `ARCHITECTURE.md`

```markdown
# Architecture Notes

## Product Architecture Principle

Desktop Calendar is designed as a glanceable desktop companion rather than a full calendar application.

Architecture decisions should support the primary product goal:

> Give the user useful awareness of upcoming commitments with as little attention and interaction as possible.

Technical complexity should remain behind the interface.

The user should see a simple widget even if the implementation uses multiple services, Google APIs, OAuth, browser automation, caching and background threads.

## Source of Truth

Google Calendar and Google Tasks are the authoritative sources of calendar information.

The local application does not maintain an independent calendar database.

Local cache exists only to:

- improve startup speed
- preserve useful information during temporary network failures
- reduce visible loading states

Changes to calendar information should normally be made through Google Calendar.

## Layers

### `models/`

Defines application-level data structures.

`CalendarEvent` provides a common representation for calendar events and task-like items.

UI code should depend on this model instead of raw Google API, iCal or browser-scraping payloads.

This keeps the interface independent from the underlying integration method.

### `services/`

Owns integrations and external data access.

Examples include:

- Google Calendar iCal
- Google authentication
- Google Tasks
- browser automation
- persistent Chrome session management
- local cache
- Windows startup integration

The UI should not know how any of these systems work internally.

### `services/combined_calendar.py`

Acts as the aggregation layer for calendar-related data.

Different sources may provide different pieces of information.

The combined service converts them into a single list of `CalendarEvent` objects for the rest of the application.

### `controllers/`

Coordinates services and the UI.

Network and external operations run outside the main UI thread so that slow Google responses do not freeze the desktop widget.

The controller emits application-level results and errors rather than exposing external implementation details directly to the UI.

### `ui/components/`

Contains reusable visual components.

Examples:

- month calendar
- upcoming event list
- status information
- lightweight widget controls

Components should optimize for glanceability rather than feature density.

### `ui/behaviors/`

Contains window-specific behaviour that is separate from calendar functionality.

Examples include:

- frameless dragging
- resizing
- lock/unlock position behaviour

### `ui/calendar_widget.py`

The top-level composition layer.

Its responsibilities are intentionally limited to:

- configuring the window
- composing child widgets
- connecting signals
- displaying controller results
- coordinating high-level UI state

External integration logic should not be implemented here.

## Startup Flow

```text
Windows / User launches app
             |
             v
      CalendarWidget starts
             |
             v
        Load cache
             |
             v
Display saved data immediately
             |
             v
      Start background sync
             |
             v
       Fetch fresh data
             |
        +----+----+
        |         |
     Success    Failure
        |         |
        v         v
 Update UI     Keep cache
 Save cache    Show warning status
        |
        v
"Updated just now"

Calendar Data Flow:

Google Calendar / Tasks / Browser
                |
                v
          Service layer
                |
                v
     CombinedCalendarService
                |
                v
       CalendarController
                |
                v
          CalendarEvent[]
                |
                v
        UI Components

Browser Automation:
Desktop Calendar
       |
       v
ensure_calendar_chrome()
       |
       v
Persistent Chrome profile
       |
       v
Remote debugging / CDP
       |
       v
Playwright
       |
       v
Google Calendar web UI

Cache Architecture:
Successful sync
      |
      v
CalendarEvent[]
      |
      v
%LOCALAPPDATA%\DesktopCalendar\cache.json

At the next startup:

cache.json
    |
    v
Widget renders immediately
    |
    v
Fresh sync happens in background

Error Handling

External service failure should degrade gracefully.

Bad behaviour:

Google unavailable
      |
      v
Clear all events
      |
      v
Empty widget

Preferred behaviour:

Google unavailable
      |
      v
Keep cached events
      |
      v
⚠ Showing saved events · Updated 18 min ago

UX Architecture Rules
1. Every permanent UI element has a cost

Users visually process everything that remains on screen.

Do not permanently display information unless it provides regular value.

2. Primary information requires no interaction

Upcoming dates, times and titles should be visible without hover or clicks.

3. Secondary actions may use tooltips

Controls such as:

refresh
lock/unlock
open Google Calendar

can use hover labels because they are not the primary information.

4. Use visual hierarchy instead of excessive bold text

Important information should be distinguishable without making every element visually dominant.

5. Avoid unnecessary notifications and popups

The widget should be quiet.

Background refresh should normally not interrupt the user.

6. Prefer status recognition over status reading

For example:

✓ Updated just now

and:

⚠ Showing saved events

allow the user to understand state from the symbol before reading the full sentence.

7. Rare actions should not dominate the interface

For example, resetting the window position is useful but much less frequent than checking upcoming events.

Always-visible controls should be reserved for actions that justify their visual cost.

Position Behaviour

The widget defaults to a locked position.

🔒

This prevents accidental dragging or resizing.

Users can temporarily unlock it when repositioning is required.

Locking the widget should only prevent drag/resize behaviour. It should not disable normal controls or change window visibility.

Refresh Behaviour

Refresh should happen automatically in the background.

A manual refresh control may also be provided for cases where the user has just changed something in Google Calendar and wants immediate confirmation.

Refresh operations must not freeze the UI.

Google Calendar Management

The desktop application intentionally delegates complex calendar management to Google Calendar.

Desktop Widget
      |
      | Open Google Calendar
      v
Google Calendar Web
      |
      +-- Create
      +-- Edit
      +-- Delete
      +-- Appointment schedules

This avoids duplicating a mature calendar interface and keeps Desktop Calendar focused on its core purpose.

Design Decision Test

Before adding a new feature, ask:

Does this reduce the effort required for the user to understand what is coming up?

If the answer is no, the feature should probably remain outside the always-visible widget UI.



---


# 5. Generate lại `ai_context.txt`


Sau khi Save All:


```powershell
.\export_project.ps1