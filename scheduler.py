"""
Scheduler for AI for Nonprofits automation.

Usage:
  python scheduler.py                    # Run once now
  python scheduler.py --daemon           # Run in continuous loop (checks every N hours)
  python scheduler.py --once             # Run once and exit (same as no flag)

Daemon mode runs the pipeline every INTERVAL_HOURS hours with jitter.
"""

import os
import sys
import time
import random
from datetime import datetime

from main import run_pipeline

INTERVAL_HOURS = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "24"))
JITTER_MINUTES = int(os.getenv("SCHEDULE_JITTER_MINUTES", "30"))


def run_daemon():
    print(f"[scheduler] Daemon mode: running every ~{INTERVAL_HOURS}h (±{JITTER_MINUTES}min jitter)")
    while True:
        run_pipeline()
        jitter = random.uniform(-JITTER_MINUTES * 60, JITTER_MINUTES * 60)
        sleep_seconds = (INTERVAL_HOURS * 3600) + jitter
        next_run = datetime.now().timestamp() + sleep_seconds
        next_str = datetime.fromtimestamp(next_run).strftime("%Y-%m-%d %H:%M")
        print(f"[scheduler] Next run at ~{next_str} (sleeping {sleep_seconds/3600:.1f}h)")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        run_daemon()
    else:
        run_pipeline()
