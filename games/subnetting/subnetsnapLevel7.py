#!/usr/bin/env python3
"""
Subnet Snap — Smart Learning Path (Level 7: Final Boss)
-------------------------------------------------------
All CIDRs /0–/30 mixed.

Adaptive phases:
  • Phase A: Multiple choice (get 10 correct in a row to advance)
  • Phase B: Type-in mastery (get 10 correct in a row to win)

Features:
  • Smart visual hints (changing octet, block size, sample ranges)
  • Progress saved to subnet_snap_progress.json
  • Score + streak tracking, avg time (Phase B)

Author: You + ChatGPT
"""

import ipaddress, json, os, random, sys, time
from collections import deque

PROGRESS_FILE = "subnet_snap_progress.json"

LEVEL = 7
TARGET_STREAK = 10
CHOICES = 4

# Pool: /0..30 (exclude /31, /32 since they’re special cases in host math)
CIDRS = list(range(0, 31))
CARDS = [{"cidr": c, "mask": str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask)} for c in CIDRS]

# ---------- Progress ----------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_level": LEVEL, "best_streak": 0, "high_score": 0, "level7_phase_cleared": False}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=2)

# ---------- Helpers ----------
def detect_changing_octet(cidr: int) -> int:
    """Return which octet (1..4) first differs from 255 in the mask."""
    mask_bytes = list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    for i, b in enumerate(mask_bytes, 1):
        if b != 255:
            return i
    return 4

def block_size_from_cidr(cidr: int) -> int:
    """Block size in addresses across whole 32-bit space."""
    return 2 ** (32 - cidr)

def per_octet_step(cidr: int, changing_octet: int) -> int:
    """
    Convert the global block size to the step within the changing octet.
    Example:
      /27 → changing_octet=4 → step = 32
      /19 → changing_octet=3 → step = 32
      /10 → changing_octet=2 → step = 64
      /3  → changing_octet=1 → step = 32
    """
    global_block = block_size_from_cidr(cidr)
    # Divide out the lower octets (to isolate the step within the changing octet)
    divisor = [1, 256**3, 256**2, 256, 1][changing_octet]  # index by octet; 1->256^3 etc.
    step = max(1, global_block // divisor)
    return min(step, 256)

def sample_ranges_for_octet(step: int, samples: int = 8):
    out = []
    start = 0
    for _ in range(samples):
        end = min(start + step - 1, 255)
        out.append(f"{start}–{end}")
        start += step
        if start > 255:
            break
    return out

def visual_hint(cidr: int) -> str:
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    octet = detect_changing_octet(cidr)
    step = per_octet_step(cidr, octet)
    ranges = sample_ranges_for_octet(step, samples=8)
    return (
        f"\n💡 Hint for /{cidr}\n"
        f"Mask: {mask}\n"
        f"Changing octet: {octet}\n"
        f"Block size in changing octet: {step}\n"
        f"Subnet ranges (octet {octet}): " + ", ".join(ranges) + (" ..." if ranges and ranges[-1] != "255–255" else "")
    )

def make_choices(correct_cidr: int, pool, direction: str):
    others = [c for c in pool if c != correct_cidr]
    distractors = random.sample(others, k=min(CHOICES - 1, len(others)))
    picks = [correct_cidr] + distractors
    random.shuffle(picks)
    if direction == "cidr_to_mask":
        return [str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask) for c in picks]
    else:
        return [str(c) for c in picks]

# ---------- Phase A (Multiple Choice) ----------
def ask_mc_question(card):
    cidr, mask = card["cidr"], card["mask"]
    direction = random.choice(["cidr_to_mask", "mask_to_cidr"])

    if direction == "cidr_to_mask":
        correct_value = mask
        choices = make_choices(cidr, CIDRS, direction)
        prompt = f"\n🟦 CIDR: /{cidr}\nSelect the matching subnet mask:"
    else:
        correct_value = str(cidr)
        choices = make_choices(cidr, CIDRS, direction)
        prompt = f"\n🟩 Subnet mask: {mask}\nSelect the matching CIDR (number only):"

    print(prompt)
    for i, opt in enumerate(choices, 1):
        print(f"  {i}. {opt}")
    print("  h. hint   q. quit")

    while True:
        ans = input("> ").strip().lower()
        if ans in ("q", "quit", "exit"):
            return None, True  # (correct=None, quit=True)
        if ans == "h":
            print(visual_hint(cidr))
            continue
        if ans.isdigit():
            idx = int(ans)
            if 1 <= idx <= len(choices):
                picked = choices[idx - 1]
                ok = (picked == correct_value)
                if ok:
                    print("✅ Correct!")
                else:
                    print(f"❌ Incorrect.\nCorrect answer: {correct_value}")
                    print(visual_hint(cidr))
                return ok, False
        print("Choose 1-4, 'h', or 'q'.")

