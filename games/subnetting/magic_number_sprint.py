#!/usr/bin/env python3
"""
Magic Number Sprint v2.5 — Cross-Platform Stable Edition
--------------------------------------------------------
✅ Fully portable: Windows, macOS, Linux
✅ Clean timing logic — no threads or signals
✅ Difficulty selector, hints, tutorial, scoring, and high-score tracking
"""

import ipaddress
import json
import os
import random
import sys
import time
from datetime import datetime

SCORE_FILE = "magic_number_sprint_scores.json"
STREAK_BONUS_TIME = 1.0
BASE_POINTS = 100
BONUS_MULTIPLIER = 1.5
HINT_PENALTY = 50
WRONG_PENALTY = 75
MIN_TIME = 5.0


# ---------- difficulty selector ----------
def choose_difficulty():
    print("\n🎮 Select Difficulty:")
    print("1) Casual   – 30 s per question (easiest)")
    print("2) Standard – 15 s per question (default)")
    print("3) Speedrun – 7 s per question (hardcore)")
    choice = input("> ").strip()
    if choice == "1":
        return 30.0
    elif choice == "3":
        return 7.0
    else:
        return 15.0


# ---------- helpers ----------
def detect_octet(cidr: int) -> int:
    for i, b in enumerate(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed, 1):
        if b != 255:
            return i
    return 4


def magic_number(cidr: int) -> int:
    net = ipaddress.ip_network(f"0.0.0.0/{cidr}")
    octet = detect_octet(cidr)
    mask_bytes = list(net.netmask.packed)
    val = 256 - mask_bytes[octet - 1]
    return val if val > 0 else 256


def visual_hint(cidr: int) -> str:
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    octet = detect_octet(cidr)
    mnum = magic_number(cidr)
    return (
        f"\n💡 /{cidr} → {mask}\nChanging octet = {octet}\n"
        f"Magic number = {mnum}\nExample ranges: "
        + ", ".join(f"{i}-{i + mnum - 1}" for i in range(0, 256, mnum)[:8])
        + " ...\n"
    )


# ---------- data ----------
def load_scores():
    if os.path.exists(SCORE_FILE):
        try:
            data = json.load(open(SCORE_FILE))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    else:
        data = {}
    data.setdefault("players", {})
    data.setdefault("runs", [])
    return data


