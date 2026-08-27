#!/usr/bin/env python3
"""Fix the mobile-buy-btn onclick handler in index.html and indexB.html"""

import sys


def fix_mobile_buy_btn(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return

    # Fix the broken onclick handler - replace double quotes with single quotes inside onclick
    old = 'onclick="event.preventDefault();document.getElementById("pricing").scrollIntoView({behavior:"smooth",block:"start"})"'
    new = "onclick=\"event.preventDefault();document.getElementById('pricing').scrollIntoView({behavior:'smooth',block:'start'})\""

    if old in content:
        content = content.replace(old, new)
        print(f"Fixed mobile-buy-btn in {filepath}")
    else:
        print(f"No broken mobile-buy-btn found in {filepath}")

    try:
        with open(filepath, "w") as f:
            f.write(content)
    except OSError as e:
        print(f"Error writing {filepath}: {e}")


if __name__ == "__main__":
    for filepath in sys.argv[1:]:
        fix_mobile_buy_btn(filepath)
