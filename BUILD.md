# Build and Release

## Development Build

From the project root:

```powershell
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --console `
    --name DesktopCalendar `
    --collect-all playwright `
    --add-data "credentials.json:." `
    app.py
```

Use `--console` while diagnosing startup, OAuth, browser or scraper issues.

Run:

```powershell
.\dist\DesktopCalendar\DesktopCalendar.exe
```

## Release Build

After testing is complete:

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

Output:

```text
dist\DesktopCalendar\
```

## Clean-Install Test

Before release, test the executable as a new user.

Back up/remove test runtime data and QSettings, then verify:

1. first-run setup appears
2. Google OAuth completes
3. Edge/Chrome/Brave selection works
4. browser Calendar sign-in is verified
5. setup completes
6. widget starts
7. Calendar events/appointments appear
8. Tasks API tasks appear
9. scraper-enriched recurring tasks appear
10. restarting does not repeat setup
11. normal operation does not show a visible browser
12. refresh remains responsive

## Installer

The Inno Setup script packages:

```text
dist\DesktopCalendar\*
```

into:

```text
DesktopCalendarSetup.exe
```

The installer should not contain:

- `token.json`
- browser profiles
- cache files
- personal test data

## OAuth Distribution

A local/test OAuth configuration may require manually registered test users.

For public distribution, configure the Google OAuth application appropriately for external production users and complete any Google verification required for the Calendar/Tasks scopes before advertising the installer publicly.

## Release Gate

Do not consider the application release-ready until the reliability work in `RELIABILITY.md` has been implemented and tested against:

- network failure
- browser missing
- browser logged out
- CDP timeout
- scraper parser failure
- unexpected zero scraped tasks
- stale cache
- forced process termination during cache write
