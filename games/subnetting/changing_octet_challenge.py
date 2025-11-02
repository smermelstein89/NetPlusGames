#!/usr/bin/env python3
"""
Changing Octet Challenge v3 — Timed Reflex Mode
------------------------------------------------
Arcade-style subnet reflex trainer:
 - Starts with 10 seconds total
 - Time slowly decreases per question
 - Wrong answers cut more time
 - Increasing difficulty, combos, score multipliers
 - Ends automatically when timer hits zero
"""

import ipaddress, random, time, json, os, sys

PROGRESS_FILE = "subnet_snap_progress.json"

# Difficulty progression
DIFFICULTY = [
    (0,   range(24, 31)),  # Easy — last octet
    (15,  range(16, 31)),  # Medium — adds 3rd octet
    (30,  range(8, 31)),   # Hard — adds 2nd octet
    (50,  range(0, 31)),   # Expert — all octets
]

BASE_POINTS = 100
BONUS_MULTIPLIER = 1.5
TIME_BONUS_CUTOFF = 3.0
TIME_PENALTY_CUTOFF = 6.0
HINT_PENALTY = 50
WRONG_PENALTY = 75

# Timer behavior
START_TIME = 10.0        # seconds to start
TIME_DECAY_PER_Q = 0.3   # time lost per question
WRONG_TIME_PENALTY = 1.5 # extra time lost on wrong answer
TIME_BONUS_ON_CORRECT = 0.2 # regain a tiny bit for fast answers

# ---------- Helpers ----------
def detect_changing_octet(cidr: int) -> int:
    mask_bytes = list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    for i, b in enumerate(mask_bytes, 1):
        if b != 255:
            return i
    return 4

def binary_mask_visual(cidr: int) -> str:
    mask_bytes = list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    bits = ["{0:08b}".format(b) for b in mask_bytes]
    return ".".join(bits)

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

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"changing_octet_highscore": 0, "changing_octet_best_streak": 0}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=2)

def pick_cidr(score: int):
    allowed = range(24, 31)
    for threshold, rng in DIFFICULTY:
        if score >= threshold:
            allowed = rng
    return random.choice(allowed)

# ---------- Game ----------
def play():
    progress = load_progress()
    highscore = progress.get("changing_octet_highscore", 0)
    best_streak = progress.get("changing_octet_best_streak", 0)
    score = 0
    streak = 0
    multiplier = 1.0
    time_left = START_TIME
    question_count = 0

    print("=== ⏱️ Changing Octet Challenge v3 — Timed Reflex Mode ===")
    print("Identify which octet changes before the timer hits zero!")
    print(f"Start time: {START_TIME:.1f}s | Each round gets faster!")
    print("Use 'h' for hint (-50 pts, -0.5s), 'q' to quit.\n")

    while time_left > 0:
        cidr = pick_cidr(score)
        mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
        question_type = random.choice(["cidr", "mask"])
        display = f"/{cidr}" if question_type == "cidr" else mask
        label = "CIDR" if question_type == "cidr" else "Subnet Mask"

        print(f"\n⏱️ Time Left: {time_left:.1f}s | Score: {score} | x{multiplier:.1f}")
        print(f"📘 {label}: {display}")

        start_time = time.time()
        ans = input("👉 Which octet changes (1–4)? ").strip().lower()
        elapsed = time.time() - start_time
        time_left -= elapsed  # subtract response time
        question_count += 1
        time_left -= TIME_DECAY_PER_Q  # shrink available time each round

        if ans in ("q", "quit", "exit"):
            break
        if ans in ("h", "hint"):
            print(visual_explanation(cidr))
            score = max(0, score - HINT_PENALTY)
            time_left -= 0.5
            print(f"🔹 Hint used (-{HINT_PENALTY} pts, -0.5s). Score:{score}\n")
            continue

        if not ans.isdigit() or not (1 <= int(ans) <= 4):
            print("Please enter 1–4, 'h', or 'q'.")
            continue

        correct_octet = detect_changing_octet(cidr)
        ans_int = int(ans)

        if ans_int == correct_octet:
            base = BASE_POINTS
            if elapsed <= TIME_BONUS_CUTOFF: base += 50; time_left += TIME_BONUS_ON_CORRECT
            elif elapsed > TIME_PENALTY_CUTOFF: base -= 25
            if streak and streak % 5 == 0:
                multiplier *= BONUS_MULTIPLIER
                print("🔥 Combo multiplier increased!")
            points = int(base * multiplier)
            score += points
            streak += 1
            best_streak = max(best_streak, streak)
            print(f"✅ Correct! Changing octet: {correct_octet} ({['1st','2nd','3rd','4th'][correct_octet-1]})")
            print(f"⏱ {elapsed:.1f}s | +{points} pts | Streak:{streak}\n")
        else:
            print(f"❌ Wrong! It was {correct_octet} ({['1st','2nd','3rd','4th'][correct_octet-1]}).")
            print(visual_explanation(cidr))
            score = max(0, score - WRONG_PENALTY)
            time_left -= WRONG_TIME_PENALTY
            streak = 0
            multiplier = 1.0
            print(f"💀 -{WRONG_PENALTY} pts | -{WRONG_TIME_PENALTY:.1f}s | Score:{score}\n")

        if time_left <= 0:
            break

    # Save and end
    progress["changing_octet_highscore"] = max(progress.get("changing_octet_highscore", 0), score)
    progress["changing_octet_best_streak"] = max(progress.get("changing_octet_best_streak", 0), best_streak)
    save_progress(progress)

    print("\n=== ⏰ TIME'S UP! ===")
    print(f"Final Score: {score} | Best Streak: {best_streak}")
    print(f"🏆 High Score: {progress['changing_octet_highscore']} | Longest Streak: {progress['changing_octet_best_streak']}")
    print("Keep practicing your reflexes to improve your subnetting speed!\n")

# ---------- Main ----------
if __name__ == "__main__":
    try:
        play()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
