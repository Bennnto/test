# Auto-Commit

A lightweight Python utility that watches a git repository for changes and
automatically stages and commits them on a configurable timer.

## Requirements

- Python 3.10+
- Git (available on `$PATH`)

No third-party packages are required — the script uses the Python standard
library only.

## Usage

```bash
# Commit every 60 seconds (default) in the current directory
python auto_commit.py

# Commit every 5 minutes
python auto_commit.py --interval 300

# Target a specific repository
python auto_commit.py --repo /path/to/repo

# Custom commit-message prefix
python auto_commit.py --message "auto: save progress"

# Run once and exit (handy for cron jobs)
python auto_commit.py --once
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--interval SECONDS` | `60` | Seconds between commit checks |
| `--repo PATH` | `.` | Path to the git repository |
| `--message MSG` | `"auto commit"` | Commit-message prefix |
| `--once` | — | Perform one cycle then exit |

## Commit message format

Every automatic commit message looks like:

```
auto commit [2024-06-01 12:34:56 UTC]
```

The UTC timestamp makes it easy to trace when a snapshot was taken.

## Stopping the daemon

Send `SIGINT` (Ctrl-C) or `SIGTERM` to the process and it will finish the
current cycle and exit cleanly.

## Running as a cron job

```cron
# Every 10 minutes, auto-commit the project
*/10 * * * * cd /path/to/repo && python auto_commit.py --once
```