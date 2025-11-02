#!/usr/bin/env python3
"""
Subnet Snap — CIDR Flashcards for Beginners
-------------------------------------------
An Anki-style flashcard game for learning subnet masks the fun way.

Features:
• Focus on CIDR ↔ Mask recall
• Simple scoring (+1 per correct)
• Beginner-friendly pattern hints (e.g., .128, .192, .224, etc.)
• Exit anytime with 'q'
"""

import ipaddress
import random
import os

# --- Data Setup ---
CIDR_TABLE = [
    {"cidr": i, "mask": str(ipaddress.ip_network(f"0.0.0.0/{i}").netmask)}
    for i in range(24, 31)  # start small, just /24–/30 for beginners
]

PATTERN_HINTS = {
    24: ".0 — one full 256-block (Class C)",
    25: ".0, .128 — halves the range (128)",
    26: ".0, .64, .128, .192 — quarters the range (64)",
    27: ".0, .32, .64, .96, .128, .160, .192, .224 — eighths (32)",
    28: "increments of 16 → .0, .16, .32, .48, .64, .80, .96...",
    29: "increments of 8 → .0, .8, .16, .24, .32, ...",
    30: "increments of 4 → .0, .4, .8, .12, .16..."
}


# --- Core Game Logic ---
def show_hint(cidr):
    """Return an intuitive hint for how to visualize the pattern."""
    mask = ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask
    block_size = 2 ** (32 - cidr)
    pattern = PATTERN_HINTS.get(cidr, "")
    return (
        f"💡 Hint for /{cidr}:\n"
        f"   Mask: {mask}\n"
        f"   Block size: {block_size}\n"
        f"   Pattern: {pattern}\n"
        f"   → Each step halves the usable space in the last octet.\n"
    )


def subnet_snap():
    print("=== 🧮 Subnet Snap — CIDR Flashcards for Beginners ===")
    print("Type 'h' for a hint, 'q' to quit anytime.\n")

    score = 0
    total = 0

    while True:
        q = random.choice(CIDR_TABLE)
        direction = random.choice(["cidr_to_mask", "mask_to_cidr"])

        if direction == "cidr_to_mask":
            print(f"\n📘 CIDR: /{q['cidr']}")
            ans = input("👉 What is the subnet mask? ").strip()
            if ans.lower() in ["q", "quit", "exit"]:
                break
            if ans.lower() in ["h", "hint"]:
                print(show_hint(q["cidr"]))
                ans = input("Try again: ").strip()
            if ans == q["mask"]:
                print(f"✅ Correct! /{q['cidr']} = {q['mask']}")
                score += 1
            else:
                print(f"❌ Nope. /{q['cidr']} = {q['mask']}")
                print(show_hint(q["cidr"]))

        else:  # mask_to_cidr
            print(f"\n📗 Subnet Mask: {q['mask']}")
            ans = input("👉 What is the CIDR prefix? (just the number) /").strip()
            if ans.lower() in ["q", "quit", "exit"]:
                break
            if ans.lower() in ["h", "hint"]:
                print(show_hint(q["cidr"]))
                ans = input("Try again (just the number): /").strip()
            if ans == str(q["cidr"]):
                print(f"✅ Correct! {q['mask']} = /{q['cidr']}")
                score += 1
            else:
                print(f"❌ Nope. {q['mask']} = /{q['cidr']}")
                print(show_hint(q["cidr"]))

        total += 1
        if total % 5 == 0:
            print(f"\n🎯 Progress: {score}/{total} correct ({(score/total)*100:.0f}%)")

    print(f"\n🏁 Session complete! Final Score: {score}/{total} ({(score/total)*100 if total else 0:.0f}%)")
    print("💪 Keep practicing until you recognize the patterns instantly!\n")


if __name__ == "__main__":
    subnet_snap()
