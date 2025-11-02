#!/usr/bin/env python3
"""
Subnet Snap — Smart Learning Path (Level 5)
-------------------------------------------
General-purpose subnet fluency drill:
 • Covers /8–/30  (all octet levels)
 • Type-in recall (no multiple choice)
 • Scoring + streak tracking
 • Optional hints showing which octet changes
 • Saves progress to subnet_snap_progress.json
"""

import ipaddress, json, os, random, sys, time
from collections import deque

PROGRESS_FILE = "subnet_snap_progress.json"
LEVEL = 5
TARGET_STREAK = 10

# ----- Pool: /8 .. /30 -----
CIDRS = list(range(8, 31))
CARDS = [{"cidr": c, "mask": str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask)} for c in CIDRS]

# ----- Progress helpers -----
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_level": 5, "best_streak": 0, "high_score": 0}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=2)

# ----- Hint builder -----
def detect_changing_octet(cidr: int) -> int:
    mask_bytes = list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    for i, b in enumerate(mask_bytes, 1):
        if b != 255:
            return i
    return 4

def block_size_from_cidr(cidr: int) -> int:
    return 2 ** (32 - cidr)

def visual_hint(cidr: int) -> str:
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    octet = detect_changing_octet(cidr)
    block = block_size_from_cidr(cidr)
    div = [1, 256, 256**2, 256**3][4 - octet]
    step = block // div
    sample = [f"{a}–{a+step-1}" for a in range(0, min(256, 8*step), step)]
    return (
        f"\n💡 Hint for /{cidr}\n"
        f"Mask: {mask}\n"
        f"Changing octet: {octet}\n"
        f"Block size: {step}\n"
        f"Subnet ranges (octet {octet}): " + ", ".join(sample) + " ..."
    )

# ----- Game logic -----
def ask_typed_question(card):
    cidr, mask = card["cidr"], card["mask"]
    direction = random.choice(["cidr_to_mask", "mask_to_cidr"])
    start = time.time()
    was_hint = False
    if direction == "cidr_to_mask":
        print(f"\n🟦 CIDR: /{cidr}")
        ans = input("👉 Enter subnet mask (or 'h' for hint): ").strip()
        if ans.lower() in ["h", "hint"]:
            print(visual_hint(cidr))
            was_hint = True
            ans = input("Try again: ").strip()
        correct = ans == mask
        if correct:
            print("✅ Correct!")
        else:
            print(f"❌ Wrong — correct mask: {mask}")
            print(visual_hint(cidr))
    else:
        print(f"\n🟩 Subnet mask: {mask}")
        ans = input("👉 Enter CIDR prefix (number only, or 'h' for hint): /").strip()
        if ans.lower() in ["h", "hint"]:
            print(visual_hint(cidr))
            was_hint = True
            ans = input("Try again (number only): /").strip()
        correct = ans == str(cidr)
        if correct:
            print("✅ Correct!")
        else:
            print(f"❌ Wrong — correct CIDR: /{cidr}")
            print(visual_hint(cidr))
    elapsed = time.time() - start
    return correct, was_hint, elapsed

# ----- Main -----
def main():
    prog = load_progress()
    if prog.get("current_level", 1) > 5:
        print("📈 You already cleared Level 5. (Progress loaded)")
    print("=== 🧮 Subnet Snap — Level 5 (Mastery Mode) ===")
    print("Type answers directly. Get 10 correct in a row to finish the training.\n")

    deck = deque(CARDS)
    random.shuffle(deck)
    score = 0
    streak = 0
    best_streak = prog.get("best_streak", 0)
    high_score = prog.get("high_score", 0)
    total_time = 0

    while True:
        if not deck:
            deck = deque(CARDS)
            random.shuffle(deck)
        card = deck.popleft()
        correct, hint, elapsed = ask_typed_question(card)
        if not correct:
            streak = 0
            deck.appendleft(card)
        else:
            score += 1
            streak += 1
            best_streak = max(best_streak, streak)
        total_time += elapsed
        avg_time = total_time / max(score, 1)
        print(f"Score: {score}   Streak: {streak}   Best: {best_streak}   ⏱ Avg: {avg_time:.1f}s")
        if streak >= TARGET_STREAK:
            print("\n🏆 CONGRATULATIONS! You’ve mastered Level 5 Subnet Fluency!")
            prog["current_level"] = max(prog.get("current_level", 5), LEVEL + 1)
            break
        cmd = input("(Press Enter to continue or 'q' to quit) > ").strip().lower()
        if cmd in ("q", "quit", "exit"):
            break

    prog["best_streak"] = max(prog.get("best_streak", 0), best_streak)
    prog["high_score"] = max(prog.get("high_score", 0), score)
    save_progress(prog)

    print("\n=== Session Summary ===")
    print(f"Final Score: {score}   Best Streak: {best_streak}")
    print(f"Average Time Per Answer: {avg_time:.1f}s")
    print(f"Progress Saved — Level: {prog['current_level']}   High Score: {prog['high_score']}")
    print("🎯 You’re now ready for the full 7-Second Subnetting speed game!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
