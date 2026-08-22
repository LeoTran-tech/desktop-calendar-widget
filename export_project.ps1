$output = "ai_context.txt"

if (Test-Path $output) {
    Remove-Item $output
}

$includeFolders = @(
    "controllers",
    "models",
    "services",
    "ui",
    "utils"
)

$includeRootFiles = @(
    "app.py",
    "README.md",
    "ARCHITECTURE.md",
    "RELIABILITY.md",
    "BUILD.md",
    "requirements.txt",
    "export_project.ps1",
    "DesktopCalendar.iss",
    "build_installer.ps1"
)

$allowedExtensions = @(
    ".py",
    ".ps1",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".css",
    ".html",
    ".js",
    ".iss"
)

$excludeNames = @(
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "build",
    "dist",
    "installer_output",

    "BrowserProfiles",
    "ChromeProfile",
    "chrome_profile",
    "google_calendar_profile",
    "calendar-debug-profile",

    "credentials.json",
    "token.json",
    "config.json",

    "cache.json",
    "task_dom_dump.json",

    "project_dump.txt",
    "ai_context.txt"
)

@"
============================================================
DESKTOP CALENDAR - AI PROJECT CONTEXT
============================================================

Generated: $(Get-Date)

============================================================
PRODUCT PURPOSE
============================================================

Desktop Calendar is a lightweight Windows desktop calendar
widget built with PySide6.

Its purpose is to let the user glance at the desktop and
immediately understand what is coming up.

Google Calendar and Google Tasks remain the source of truth.

============================================================
CURRENT DATA ARCHITECTURE
============================================================

1. Google Calendar API
   - events and appointments

2. Google Tasks API
   - dated task data

3. Google Calendar UI scraper
   - supplements recurring-task occurrences / Calendar-visible
     task time information that is not equivalently exposed by
     the Tasks API

The scraper uses Playwright and an app-owned Chromium browser
profile (Edge by default; Chrome and Brave are also supported).

============================================================
FIRST-RUN SETUP
============================================================

Before the normal widget starts:

1. Google OAuth sign-in for Calendar + Tasks APIs
2. Choose Edge / Chrome / Brave
3. Sign in to Google Calendar in the app-owned browser profile
4. Verify Calendar sign-in
5. Mark setup complete

Normal browser work is headless after setup.

============================================================
LOCAL DATA
============================================================

Per-user runtime data lives under:

    %LOCALAPPDATA%\DesktopCalendar\

including:

- token.json
- cache.json
- BrowserProfiles\

Preferences and setup state use Qt QSettings.

Sensitive credentials, OAuth tokens, browser profiles, caches,
generated build output and personal data must never be included
in this AI context or committed to Git.

============================================================
RELIABILITY PRIORITY
============================================================

The Google Calendar UI scraper is a supplementary, inherently
less stable integration.

Future reliability hardening must ensure that scraper failure
cannot silently make the calendar appear complete.

See RELIABILITY.md.

============================================================
PROJECT STRUCTURE
============================================================

"@ | Out-File $output -Encoding UTF8

foreach ($file in $includeRootFiles) {
    if (Test-Path $file) {
        "[FILE] $file" |
        Out-File $output -Append -Encoding UTF8
    }
}

foreach ($folder in $includeFolders) {
    if (-not (Test-Path $folder)) {
        continue
    }

    "[DIR] $folder" |
    Out-File $output -Append -Encoding UTF8

    Get-ChildItem $folder -Recurse |
    Where-Object {
        $item = $_

        -not ($excludeNames | Where-Object {
            $item.FullName -match "\\$([regex]::Escape($_))(\\|$)"
        })
    } |
    ForEach-Object {
        $relative =
            $_.FullName.Substring((Get-Location).Path.Length + 1)

        if ($_.PSIsContainer) {
            "[DIR]  $relative"
        }
        else {
            "[FILE] $relative"
        }
    } |
    Out-File $output -Append -Encoding UTF8
}

function Add-FileToContext {
    param (
        [string]$FilePath
    )

    if (-not (Test-Path $FilePath)) {
        return
    }

    $file = Get-Item $FilePath

    if ($file.Length -gt 200KB) {
        @"

============================================================
FILE: $FilePath
============================================================

[SKIPPED - File larger than 200 KB]

"@ | Out-File $output -Append -Encoding UTF8

        return
    }

    @"

============================================================
FILE: $FilePath
============================================================

"@ | Out-File $output -Append -Encoding UTF8

    Get-Content $FilePath |
    Out-File $output -Append -Encoding UTF8
}

foreach ($file in $includeRootFiles) {
    if (Test-Path $file) {
        $extension =
            [System.IO.Path]::GetExtension($file).ToLower()

        if ($allowedExtensions -contains $extension) {
            Add-FileToContext $file
        }
    }
}

foreach ($folder in $includeFolders) {
    if (-not (Test-Path $folder)) {
        continue
    }

    Get-ChildItem $folder -Recurse -File |
    Where-Object {
        $file = $_

        ($allowedExtensions -contains $file.Extension.ToLower()) -and

        -not ($excludeNames | Where-Object {
            $file.FullName -match "\\$([regex]::Escape($_))(\\|$)"
        })
    } |
    ForEach-Object {
        $relative =
            $_.FullName.Substring((Get-Location).Path.Length + 1)

        Add-FileToContext $relative
    }
}

Write-Host ""
Write-Host "============================================"
Write-Host "AI context generated successfully"
Write-Host "File: $output"
Write-Host "============================================"
