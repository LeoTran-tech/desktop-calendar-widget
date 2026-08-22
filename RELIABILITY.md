# Reliability Strategy

## Goal

The goal is not to claim that a third-party web scraper can run forever without maintenance.

The goal is stronger in the way that matters to the user:

> A scraper failure must never silently make Desktop Calendar look complete when recurring-task data is no longer trustworthy.

## Threat Model

The recurring-task scraper can fail because of:

- Google Calendar DOM changes
- accessibility-label/text-format changes
- Calendar redesigns
- lazy rendering or viewport changes
- browser/CDP startup failures
- Playwright/CDP timeouts
- Google sign-in expiry
- account/session changes
- network failures
- unexpected zero-result parsing
- partial month rendering

Official Calendar and Tasks APIs have a different and generally lower integration risk.

## Current State

Current strengths:

- APIs and scraper are separate services
- scraper exceptions do not have to erase API data
- a local cache is shown immediately at startup
- browser sign-in is explicit during first-run setup
- browser profiles are isolated from the user's normal profile
- scraper uses semantic/accessibility-oriented DOM information rather than generated CSS classes
- browser viewport and timeouts are configured to reduce incomplete rendering

Current reliability gap:

- source health is not yet represented independently end-to-end
- a refresh can appear recent even if the scraper failed
- combined cache is not yet source-aware
- an unexpected scraper result of zero tasks is not yet treated as suspicious based on history

## Required Hardening

### 1. Per-source health

Track separately:

```text
Calendar API
Tasks API
Recurring-task scraper
```

Each source should have:

- state: `healthy`, `failed`, `suspicious`, `auth_required`
- last attempt time
- last successful time
- last error
- item count

### 2. Never silently convert scraper failure into valid empty data

These situations are different:

```text
Scraper successfully verified that there are zero tasks
```

and:

```text
Scraper could not verify task data
```

The second must never be represented as an ordinary empty list.

### 3. Separate last-known-good scraper cache

Persist scraper-derived task data independently.

If scraper refresh fails:

- keep displaying the last known-good recurring-task data
- keep API data fresh
- mark scraper data as stale/unverified
- do not overwrite good scraper cache with an empty/failed result

### 4. Anomaly detection

Examples that should become `suspicious` rather than immediate truth:

- scraper previously returned recurring tasks and suddenly returns zero
- a known recurring series disappears unexpectedly
- parsed task count drops dramatically between adjacent refreshes
- Calendar page loads but expected task structure is absent
- multiple months all produce zero parseable task structures despite historical data

Anomaly detection should be conservative: it should warn rather than invent data.

### 5. Explicit UI status

Healthy:

```text
Updated just now
```

Partial degradation:

```text
⚠ Recurring tasks not verified · Events updated just now
```

Browser authentication expired:

```text
⚠ Google Calendar sign-in required
```

DOM/parser incompatibility suspected:

```text
⚠ Recurring-task sync may be incompatible
Saved recurring tasks are still shown
```

### 6. Escalation

Suggested escalation:

- first transient failure: retry silently
- repeated failure: visible warning
- authentication failure: direct sign-in action
- parser/DOM anomaly: persistent warning until a successful verified scrape occurs

### 7. Logging

Write a rotating local diagnostic log outside the installation directory.

Log:

- source start/end times
- item counts
- browser selected
- Calendar authentication state
- scraper parser health
- exceptions/timeouts
- cache fallback decisions

Never log OAuth tokens, cookies or sensitive browser-profile content.

### 8. Atomic cache writes

Write cache to a temporary file and atomically replace the previous cache only after serialization succeeds.

A crash or forced shutdown must not corrupt the last known-good dataset.

### 9. Source isolation

A scraper timeout must not prevent fresh Calendar API data from becoming available.

Long term, source jobs should be independently timed/observed and merged through a result object rather than one source blocking the entire refresh chain.

### 10. Self-test

The scraper should verify structural assumptions, for example:

- current URL is authenticated Google Calendar
- month view loaded
- expected Calendar DOM structure exists
- task text format is recognized when task elements are present

Failure of a structural assumption is a health failure, not a legitimate zero-task result.

## Reliability Invariant

The application should maintain this invariant:

> Incomplete or unverified fresh data must never overwrite verified useful data without an explicit warning.

This is the core rule for long-term safety.

## Planned Implementation Order

1. Introduce structured `SourceHealth` / `SyncResult`
2. Add separate scraper cache
3. Preserve last-known-good scraper tasks on failure
4. Add zero-result and structural anomaly detection
5. Update widget status to reflect partial health
6. Add retry/backoff policy
7. Add local rotating logs
8. Add atomic cache writes
9. Add automated failure-mode tests
10. Only then treat the installer build as release-ready
