#!/usr/bin/env python3
"""
run_outreach.py — Orchestrator for the HyperNexus outreach automation suite.

Runs the full outreach pipeline:
  1. Initial top-100 outreach (rate-limited, 30/hour)
  2. Targeted CTO pitches from the DB
  3. Due follow-ups (day 5/10/15 schedule)

Usage:
  python run_outreach.py                # run everything
  python run_outreach.py --initial      # only initial top-100 outreach
  python run_outreach.py --targeted     # only CTO pitches
  python run_outreach.py --followups    # only due follow-ups
  python run_outreach.py --dry-run      # preview everything without sending
"""

import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, extra=None):
    """Run an outreach script with optional extra args."""
    cmd = [sys.executable, os.path.join(HERE, script)]
    if extra:
        cmd.extend(extra)
    print(f"\n{'='*60}\n▶ Running: {' '.join(cmd)}\n{'='*60}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    extra = ["--dry-run"] if dry_run else []

    only = None
    for flag in ("--initial", "--targeted", "--followups"):
        if flag in args:
            only = flag
            break

    rc = 0
    if only in (None, "--initial"):
        rc |= run("outreach_top100.py", extra)
    if only in (None, "--targeted"):
        rc |= run("outreach_targeted.py", extra)
    if only in (None, "--followups"):
        rc |= run("outreach_followup.py", extra)

    if only is None and not dry_run:
        print("\n✅ Full outreach cycle complete.")
        print("Next cycle: run this again tomorrow (follow-ups will handle Day 5/10/15).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
