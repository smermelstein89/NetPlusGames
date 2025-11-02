#!/usr/bin/env python3
"""
Subnet Snap — Smart Learning Path (Level 1)
-------------------------------------------
Level 1 focus: Recognize CIDR <-> Mask for /24–/30 via multiple choice.
- Get 10 correct in a row to level up (saved in subnet_snap_progress.json)
- Press 'h' for a visual hint (block table)
- Wrong answers show the hint automatically and re-queue the card
- Score & streak tracking, exit anytime with 'q'

Next levels can be layered on later using the saved progress.
"""

import ipaddress
import json
import os
import random
import sys
from collections import deque

PROGRESS_FILE = "subnet_snap_progress.json"

LEVEL = 1                # This script implements Level 1 only
TARGET_STREAK = 10       # Promote after this many correct in a row
CHOICES = 4              # multiple-choice options

# ----- Card pool for Level 1: /24.. /30 -----
CIDRS = list(range(24, 31))
CARDS = [{"cidr": c, "mask": str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask)} for c in CIDRS]

# ----- Progress I/O -----
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_level": 1, "best_streak": 0, "high_score": 0}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=2)

# ----- Utilities -----
def block_size_from_cidr(cidr: int) -> int:
    return 2 ** (32 - cidr)

def block_ranges_last_octet(cidr: int):
    """Return list of (start,end) tuples for /24–/30 in the last octet."""
    # For /24, the changing octet is past the 3rd (i.e., 4th octet fully host bits)
    # This is fine: block size 256 → single block 0–255.
    size = block_size_from_cidr(cidr)
    ranges = []
    start = 0
    while start < 256:
        end = min(start + size - 1, 255)
        ranges.append((start, end))
        start += size
    return ranges

def visual_hint(cidr: int) -> str:
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    size = block_size_from_cidr(cidr)
    subs = block_ranges_last_octet(cidr)
    # Show only the first few ranges to keep it readable
    shown = subs[:8]
    ranges_text = "\n  ".join([f"{a:>3}–{b:<3}" for a,b in shown]) + ("  ..." if len(subs) > 8 else "")
    return (
        f"\n💡 Hint for /{cidr}\n"
        f"Mask: {mask}\n"
        f"Changing octet: 4th (last octet)\n"
        f"Block size: {size}\n"
        f"Subnets (last octet ranges):\n  {ranges_text}\n"
        f"Network addresses at the block STARTS: ." +
        ", .".join(str(a) for a,_ in shown[:8]) + (" ..." if len(subs) > 8 else "") + "\n"
    )

def make_choices(correct, pool, direction):
    """
    Build 4 choices containing the correct answer + 3 distractors.
    direction: 'cidr_to_mask' or 'mask_to_cidr'
    """
    others = [c for c in pool if c != correct]
    distractors = random.sample(others, k=min(CHOICES - 1, len(others)))
    picks = [correct] + distractors
    random.shuffle(picks)

    if direction == "cidr_to_mask":
        # Return mask strings
        return [str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask) for c in picks]
    else:
        # Return CIDR numbers (as strings)
        return [str(c) for c in picks]

def ask_mc_question(card, score, streak):
    """
    Ask one multiple-choice question for the given card.
    Returns: (correct: bool, was_hint_used: bool, want_quit: bool)
    """
    cidr = card["cidr"]
    mask = card["mask"]
    direction = random.choice(["cidr_to_mask", "mask_to_cidr"])

    pool_cidrs = CIDRS[:]  # used to generate distractors

    if direction == "cidr_to_mask":
        correct_value = mask
        choices = make_choices(cidr, pool_cidrs, direction)
        prompt = f"\n🟦 CIDR: /{cidr}\nSelect the matching subnet mask:"
    else:
        correct_value = str(cidr)
        choices = make_choices(cidr, pool_cidrs, direction)
        prompt = f"\n🟩 Subnet mask: {mask}\nSelect the matching CIDR (number only):"

    print(prompt)
    for i, opt in enumerate(choices, 1):
        print(f"  {i}. {opt}")

    print("  h. hint   q. quit")
    was_hint = False

    while True:
        ans = input("> ").strip().lower()
        if ans in ("q", "quit", "exit"):
            return False, was_hint, True
        if ans == "h":
            print(visual_hint(cidr))
            was_hint = True
            continue
        if ans.isdigit():
            idx = int(ans)
            if 1 <= idx <= len(choices):
                picked = choices[idx - 1]
                is_correct = (picked == correct_value)
                if is_correct:
                    print("✅ Correct!")
                else:
                    print(f"❌ Incorrect.\nCorrect answer: {correct_value}")
                    # Show the teaching hint automatically
                    print(visual_hint(cidr))
                return is_correct, was_hint, False
        print("Please choose 1-4, 'h' for hint, or 'q' to quit.")

def main():
    progress = load_progress()
    if progress.get("current_level", 1) > 1:
        print("📈 You’ve already cleared Level 1 previously. (Progress loaded)")
    print("=== 🧮 Subnet Snap — Level 1 (/24–/30) ===")
    print("Get 10 correct in a row to level up. 'h' for hint, 'q' to quit.\n")

    deck = deque(CARDS)  # queue of cards; wrong answers get re-queued at front
    random.shuffle(deck)

    score = 0
    streak = 0
    best_streak = progress.get("best_streak", 0)
    high_score = progress.get("high_score", 0)

    while True:
        if not deck:
            # reshuffle the deck if exhausted
            deck = deque(CARDS)
            random.shuffle(deck)

        card = deck.popleft()
        correct, used_hint, want_quit = ask_mc_question(card, score, streak)

        if want_quit:
            break

        if correct:
            score += 1
            streak += 1
            best_streak = max(best_streak, streak)
            print(f"Score: {score}   Streak: {streak}   Best: {best_streak}")
        else:
            streak = 0
            # push the missed card near the front for quick review
            deck.appendleft(card)
            print(f"Score: {score}   Streak reset to 0   Best: {best_streak}")

        # Level up check
        if streak >= TARGET_STREAK:
            print("\n🏆 LEVEL UP! You nailed 10 in a row.")
            progress["current_level"] = max(progress.get("current_level", 1), LEVEL + 1)
            break

    # Save progress
    progress["best_streak"] = max(progress.get("best_streak", 0), best_streak)
    progress["high_score"] = max(progress.get("high_score", 0), score)
    save_progress(progress)

    print("\n=== Session Summary ===")
    print(f"Final Score: {score}")
    print(f"Best Streak (this session): {best_streak}")
    print(f"Level Saved: {progress['current_level']}  | High Score Saved: {progress['high_score']}")
    if progress["current_level"] > 1:
        print("🎉 Next time we can unlock Level 2 (third-octet masks: /16–/23).")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
