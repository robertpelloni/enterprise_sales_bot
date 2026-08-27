#!/usr/bin/env python3
"""Fix mobile-buy-btn onclick handlers in all index pages"""

import sys


def fix_mobile_btn(filepath):
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return

    changed = False
    for i, line in enumerate(lines):
        if "mobile-buy-btn" in line and "onclick" not in line:
            # Add onclick handler to scroll to pricing section
            lines[i] = line.replace(
                'class="mobile-buy-btn"',
                "class=\"mobile-buy-btn\" onclick=\"event.preventDefault();document.getElementById('pricing').scrollIntoView({behavior:'smooth',block:'start'})\"",
            )
            changed = True
            print(f"Fixed line {i + 1} in {filepath}")

    if changed:
        try:
            with open(filepath, "w") as f:
                f.writelines(lines)
        except OSError as e:
            print(f"Error writing {filepath}: {e}")
    else:
        print(f"No unfixed mobile-buy-btn found in {filepath}")


if __name__ == "__main__":
    for filepath in sys.argv[1:]:
        fix_mobile_btn(filepath)
