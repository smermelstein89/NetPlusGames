#!/usr/bin/env python3
"""
Changing Octet Challenge v5 — Dynamic Timer Edition
---------------------------------------------------
Each question starts with a timer that shortens as you progress:
  • Starts at 10s
  • After Q10, -2s per question
  • After Q20, -3s per question, etc.
Game ends automatically when timer <= 0.
"""

import ipaddress, json, os, random, signal, sys, time

SCORE_FILE = "changing_octet_v5_scores.json"
BASE_TIME = 10.0
STREAK_BONUS_TIME = 1.0
BASE_POINTS = 100
BONUS_MULTIPLIER = 1.5
HINT_PENALTY = 50
WRONG_PENALTY = 75
MIN_TIME = 2.0  # never go below 2 seconds

# ---------- helpers ----------
def detect_octet(cidr: int) -> int:
    for i, b in enumerate(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed, 1):
        if b != 255:
            return i
    return 4

def visual_explanation(cidr: int) -> str:
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    bits = ".".join(f"{b:08b}" for b in ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    o = detect_octet(cidr)
    return (
        f"\n💡 /{cidr}  →  {mask}\nBinary: {bits}\nChanging octet = {o} "
        f"({['1st','2nd','3rd','4th'][o-1]})\n"
    )

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
    return data

def save_scores(data):
    with open(SCORE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def show_highscores(data):
    print("\n🏆 High Scores (v5)")
    entries = [(v.get("highscore", 0), k) for k, v in data["players"].items()]
    entries.sort(reverse=True)
    if not entries:
        print("(no scores yet)")
    for i, (s, name) in enumerate(entries[:10], 1):
        print(f"{i:>2}. {name:<15} {s}")
    print()

# ---------- timer ----------
class Timeout(Exception):
    pass
def handler(signum, frame): raise Timeout
signal.signal(signal.SIGALRM, handler)

# ---------- core ----------
def get_time_for_question(qnum):
    """Determine the time allowed based on question number."""
    if qnum < 10:
        return BASE_TIME - qnum * 1
    elif qnum < 20:
        return BASE_TIME - 9 - (qnum - 9) * 2
    elif qnum < 30:
        return BASE_TIME - 9 - 10 * 2 - (qnum - 19) * 3
    elif qnum < 40:
        return BASE_TIME - 9 - 10 * 2 - 10 * 3 - (qnum - 29) * 4
    else:
        # keep increasing rate
        reduction = 9 + 20 + 30 + (qnum - 39) * 5
        return max(BASE_TIME - reduction, MIN_TIME)

# ---------- main game ----------
def play(name, data):
    player = data["players"].get(name, {"highscore": 0, "best_streak": 0})
    highscore = player.get("highscore", 0)
    best_streak = player.get("best_streak", 0)
    score = 0
    streak = 0
    mult = 1.0
    extra_time = 0.0
    qnum = 0

    print(f"\nWelcome {name}! Current high score: {highscore}")
    print("Timer shortens every 10 questions! +1s per 5-streak bonus.\n")

    while True:
        qnum += 1
        base_time = max(get_time_for_question(qnum), MIN_TIME)
        time_limit = base_time + extra_time
        extra_time = 0.0
        if time_limit <= 0:
            print("\n🕑 Timer exhausted — game over!")
            break

        cidr = random.randint(0, 30)
        mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
        qtype = random.choice(["cidr", "mask"])
        disp = f"/{cidr}" if qtype == "cidr" else mask
        label = "CIDR" if qtype == "cidr" else "Subnet Mask"

        print(f"\nQ{qnum} | {label}: {disp} | Score:{score} x{mult:.1f} | Time:{time_limit:.1f}s")

        signal.alarm(int(time_limit))
        try:
            start = time.time()
            ans = input("👉 Which octet changes (1–4)? ").strip().lower()
            signal.alarm(0)
        except Timeout:
            print("\n⏰ Time up!")
            break

        elapsed = time.time() - start
        if ans in ("q", "quit", "exit"):
            break
        if ans in ("h", "hint"):
            print(visual_explanation(cidr))
            score = max(0, score - HINT_PENALTY)
            continue
        if not ans.isdigit() or not (1 <= int(ans) <= 4):
            print("Enter 1–4, 'h', or 'q'.")
            continue

        correct = detect_octet(cidr)
        if int(ans) == correct:
            base = BASE_POINTS
            if elapsed <= 3:
                base += 50
            if streak and streak % 5 == 0:
                mult *= BONUS_MULTIPLIER
                extra_time += STREAK_BONUS_TIME
                print(f"⚡ 5-Streak! +{STREAK_BONUS_TIME:.0f}s bonus next round, x{mult:.1f}!")
            pts = int(base * mult)
            score += pts
            streak += 1
            best_streak = max(best_streak, streak)
            print(f"✅ Correct! +{pts} pts (Streak {streak})\n")
        else:
            print(f"❌ Wrong → {correct} ({['1st','2nd','3rd','4th'][correct-1]})")
            print(visual_explanation(cidr))
            score = max(0, score - WRONG_PENALTY)
            streak = 0
            mult = 1.0
            print(f"💀 -{WRONG_PENALTY} pts | Score {score}\n")

        # End game when timer per question gets too short
        if time_limit <= MIN_TIME:
            print("🕒 Timer reached minimum! Game complete!")
            break

    # Save
    data["players"].setdefault(name, {})
    data["players"][name]["highscore"] = max(highscore, score)
    data["players"][name]["best_streak"] = max(best_streak, streak)
    save_scores(data)
    print(f"\n=== Session End ===\nScore:{score} | Best Streak:{best_streak}")
    print(f"🏆 {name}'s High Score: {data['players'][name]['highscore']}\n")

# ---------- menu ----------
def main():
    data = load_scores()
    while True:
        print("=== Changing Octet Challenge v5 ===")
        print("1) Start new game")
        print("2) View high scores")
        print("3) Quit")
        c = input("> ").strip()
        if c == "1":
            name = input("Enter your name: ").strip() or "Player"
            play(name, data)
        elif c == "2":
            show_highscores(data)
        elif c == "3":
            print("Goodbye!")
            break
        else:
            print("Choose 1-3.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
