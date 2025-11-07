#!/usr/bin/env python3
"""
Subnet Snap — Smart Learning Path (Level 5, Revised)
----------------------------------------------------
General-purpose subnet fluency drill:
 • Covers /8–/30 (all octet levels)
 • Type-in recall (no multiple choice)
 • Continuous flow like Level 4 (no "press Enter" pauses)
 • Scoring + streak tracking + average time
 • Saves progress to subnet_snap_progress.json
"""

import ipaddress, json, os, random, sys, time
from collections import deque

PROGRESS_FILE = "subnet_snap_progress.json"
LEVEL = 5
TARGET_STREAK = 10

CIDRS = list(range(8, 31))
CARDS = [{"cidr": c, "mask": str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask)} for c in CIDRS]

# ---------- Progress ----------
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

# ---------- Hint ----------
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
    div = [1, 256**3, 256**2, 256, 1][octet]
    step = max(1, block // div)
    sample = [f"{a}–{a+step-1}" for a in range(0, min(256, 8*step), step)]
    return (
        f"\n💡 Hint for /{cidr}\n"
        f"Mask: {mask}\n"
        f"Changing octet: {octet}\n"
        f"Block size: {step}\n"
        f"Subnet ranges (octet {octet}): " + ", ".join(sample) + " ..."
    )

# ---------- Question ----------
def ask_typed_question(card):
    cidr, mask = card["cidr"], card["mask"]
    direction = random.choice(["cidr_to_mask", "mask_to_cidr"])
    start = time.time()
    used_hint = False

    if direction == "cidr_to_mask":
        print(f"\n🟦 CIDR: /{cidr}")
        ans = input("👉 Enter subnet mask (or 'h' for hint, 'q' to quit): ").strip()
        if ans.lower() in ("q", "quit", "exit"):
            return None, False, 0.0, True
        if ans.lower() in ("h", "hint"):
            print(visual_hint(cidr))
            used_hint = True
            ans = input("Try again: ").strip()
        ok = (ans == mask)
        if ok:
            print("✅ Correct!")
        else:
            print(f"❌ Wrong — correct mask: {mask}")
            print(visual_hint(cidr))
    else:
        print(f"\n🟩 Subnet mask: {mask}")
        ans = input("👉 Enter CIDR prefix (number only, 'h' for hint, 'q' to quit): /").strip()
        if ans.lower() in ("q", "quit", "exit"):
            return None, False, 0.0, True
        if ans.lower() in ("h", "hint"):
            print(visual_hint(cidr))
            used_hint = True
            ans = input("Try again (number only): /").strip()
        ok = (ans == str(cidr))
        if ok:
            print("✅ Correct!")
        else:
            print(f"❌ Wrong — correct CIDR: /{cidr}")
            print(visual_hint(cidr))

    elapsed = time.time() - start
    return ok, used_hint, elapsed, False

# ---------- Main ----------
def main():
    prog = load_progress()
    if prog.get("current_level", 1) > 5:
        print("📈 You already cleared Level 5 previously. (Progress loaded)")
    print("=== 🧮 Subnet Snap — Level 5 (Revised) ===")
    print("Type answers directly. Get 10 correct in a row to finish.\n")

    deck = deque(CARDS)
    random.shuffle(deck)
    score = 0
    streak = 0
    best_streak = prog.get("best_streak", 0)
    high_score = prog.get("high_score", 0)
    total_time = 0.0
    answered = 0

    while True:
        if not deck:
            deck = deque(CARDS)
            random.shuffle(deck)
        card = deck.popleft()
        ok, hint, elapsed, quit_now = ask_typed_question(card)
        if quit_now:
            break
        answered += 1
        total_time += elapsed
        avg_time = total_time / answered

        if ok:
            score += 1
            streak += 1
            best_streak = max(best_streak, streak)
            print(f"Score:{score}  Streak:{streak}  Best:{best_streak}  ⏱Avg:{avg_time:.1f}s")
        else:
            streak = 0
            deck.appendleft(card)
            print(f"Score:{score}  Streak reset  Best:{best_streak}  ⏱Avg:{avg_time:.1f}s")

        if streak >= TARGET_STREAK:
            print("\n🏆 LEVEL UP! You nailed 10 in a row at Level 5!")
            prog["current_level"] = max(prog.get("current_level", 5), LEVEL + 1)
            break

    prog["best_streak"] = max(prog.get("best_streak", 0), best_streak)
    prog["high_score"] = max(prog.get("high_score", 0), score)
    save_progress(prog)

    print("\n=== Session Summary ===")
    print(f"Final Score:{score}  Best Streak:{best_streak}")
    print(f"Average Time:{(total_time/answered if answered else 0):.1f}s")
    print(f"Saved Level:{prog['current_level']}  | High Score:{prog['high_score']}")
    if prog["current_level"] > 5:
        print("🎉 Next time you can unlock Level 6 (/0–/8 supernets).")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
