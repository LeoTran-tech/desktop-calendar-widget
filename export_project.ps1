$output = "ai_context.txt"

# Xóa file cũ
if (Test-Path $output) {
    Remove-Item $output
}

# ============================================
# FOLDERS AI CẦN ĐỌC
# ============================================

$includeFolders = @(
    "controllers",
    "models",
    "services",
    "ui",
    "utils"
)

# ============================================
# FILE Ở ROOT AI CẦN ĐỌC
# ============================================

$includeRootFiles = @(
    "app.py",
    "config.py",
    "config.example.json",
    "README.md",
    "ARCHITECTURE.md",
    "requirements.txt",
    "export_project.ps1"
)

# ============================================
# EXTENSIONS ĐƯỢC PHÉP
# ============================================

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
    ".js"
)

# ============================================
# FILE / FOLDER KHÔNG BAO GIỜ ĐƯA CHO AI
# ============================================

$excludeNames = @(
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".idea",
    ".vscode",

    "chrome_profile",
    "google_calendar_profile",
    "ChromeProfile",
    "calendar-debug-profile",

    "credentials.json",
    "token.json",
    "config.json",

    "cache.json",
    "task_dom_dump.json",

    "project_dump.txt",
    "ai_context.txt"
)

# ============================================
# HEADER
# ============================================

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

The product is NOT intended to replace Google Calendar.

Its primary purpose is:

    Open computer
        ->
    glance at the desktop
        ->
    immediately understand what is coming up

The widget should minimize the amount of attention, reading,
clicking and interaction required from the user.

Google Calendar remains the source of truth for creating,
editing and deleting calendar data.

The desktop widget mainly provides a fast, glanceable,
read-oriented view of upcoming commitments.

============================================================
PRODUCT / UX PRINCIPLES
============================================================

1. MINIMIZE COGNITIVE LOAD

The user should understand the important information within
a few seconds.

Important information:
- date
- time
- event/task title
- whether the displayed data is up to date

Avoid unnecessary text, controls and visual noise.


2. GLANCEABILITY FIRST

Primary information must be visible without requiring clicks,
hovering, opening menus or navigating through screens.

Hover text is appropriate only for secondary controls.


3. DO NOT REBUILD GOOGLE CALENDAR

Complex calendar management such as creating, editing,
deleting events and appointment schedules belongs in
Google Calendar.

The widget can open Google Calendar when the user needs
those capabilities.


4. QUIET DESKTOP BEHAVIOUR

The application should behave like a desktop widget:

- start automatically with Windows
- remain visible on the desktop
- not steal focus unnecessarily
- not open visible browser windows for background work
- refresh silently
- default to a locked position


5. FAST STARTUP

Cached events/tasks should be displayed immediately when the
application starts.

Network synchronisation happens afterwards in the background.


6. GRACEFUL FAILURE

Network, Google Calendar or scraper failures should not make
the widget suddenly empty.

If fresh data cannot be retrieved, continue displaying the
last successful cached data and show a lightweight status such
as:

    Warning: Showing saved events - Updated 12 min ago


7. SOURCE OF TRUTH

Google Calendar / Google Tasks are the authoritative data
sources.

Local cache exists only to improve startup speed and
resilience. It is not an independent calendar database.


8. LOW-EFFORT STATUS

Synchronisation state should be understandable at a glance.

Examples:

    Updated just now
    Updated 3 min ago
    Warning: Showing saved events - Updated 18 min ago

The user should not need to inspect logs or terminals.


9. BACKGROUND IMPLEMENTATION SHOULD BE INVISIBLE

OAuth, Chrome debugging, Playwright scraping, caching and
network requests are implementation details.

Normal users should not have to manually start Chrome,
run PowerShell commands, or understand these systems.


10. KEEP THE PRODUCT SMALL

Before adding a feature, ask:

    Does this reduce the effort required to understand
    what is coming up?

If not, it probably does not belong in the always-visible
widget UI.

============================================================
AI COLLABORATION GUIDANCE
============================================================

When suggesting changes:

- preserve the glanceable-widget philosophy
- prefer simpler UX over additional features
- avoid turning the app into a full calendar client
- keep network/browser work outside the UI thread
- preserve cached data when refresh fails
- avoid unnecessary popups
- avoid adding permanently visible controls for rare actions
- treat Google Calendar as the management interface
- prioritize reliability at Windows startup

Sensitive credentials, browser profiles, caches and generated
files must never be included in this context or committed to Git.

"@ | Out-File $output -Encoding UTF8


# ============================================
# PROJECT STRUCTURE
# ============================================

@"

============================================================
PROJECT STRUCTURE
============================================================

"@ | Out-File $output -Append -Encoding UTF8


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


# ============================================
# FUNCTION ĐỂ DUMP FILE
# ============================================

function Add-FileToContext {

    param (
        [string]$FilePath
    )

    if (-not (Test-Path $FilePath)) {
        return
    }

    $file = Get-Item $FilePath

    # Không đọc file quá lớn (> 200 KB)
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


# ============================================
# ROOT FILE CONTENTS
# ============================================

foreach ($file in $includeRootFiles) {

    if (Test-Path $file) {

        $extension =
            [System.IO.Path]::GetExtension($file).ToLower()

        if ($allowedExtensions -contains $extension) {
            Add-FileToContext $file
        }
    }
}


# ============================================
# SOURCE CODE CONTENTS
# ============================================

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