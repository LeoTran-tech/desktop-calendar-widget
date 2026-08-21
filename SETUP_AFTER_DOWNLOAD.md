# Setup After Download

This package intentionally does **not** contain private files from your original project.

Before running it, copy your own local files from the old project into this folder if you already use them:

- `config.json`
- `credentials.json`
- `token.json`

Do not commit those files to Git.

The main additions in this version are:

- multi-monitor-safe window position restore
- Windows system tray icon
- month navigation by mouse wheel (3 months back / 6 months forward)
- 7-day default upcoming view
- user-selectable 3 / 7 / 14 / 30-day upcoming range through tray Settings
- `EventCard` extracted from `upcoming_events.py`
- user preferences stored separately with `QSettings`
- cached last-update time reused correctly when the first online refresh fails
