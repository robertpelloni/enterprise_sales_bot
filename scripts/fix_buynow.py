#!/usr/bin/env python3
"""Update buyNow functions to support monthly/yearly selection"""

import sys


def update_buyNow(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return

    # Pattern 1: with plausible analytics
    old1 = """function buyNow(){
                      if(typeof plausible==='function')plausible('Buy Now Click');
                      fetch('/api/v1/billing/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tier:'HYPERNEXUS_PROFESSIONAL_LICENSE',seats:1,success_url:'https://hypernexus.site/success.html',cancel_url:'https://hypernexus.site/#pricing'})})"""

    new1 = """function buyNow(){
                      if(typeof plausible==='function')plausible('Buy Now Click');
                      fetch('/api/v1/billing/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tier:'HYPERNEXUS_PROFESSIONAL_LICENSE',seats:1,price_amount:window.__price_amount||500,interval:window.__pricing_plan==='yearly'?'year':'month',success_url:'https://hypernexus.site/success.html',cancel_url:'https://hypernexus.site/#pricing'})})"""

    # Pattern 2: without plausible analytics
    old2 = """function buyNow(){
                      fetch('/api/v1/billing/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tier:'HYPERNEXUS_PROFESSIONAL_LICENSE',seats:1,success_url:'https://hypernexus.site/success.html',cancel_url:'https://hypernexus.site/#pricing'})})"""

    new2 = """function buyNow(){
                      fetch('/api/v1/billing/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tier:'HYPERNEXUS_PROFESSIONAL_LICENSE',seats:1,price_amount:window.__price_amount||500,interval:window.__pricing_plan==='yearly'?'year':'month',success_url:'https://hypernexus.site/success.html',cancel_url:'https://hypernexus.site/#pricing'})})"""

    changed = False
    if old1 in content:
        content = content.replace(old1, new1)
        changed = True
        print(f"Updated buyNow (with analytics) in {filepath}")

    if old2 in content:
        content = content.replace(old2, new2)
        changed = True
        print(f"Updated buyNow (without analytics) in {filepath}")

    if not changed:
        print(f"No matching buyNow found in {filepath}")

    try:
        with open(filepath, "w") as f:
            f.write(content)
    except OSError as e:
        print(f"Error writing {filepath}: {e}")


if __name__ == "__main__":
    for filepath in sys.argv[1:]:
        update_buyNow(filepath)