def save_scores(data):
    with open(SCORE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def show_highscores(data):
    print("\n🏆 Magic Number Sprint Top 10")
    if not data["runs"]:
        print("(no runs yet)\n")
        return
    top = sorted(data["runs"], key=lambda x: x["score"], reverse=True)[:10]
    for i, r in enumerate(top, 1):
        print(f"{i:>2}. {r['name']:<12} {r['score']:>6} ({r['streak']} streak, {r['time']})")
    print()


# ---------- tutorial ----------
def explain_rules():
    print("\n📘 Magic Number Sprint – Rules and Example")
    print("""
A subnet's *magic number* (block size) is how much the *changing octet* increases
between subnets.

Formula:  Magic Number = 256 − (value of the subnet mask in the changing octet)

Example:  /26 → 255.255.255.192 → 256 − 192 = 64

That means subnets start at:
  0–63, 64–127, 128–191, 192–255 (in the last octet)

You'll be shown a CIDR prefix or a mask.
Type the correct magic number — the block size for that subnet.
""")

    trial_cidr = random.randint(8, 30)
    mask = str(ipaddress.ip_network(f"0.0.0.0/{trial_cidr}").netmask)
    correct = magic_number(trial_cidr)

    print(f"Let's try an untimed example:\n  CIDR: /{trial_cidr} ({mask})")
    ans = input("👉 Enter the magic number: ").strip()

    if ans == str(correct):
        print(f"✅ Correct! /{trial_cidr} → Magic number = {correct}")
    else:
        print(f"❌ Not quite. /{trial_cidr} → Magic number = {correct}")
        print(visual_hint(trial_cidr))

    print("\nExplanation:")
    print(f"The mask in the changing octet is {mask.split('.')[detect_octet(trial_cidr)-1]}.")
    print(f"256 − {mask.split('.')[detect_octet(trial_cidr)-1]} = {correct}, "
          f"so each subnet increases by {correct}.")
    input("\nPress Enter to return to menu…\n")


# ---------- main game ----------
def play(name, data):
    base_time = choose_difficulty()
    print(f"\nYou selected {base_time}s base time per question.\n")

    def get_time_for_question(q):
        if q < 10:
            return base_time - q * 1
        elif q < 20:
            return base_time - 9 - (q - 9) * 2
        elif q < 30:
            return base_time - 9 - 10 * 2 - (q - 19) * 3
        elif q < 40:
            return base_time - 9 - 10 * 2 - 10 * 3 - (q - 29) * 4
        else:
            reduction = 9 + 20 + 30 + (q - 39) * 5
            return max(base_time - reduction, MIN_TIME)

    p = data["players"].get(name, {"highscore": 0, "best_streak": 0})
    high = p.get("highscore", 0)
    best = p.get("best_streak", 0)
    score = 0
    streak = 0
    mult = 1.0
    extra_time = 0.0
    q = 0

    print(f"\nWelcome {name}! Personal high score: {high}\n")

    while True:
        q += 1
        base_t = max(get_time_for_question(q), MIN_TIME)
        time_limit = base_t + extra_time
        extra_time = 0
        if time_limit <= 0:
            print("\n🕑 Timer exhausted!")
            break

        cidr = random.randint(0, 30)
        mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
        qtype = random.choice(["cidr", "mask"])
        disp = f"/{cidr}" if qtype == "cidr" else mask
        label = "CIDR" if qtype == "cidr" else "Subnet Mask"
        answer = magic_number(cidr)

        print(f"\nQ{q} | {label}: {disp} | Score:{score} x{mult:.1f} | Time:{time_limit:.1f}s")

        # Measure elapsed time instead of interrupting input
        start = time.time()
        ans = input(f"👉 Enter magic number (you have {time_limit:.0f}s): ").strip().lower()
        elapsed = time.time() - start

        if elapsed > time_limit:
            print("\n⏰ Time up!")
            break

        if ans in ("q", "quit", "exit"):
            break
        if ans in ("h", "hint"):
            print(visual_hint(cidr))
            score = max(0, score - HINT_PENALTY)
            continue
        if not ans.isdigit():
            print("Enter a number, 'h', or 'q'.")
            continue

        ans_int = int(ans)
        if ans_int == answer:
            base = BASE_POINTS
            if elapsed <= 3:
                base += 50
            if streak and streak % 5 == 0:
                mult *= BONUS_MULTIPLIER
                extra_time += STREAK_BONUS_TIME
                print(f"⚡ 5-Streak! +{STREAK_BONUS_TIME:.0f}s bonus, x{mult:.1f} multiplier!")
            pts = int(base * mult)
            score += pts
            streak += 1
            best = max(best, streak)
            print(f"✅ Correct! +{pts} pts (Streak {streak})\n")
        else:
            print(f"❌ Wrong → {answer}")
            print(visual_hint(cidr))
            score = max(0, score - WRONG_PENALTY)
            streak = 0
            mult = 1.0
            print(f"💀 -{WRONG_PENALTY} pts | Score {score}\n")

        if time_limit <= MIN_TIME:
            print("🕒 Timer minimum reached — game complete!")
            break

    data["players"].setdefault(name, {})
    data["players"][name]["highscore"] = max(high, score)
    data["players"][name]["best_streak"] = max(best, streak)
    data["runs"].append({
        "name": name,
        "score": score,
        "streak": best,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    data["runs"] = data["runs"][-500:]
    save_scores(data)
    print(f"\n=== Session End ===\nScore:{score} | Best Streak:{best}")
    print(f"🏆 {name}'s High Score: {data['players'][name]['highscore']}\n")


# ---------- menu ----------
def main():
    data = load_scores()
    while True:
        print("=== Magic Number Sprint v2.5 ===")
        print("1) Start new game")
        print("2) Explain rules / Trial round")
        print("3) View global high scores")
        print("4) Quit")
        c = input("> ").strip()
        if c == "1":
            name = input("Enter your name: ").strip() or "Player"
            play(name, data)
        elif c == "2":
            explain_rules()
        elif c == "3":
            show_highscores(data)
        elif c == "4":
            print("Goodbye!")
            break
        else:
            print("Choose 1-4.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
