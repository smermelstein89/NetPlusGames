#!/usr/bin/env python3
"""
Changing Octet Challenge
------------------------
Subnet Snap mini-game focused on identifying which octet changes
for any given CIDR prefix or subnet mask.

Goal: Train instant recognition of the "changing octet" — the core
reflex behind fast subnetting.
"""

import ipaddress, random, json, os, sys

PROGRESS_FILE = "subnet_snap_progress.json"
TARGET_STREAK = 10

CIDRS = list(range(0, 31))  # /0–/30 (ignore /31+/32)

# ---------- Helpers ----------
def detect_changing_octet(cidr: int) -> int:
    """Return which octet changes (1-based)."""
    mask_bytes = list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    for i, b in enumerate(mask_bytes, 1):
        if b != 255:
            return i
    return 4

def binary_mask_visual(cidr: int) -> str:
    mask_bytes = list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    bits = ["{0:08b}".format(b) for b in mask_bytes]
    return ".".join(bits)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"changing_octet_best_streak": 0}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=2)

def visual_explanation(cidr: int) -> str:
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    binary_mask = binary_mask_visual(cidr)
    changing = detect_changing_octet(cidr)
    return (
        f"\n💡 Explanation:\n"
        f"CIDR: /{cidr}\n"
        f"Mask: {mask}\n"
        f"Binary: {binary_mask}\n"
        f"Changing octet = {changing} ({['1st','2nd','3rd','4th'][changing-1]} octet)\n"
    )

# ---------- Game ----------
def play_changing_octet():
    progress = load_progress()
    best_streak = progress.get("changing_octet_best_streak", 0)
    score = 0
    streak = 0

    print("=== 🧮 Changing Octet Challenge ===")
    print("Type which octet (1–4) changes for the given CIDR or mask.")
    print("Type 'h' for explanation, 'q' to quit.\n")

    while True:
        cidr = random.choice(CIDRS)
        mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
        question_type = random.choice(["cidr", "mask"])

        if question_type == "cidr":
            print(f"📘 CIDR: /{cidr}")
        else:
            print(f"📗 Subnet Mask: {mask}")

        ans = input("👉 Which octet changes (1-4)? ").strip().lower()

        if ans in ("q", "quit", "exit"):
            break
        if ans in ("h", "hint"):
            print(visual_explanation(cidr))
            continue

        if ans.isdigit():
            ans_int = int(ans)
            correct_octet = detect_changing_octet(cidr)
            if ans_int == correct_octet:
                streak += 1
                score += 1
                best_streak = max(best_streak, streak)
                print(f"✅ Correct! Changing octet: {correct_octet}")
                print(f"Streak:{streak}  Score:{score}  Best:{best_streak}\n")
            else:
                print(f"❌ Nope — changing octet is {correct_octet}.")
                print(visual_explanation(cidr))
                streak = 0
                print(f"Score:{score}  Streak reset.  Best:{best_streak}\n")
        else:
            print("Please enter 1–4, 'h' for hint, or 'q' to quit.")

        if streak >= TARGET_STREAK:
            print("\n🏆 YOU WON! 10 correct in a row — Changing Octet Master!")
            break

    # Save progress
    progress["changing_octet_best_streak"] = max(progress.get("changing_octet_best_streak", 0), best_streak)
    save_progress(progress)
    print(f"\n=== Session Summary ===\nScore: {score}  Best Streak: {best_streak}")
    print("Progress saved. Keep training that octet reflex!")

# ---------- Main ----------
if __name__ == "__main__":
    try:
        play_changing_octet()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