def run_phase_a():
    print("\n— Phase A: Multiple Choice Warm-up (all CIDRs /0–/30).")
    print(f"Get {TARGET_STREAK} correct in a row to advance. 'h' for hint, 'q' to quit.")
    deck = deque(CARDS)
    random.shuffle(deck)
    streak = 0
    score = 0

    while True:
        if not deck:
            deck = deque(CARDS)
            random.shuffle(deck)
        card = deck.popleft()
        result, quit_now = ask_mc_question(card)
        if quit_now:
            return False, score  # didn’t finish phase A
        if result:
            score += 1
            streak += 1
            print(f"Streak: {streak}   Score: {score}")
        else:
            streak = 0
            deck.appendleft(card)
            print(f"Streak reset. Score: {score}")
        if streak >= TARGET_STREAK:
            print("\n🏆 Phase A complete! Onto Phase B: typed mastery.\n")
            return True, score

# ---------- Phase B (Type-in Mastery) ----------
def ask_typed_question(card):
    cidr, mask = card["cidr"], card["mask"]
    direction = random.choice(["cidr_to_mask", "mask_to_cidr"])
    start = time.time()
    used_hint = False

    if direction == "cidr_to_mask":
        print(f"\n🟦 CIDR: /{cidr}")
        ans = input("👉 Enter subnet mask (or 'h' for hint, 'q' to quit): ").strip()
        if ans.lower() in ("q", "quit", "exit"):
            return None, used_hint, 0.0, True
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
        ans = input("👉 Enter CIDR prefix (number only; 'h' for hint, 'q' to quit): /").strip()
        if ans.lower() in ("q", "quit", "exit"):
            return None, used_hint, 0.0, True
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

def run_phase_b():
    print("\n— Phase B: Typed Mastery (all CIDRs /0–/30).")
    print(f"Get {TARGET_STREAK} typed answers correct in a row to win. 'h' for hint, 'q' to quit.")
    deck = deque(CARDS)
    random.shuffle(deck)
    streak = 0
    score = 0
    total_time = 0.0
    answered = 0

    while True:
        if not deck:
            deck = deque(CARDS)
            random.shuffle(deck)
        card = deck.popleft()
        ok, used_hint, elapsed, quit_now = ask_typed_question(card)
        if quit_now:
            return False, score, streak, 0.0 if answered == 0 else total_time / answered
        answered += 1
        total_time += elapsed

        if ok:
            score += 1
            streak += 1
            print(f"Streak: {streak}   Score: {score}   ⏱ Avg: {total_time/answered:.1f}s")
        else:
            streak = 0
            deck.appendleft(card)
            print(f"Streak reset. Score: {score}   ⏱ Avg: {total_time/answered:.1f}s")

        if streak >= TARGET_STREAK:
            avg = total_time / answered
            print(f"\n🏆 Phase B complete! You beat Level 7. Avg time: {avg:.1f}s")
            return True, score, streak, avg

# ---------- Main ----------
def main():
    prog = load_progress()
    print("=== 🧮 Subnet Snap — Level 7 (Final Boss: /0–/30 Mixed) ===")

    # Phase A
    a_done, a_score = run_phase_a()
    if not a_done:
        # Save partial progress and exit
        prog["high_score"] = max(prog.get("high_score", 0), a_score)
        prog["best_streak"] = max(prog.get("best_streak", 0), 0)
        save_progress(prog)
        print("\nSession saved. See you next time!")
        return

    # Phase B
    b_done, b_score, b_streak, avg_time = run_phase_b()

    # Save results
    total_score = a_score + b_score
    prog["best_streak"] = max(prog.get("best_streak", 0), b_streak)
    prog["high_score"] = max(prog.get("high_score", 0), total_score)
    if b_done:
        prog["current_level"] = max(prog.get("current_level", LEVEL), LEVEL + 1)
        prog["level7_phase_cleared"] = True
    save_progress(prog)

    print("\n=== Session Summary ===")
    print(f"Total Score: {total_score}  | Best Streak: {prog['best_streak']}  | Level Saved: {prog.get('current_level')}")
    if b_done:
        print(f"Average Time (Phase B): {avg_time:.1f}s")
        print("🎉 You’ve mastered the full CIDR spectrum. Ready for the 7-Second Subnetting speedrun!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
