#!/usr/bin/env python3
"""
Octet Drill v2.0 — Identify + Focus Combo Game
----------------------------------------------
Cross-platform (Windows/macOS/Linux)

Games:
1) Octet Identifier — find which octet changed from 255
2) Octet Focus Drill — find which octet defines subnet for given CIDR

Features:
- Instructions menu
- Timer mode (optional)
- Persistent high scores
- Safe exit
"""

import os
import random
import time
import json

SCORE_FILE = "octet_drill_scores.json"
OCTETS = [255, 254, 252, 248, 240, 224, 192, 128, 0]


# ---------- Utility Functions ----------

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {"Identifier": 0, "Focus": 0}
    try:
        with open(SCORE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"Identifier": 0, "Focus": 0}


def save_scores(scores):
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)


def update_score(game, streak):
    scores = load_scores()
    if streak > scores.get(game, 0):
        scores[game] = streak
        save_scores(scores)
        print(f"🏆 New High Score for {game}: {streak}!")
    else:
        print(f"💾 Your streak: {streak} (High Score: {scores.get(game, 0)})")
    time.sleep(2)


def wait_for_enter():
    input("\nPress Enter to return to menu...")


def cidr_from_mask(mask):
    return sum(bin(int(o)).count("1") for o in mask.split("."))


def mask_from_cidr(cidr):
    bits = (1 << 32) - (1 << (32 - cidr))
    return ".".join(str((bits >> (8 * i)) & 255) for i in [3, 2, 1, 0])


# ---------- Game Logic ----------

def octet_identifier(timer_limit=None):
    streak = 0
    while True:
        # Generate random mask
        change_index = random.randint(1, 4)
        mask = []
        for i in range(1, 5):
            if i < change_index:
                mask.append(255)
            elif i == change_index:
                mask.append(random.choice(OCTETS[1:-1]))
            else:
                mask.append(0)
        mask_str = ".".join(map(str, mask))
        cidr = cidr_from_mask(mask_str)

        clear()
        print(f"🧩 Subnet Mask: {mask_str}  (/{cidr})")
        print("Which octet changed from 255?")
        print("(1) First   (2) Second   (3) Third   (4) Fourth")
        if timer_limit:
            print(f"⏱️ {timer_limit} seconds per question")

        start = time.time()
        answer = input("> ").strip()
        elapsed = time.time() - start

        if answer.lower() in ["q", "quit", "exit"]:
            print("\n👋 Exiting game...")
            break

        if timer_limit and elapsed > timer_limit:
            print("⏰ Time’s up!")
            break

        if answer not in {"1", "2", "3", "4"}:
            print("⚠️ Invalid input.")
            time.sleep(1)
            continue

        if int(answer) == change_index:
            streak += 1
            print(f"✅ Correct! Streak: {streak}")
        else:
            print(f"❌ Nope. It changed in octet {change_index}.")
            break

        time.sleep(1.2)

    update_score("Identifier", streak)


def octet_focus_drill(timer_limit=None):
    streak = 0
    while True:
        cidr = random.randint(8, 30)
        mask = mask_from_cidr(cidr)
        parts = mask.split(".")
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))

        # Determine where the mask changes
        change_index = next(
            (i + 1 for i, o in enumerate(parts) if o != "255"), 4
        )

        clear()
        print(f"🌐 IP: {ip} /{cidr}")
        print("Which octet determines the subnet?")
        print("(1) First   (2) Second   (3) Third   (4) Fourth")
        if timer_limit:
            print(f"⏱️ {timer_limit} seconds per question")

        start = time.time()
        answer = input("> ").strip()
        elapsed = time.time() - start

        if answer.lower() in ["q", "quit", "exit"]:
            print("\n👋 Exiting game...")
            break

        if timer_limit and elapsed > timer_limit:
            print("⏰ Time’s up!")
            break

        if answer not in {"1", "2", "3", "4"}:
            print("⚠️ Invalid input.")
            time.sleep(1)
            continue

        if int(answer) == change_index:
            streak += 1
            print(
                f"✅ Correct! /{cidr} = {mask}, changing at octet {change_index}. "
                f"Streak: {streak}"
            )
        else:
            print(
                f"❌ Nope. /{cidr} = {mask}, so octet {change_index} determines the subnet."
            )
            break

        time.sleep(1.8)

    update_score("Focus", streak)


def instructions():
    clear()
    print("📘 Instructions\n")
    print("1️⃣ Octet Identifier:")
    print("   - You’ll see a subnet mask (e.g., 255.255.255.224).")
    print("   - Identify which octet changed from 255 → something else.")
    print("   - Type 1–4 for first–fourth octet.")
    print("   - Builds reflexes for recognizing subnet boundaries.\n")
    print("2️⃣ Octet Focus Drill:")
    print("   - You’ll see an IP and CIDR (e.g., 192.168.35.67 /20).")
    print("   - Identify which octet determines the subnet boundary.")
    print("   - Example: /20 = 255.255.240.0 → third octet.\n")
    print("💡 Type Q anytime to quit a round.\n")
    wait_for_enter()


# ---------- Main Menu ----------

def main_menu():
    while True:
        clear()
        scores = load_scores()
        print("🌐 OCTET DRILL v2.0 — Identify + Focus Combo Game\n")
        print("1) ▶ Play Octet Identifier")
        print("2) ▶ Play Octet Focus Drill")
        print("3) ℹ️  Instructions")
        print("4) 🕒 Toggle Timer Mode")
        print("5) 🏆 View High Scores")
        print("6) ❌ Quit\n")

        choice = input("> ").strip().lower()
        if choice == "1":
            octet_identifier(timer_limit=TIMER_MODE)
        elif choice == "2":
            octet_focus_drill(timer_limit=TIMER_MODE)
        elif choice == "3":
            instructions()
        elif choice == "4":
            toggle_timer()
        elif choice == "5":
            show_scores()
        elif choice in {"6", "q", "quit", "exit"}:
            print("\n👋 Thanks for playing Octet Drill!")
            break
        else:
            print("⚠️ Invalid selection.")
            time.sleep(1)


def show_scores():
    clear()
    scores = load_scores()
    print("🏆 High Scores\n")
    for game, score in scores.items():
        print(f"{game}: {score}")
    wait_for_enter()


def toggle_timer():
    global TIMER_MODE
    clear()
    if TIMER_MODE is None:
        TIMER_MODE = 10
        print("⏱️ Timer Mode ENABLED (10 seconds per question)")
    else:
        TIMER_MODE = None
        print("🕹️ Timer Mode DISABLED")
    time.sleep(1.5)


# ---------- Entry Point ----------

if __name__ == "__main__":
    TIMER_MODE = None
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Exiting safely. Bye!")
