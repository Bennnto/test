#!/usr/bin/env python3
"""
auto_commit.py — Timer-based automatic git commit application.

Watches a git repository for uncommitted changes and automatically
stages and commits them on a configurable interval.

Usage:
    python auto_commit.py [--interval SECONDS] [--repo PATH] [--message MSG]

Examples:
    python auto_commit.py                         # commit every 60 s
    python auto_commit.py --interval 300          # commit every 5 min
    python auto_commit.py --repo /path/to/repo    # target a different repo
    python auto_commit.py --message "auto: save"  # custom commit message prefix
"""

import argparse
import logging
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_stop_requested = False


def _handle_signal(signum, frame):  # noqa: ANN001
    global _stop_requested
    logger.info("Received signal %s — stopping after current cycle.", signum)
    _stop_requested = True


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repo(path: Path) -> bool:
    """Return True if *path* is inside a git repository."""
    result = _run(["git", "rev-parse", "--git-dir"], cwd=path)
    return result.returncode == 0


def has_changes(repo: Path) -> bool:
    """Return True if the working tree or index has any changes."""
    result = _run(["git", "status", "--porcelain"], cwd=repo)
    return bool(result.stdout.strip())


def stage_all(repo: Path) -> bool:
    """Stage all changes.  Returns True on success."""
    result = _run(["git", "add", "--all"], cwd=repo)
    if result.returncode != 0:
        logger.error("git add failed: %s", result.stderr.strip())
        return False
    return True


def commit(repo: Path, message: str) -> bool:
    """Create a commit.  Returns True on success."""
    result = _run(["git", "commit", "-m", message], cwd=repo)
    if result.returncode != 0:
        logger.error("git commit failed: %s", result.stderr.strip())
        return False
    first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    logger.info("Committed: %s", first_line)
    return True


def build_message(prefix: str) -> str:
    """Build a commit message that includes a UTC timestamp."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"{prefix} [{ts}]"


def run_cycle(repo: Path, message_prefix: str) -> None:
    """Check for changes and commit them if any are found."""
    if not has_changes(repo):
        logger.debug("No changes detected.")
        return

    logger.info("Changes detected — staging and committing …")
    if not stage_all(repo):
        return

    message = build_message(message_prefix)
    commit(repo, message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automatically commit changes in a git repo on a timer.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Seconds between commit checks (default: 60).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        metavar="PATH",
        help="Path to the git repository (default: current directory).",
    )
    parser.add_argument(
        "--message",
        default="auto commit",
        metavar="MSG",
        help='Commit message prefix (default: "auto commit").',
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single commit cycle and exit (useful for testing/cron).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    repo = args.repo.resolve()
    if not repo.is_dir():
        logger.error("Repository path does not exist: %s", repo)
        return 1

    if not is_git_repo(repo):
        logger.error("Not a git repository: %s", repo)
        return 1

    if args.interval <= 0:
        logger.error("--interval must be a positive integer.")
        return 1

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Auto-commit started  repo=%s  interval=%ds", repo, args.interval)

    if args.once:
        run_cycle(repo, args.message)
        return 0

    while not _stop_requested:
        run_cycle(repo, args.message)
        # Sleep in short slices so signals are handled promptly.
        for _ in range(args.interval):
            if _stop_requested:
                break
            time.sleep(1)

    logger.info("Auto-commit stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
