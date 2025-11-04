#!/usr/bin/env python3
"""
CIDR Flash v2 — Learning Mode Edition
-------------------------------------
Practice subnet mask <-> CIDR notation using spaced repetition style.
Includes:
 - Game Mode (timed, scored)
 - Learning Mode (Anki-style, repetition & explanations)
"""

import ipaddress
import json
import os
import random
import time

HIGHSCORE_FILE = "cidr_flash_scores.json"

# Build CIDR reference table
CIDR_TABLE = [
    {
        "cidr": i,
        "mask": str(ipaddress.ip_network(f"0.0.0.0/{i}").netmask)
    }
    for i in range(8, 31)
]

# ---------------- File I/O ----------------
def load_scores():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f)
    return []

def save_scores(scores):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def print_highscores(scores):
    if not scores:
        print("\nNo scores yet!\n")
        return
    print("\n🏆 High Scores 🏆")
    for i, entry in enumerate(sorted(scores, key=lambda x: x["score"], reverse=True)[:10], start=1):
        print(f"{i}. {entry['name']} — {entry['score']} pts — {entry['avg_time']:.1f}s avg")


# ---------------- Hints and Explanations ----------------
def get_hint(cidr):
    if cidr >= 24:
        return f"💡 Hint: /{cidr} means the last octet is partially masked — notice .0, .128, .192, .224..."
    elif cidr >= 16:
        return f"💡 Hint: /{cidr} affects the 3rd octet — every step adds smaller increments (like /20 = .240)."
    else:
        return f"💡 Hint: /{cidr} changes the 2nd octet — think of big networks like /8 (Class A), /12, /16."

def get_memorization_tip(cidr, correct_mask):
    block = 2 ** (32 - cidr)
    if cidr >= 24:
        pattern = "each step right halves the subnet and adds higher last-octet values (.0, .128, .192, .224, etc.)"
    elif cidr >= 16:
        pattern = "the third octet changes — think 255.255.(mask).0 with decreasing third-octet values"
    else:
        pattern = "the second octet changes — these are large 'Class A' or 'B' networks"
    return (
        f"❌ You missed /{cidr}.\n"
        f"✅ Correct mask: {correct_mask}\n"
        f"🧠 Remember: /{cidr} leaves {32 - cidr} host bits → block size {block}. "
        f"So {pattern}."
    )


# ---------------- Game Mode ----------------
def play_game_round():
    q = random.choice(CIDR_TABLE)
    start = time.time()
    score = 0
    penalties = 0

    direction = random.choice(["cidr_to_mask", "mask_to_cidr"])

    if direction == "cidr_to_mask":
        print(f"\nCIDR: /{q['cidr']}")
        ans = input("Enter subnet mask (or 'h' for hint): ").strip()
        if ans.lower() in ["h", "hint"]:
            print(get_hint(q["cidr"]))
            penalties += 0.5
            ans = input("Try again: ").strip()
        if ans == q["mask"]:
            print("✅ Correct!")
            score = 1
        elif ans.lower() in ["q", "quit", "exit"]:
            return None, None
        else:
            print(get_memorization_tip(q["cidr"], q["mask"]))

    else:
        print(f"\nSubnet mask: {q['mask']}")
        ans = input("Enter CIDR (just the number) or 'h' for hint: /").strip()
        if ans.lower() in ["h", "hint"]:
            print(get_hint(q["cidr"]))
            penalties += 0.5
            ans = input("Try again (number only): /").strip()
        if ans == str(q["cidr"]):
            print("✅ Correct!")
            score = 1
        elif ans.lower() in ["q", "quit", "exit"]:
            return None, None
        else:
            print(get_memorization_tip(q["cidr"], q["mask"]))

    elapsed = time.time() - start
    score = max(0, score - penalties)
    print(f"⏱ {elapsed:.1f}s | Score: {score:.1f} (−{penalties:.1f} hints)\n")
    return score, elapsed


def run_game_mode():
    print("\n🎮 GAME MODE: Timed Recall")
    name = input("Enter your name: ").strip() or "Anonymous"
    rounds = input("How many rounds? (e.g. 20): ").strip()
    try:
        rounds = int(rounds)
    except:
        rounds = 20

    total_score = 0
    total_time = 0
    count = 0

    while count < rounds:
        result = play_game_round()
        if result == (None, None):
            print("🚪 Exiting early.")
            break
        s, t = result
        total_score += s
        total_time += t
        count += 1
        if count % 10 == 0:
            print(f"📈 Progress: {count}/{rounds} — Score: {total_score:.1f}\n")

    if count > 0:
        avg_time = total_time / count
        print(f"\n🏁 Final Score: {total_score:.1f}  | Avg Time: {avg_time:.1f}s")
        scores = load_scores()
        scores.append({"name": name, "score": total_score, "avg_time": avg_time})
        save_scores(scores)
        print_highscores(scores)


# ---------------- Learning Mode ----------------
def run_learning_mode():
    print("\n📚 LEARNING MODE: Anki-Style Repetition")
    print("Type 'q' anytime to exit.\n")
    correct_streak = 0
    wrong_total = 0
    review_pool = CIDR_TABLE.copy()
    random.shuffle(review_pool)
    total_answered = 0

    while review_pool:
        q = review_pool.pop(0)
        total_answered += 1
        direction = random.choice(["cidr_to_mask", "mask_to_cidr"])

        if direction == "cidr_to_mask":
            print(f"\nCIDR: /{q['cidr']}")
            ans = input("Subnet mask (or 'h' for hint): ").strip()
            if ans.lower() in ["q", "quit", "exit"]:
                print("🚪 Exiting learning mode.")
                break
            if ans.lower() in ["h", "hint"]:
                print(get_hint(q["cidr"]))
                ans = input("Try again: ").strip()

            if ans == q["mask"]:
                print("✅ Correct!")
                correct_streak += 1
            else:
                print(get_memorization_tip(q["cidr"], q["mask"]))
                wrong_total += 1
                review_pool.append(q)  # re-add for spaced review

        else:
            print(f"\nSubnet mask: {q['mask']}")
            ans = input("CIDR prefix (just number, 'h' for hint): /").strip()
            if ans.lower() in ["q", "quit", "exit"]:
                print("🚪 Exiting learning mode.")
                break
            if ans.lower() in ["h", "hint"]:
                print(get_hint(q["cidr"]))
                ans = input("Try again (number only): /").strip()

            if ans == str(q["cidr"]):
                print("✅ Correct!")
                correct_streak += 1
            else:
                print(get_memorization_tip(q["cidr"], q["mask"]))
                wrong_total += 1
                review_pool.append(q)

        if total_answered % 10 == 0:
            print(f"\n📊 Progress: {total_answered} answered, {wrong_total} missed "
                  f"({len(review_pool)} left in review pool).")

    print("\n🎓 Session Complete!")
    print(f"Answered: {total_answered} | Missed: {wrong_total} | Streak: {correct_streak}")


# ---------------- Main Menu ----------------
def main():
    print("=== 🧮 CIDR Flash v2 — Learning Mode Edition ===")
    while True:
        print("\nSelect a mode:")
        print("1. 🎮 Game Mode (timed recall)")
        print("2. 📚 Learning Mode (Anki-style repetition)")
        print("3. 🏆 View High Scores")
        print("4. 🚪 Exit")
        choice = input("> ").strip()
        if choice == "1":
            run_game_mode()
        elif choice == "2":
            run_learning_mode()
        elif choice == "3":
            print_highscores(load_scores())
        elif choice.lower() in ["4", "q", "exit", "quit"]:
            print("Goodbye 👋")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()

