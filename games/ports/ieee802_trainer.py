#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IEEE 802 Trainer v7 — Time Bonus + Full-Deck Anki MC
----------------------------------------------------
- Cross-platform (Windows, macOS, Linux)
- Core vs Expanded study sets
- Learning:
    * Flashcards
    * Anki (text SRS, self-graded)
    * Anki MC (full-deck multiple choice until all correct or quit)
    * Reset SRS
    * Instructions
- Games:
    * Multiple Choice (Code -> Name) with time bonuses
    * Reverse MC (Name -> Code) with time bonuses
    * Streak Survival
    * 60s Speedrun
- 'h' to show mnemonic hints for 802.11 (Wi-Fi) standards
- High scores + SRS saved as JSON
"""

import json
import os
import random
import sys
import time
from datetime import datetime

SCORE_FILE = "ieee802_scores.json"
SRS_FILE   = "ieee802_srs.json"

# ---------- Color helpers ----------

def _tty():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False

def _c(code, t):
    return f"\033[{code}m{t}\033[0m" if _tty() else t

def green(s):  return _c("92", s)
def red(s):    return _c("91", s)
def yellow(s): return _c("93", s)
def cyan(s):   return _c("96", s)
def bold(s):   return _c("1", s)

# ---------- Data sets ----------

STANDARDS_CORE = [
    {"code":"802.1Q","name":"VLAN Tagging","aka":[],"summary":"Adds VLAN ID to Ethernet frames for segmentation.","core":True},
    {"code":"802.1X","name":"Port-Based Access Control","aka":["NAC","EAPoL"],"summary":"Authenticates devices at the switch/AP using RADIUS.","core":True},
    {"code":"802.3","name":"Ethernet","aka":[],"summary":"Wired LAN physical & MAC (copper & fiber).","core":True},
    {"code":"802.11a","name":"Wi-Fi 1","aka":[],"summary":"5 GHz, 54 Mb/s, OFDM (legacy).","core":True},
    {"code":"802.11b","name":"Wi-Fi 2","aka":[],"summary":"2.4 GHz, 11 Mb/s, DSSS (legacy).","core":True},
    {"code":"802.11g","name":"Wi-Fi 3","aka":[],"summary":"2.4 GHz, 54 Mb/s, OFDM (legacy).","core":True},
    {"code":"802.11n","name":"Wi-Fi 4","aka":[],"summary":"2.4/5 GHz, MIMO, up to 600 Mb/s.","core":True},
    {"code":"802.11ac","name":"Wi-Fi 5","aka":[],"summary":"5 GHz, MU-MIMO, 80/160 MHz channels.","core":True},
    {"code":"802.11ax","name":"Wi-Fi 6/6E","aka":[],"summary":"2.4/5/6 GHz, OFDMA, improved efficiency.","core":True},
    {"code":"802.15.1","name":"Bluetooth (classic)","aka":["Bluetooth"],"summary":"Short-range WPAN.","core":True},
    {"code":"802.15.4","name":"Low-Rate WPAN","aka":["Zigbee/Thread base"],"summary":"IoT mesh foundations at low power/data rates.","core":True},
]

STANDARDS_EXPANDED = [
    {"code":"802","name":"IEEE 802 Overview","aka":["802 family"],"summary":"LAN/MAN standards umbrella.","core":False},
    {"code":"802.1D","name":"Bridging & Spanning Tree (STP)","aka":["STP"],"summary":"Loop prevention in Layer 2 topologies.","core":True},
    {"code":"802.1w","name":"Rapid Spanning Tree (RSTP)","aka":["RSTP"],"summary":"Faster convergence vs. STP.","core":True},
    {"code":"802.1s","name":"Multiple Spanning Tree (MSTP)","aka":["MSTP"],"summary":"Maps VLANs to STP instances.","core":True},
    {"code":"802.1Q","name":"VLAN Tagging","aka":["VLANs"],"summary":"802.1Q tag in Ethernet frames for VLAN ID.","core":True},
    {"code":"802.1p","name":"Layer 2 QoS/PCP","aka":["Class of Service"],"summary":"Priority bits inside 802.1Q header.","core":True},
    {"code":"802.1X","name":"Port-Based Network Access Control","aka":["NAC","EAPoL"],"summary":"Supplicant–Authenticator–RADIUS framework.","core":True},
    {"code":"802.1AB","name":"LLDP","aka":["Link Layer Discovery Protocol"],"summary":"Vendor-neutral neighbor discovery.","core":True},
    {"code":"802.1AX","name":"Link Aggregation","aka":["LACP"],"summary":"Bundles links for redundancy/capacity.","core":True},
    {"code":"802.3","name":"Ethernet","aka":[],"summary":"Wired LAN physical & MAC for Ethernet.","core":True},
    {"code":"802.3u","name":"Fast Ethernet","aka":["100BASE-TX"],"summary":"100 Mb/s Ethernet.","core":True},
    {"code":"802.3ab","name":"Gigabit Ethernet over Copper","aka":["1000BASE-T"],"summary":"1 Gb/s over twisted pair.","core":True},
    {"code":"802.3z","name":"Gigabit Ethernet over Fiber","aka":["1000BASE-SX/LX"],"summary":"1 Gb/s over fiber.","core":True},
    {"code":"802.3ae","name":"10 Gigabit Ethernet","aka":["10GbE"],"summary":"10 Gb/s Ethernet over fiber.","core":True},
    {"code":"802.3af","name":"Power over Ethernet (PoE)","aka":["PoE"],"summary":"~15.4W at PSE.","core":True},
    {"code":"802.3at","name":"PoE+ (Type 2)","aka":["PoE+"],"summary":"~30W at PSE.","core":True},
    {"code":"802.3bt","name":"PoE++ (Types 3/4)","aka":["4-pair PoE"],"summary":"~60–90W depending on class.","core":True},
    {"code":"802.11","name":"Wireless LAN (Wi-Fi)","aka":["Wi-Fi"],"summary":"Base Wi-Fi standard.","core":True},
    {"code":"802.11a","name":"Wi-Fi 1","aka":[],"summary":"5 GHz; 54 Mb/s.","core":True},
    {"code":"802.11b","name":"Wi-Fi 2","aka":[],"summary":"2.4 GHz; 11 Mb/s.","core":True},
    {"code":"802.11g","name":"Wi-Fi 3","aka":[],"summary":"2.4 GHz; 54 Mb/s.","core":True},
    {"code":"802.11n","name":"Wi-Fi 4 (MIMO)","aka":["Wi-Fi 4"],"summary":"2.4/5 GHz; MIMO.","core":True},
    {"code":"802.11ac","name":"Wi-Fi 5 (VHT)","aka":["Wi-Fi 5"],"summary":"5 GHz; MU-MIMO; 80/160 MHz.","core":True},
    {"code":"802.11ax","name":"Wi-Fi 6/6E (OFDMA)","aka":["Wi-Fi 6","Wi-Fi 6E"],"summary":"2.4/5/6 GHz; efficiency.","core":True},
    {"code":"802.11i","name":"Robust Security Networks","aka":["RSN"],"summary":"Introduced WPA2 (AES-CCMP).","core":True},
    {"code":"802.15.1","name":"Bluetooth (classic)","aka":["Bluetooth"],"summary":"Short-range WPAN.","core":True},
    {"code":"802.15.4","name":"Low-Rate WPAN","aka":["Zigbee base","Thread base"],"summary":"IoT low-power mesh.","core":True},
    {"code":"802.16","name":"WiMAX","aka":[],"summary":"Broadband wireless MAN.","core":False},
]

# Wi-Fi mnemonic hints (from your descriptions)
WIFI_HINTS = {
    "802.11a": '"a" for the beginning — 5 GHz, 54 Mbps (shorter range).',
    "802.11b": '"b" for better range — 2.4 GHz, 11 Mbps (longer range, slower).',
    "802.11g": '"g" rhymes with "b" — same 2.4 GHz, but 54 Mbps.',
    "802.11n": '"n" = "and" — both 2.4 & 5 GHz, 600 Mbps, first with MIMO.',
    "802.11ac": '"ac" continues the "a" (5 GHz). First with MU-MIMO; ~7 Gbps.',
    "802.11ax": '"x" looks like arrows converging — brings all together; 2.4 & 5 GHz; MU-MIMO; ~9.6 Gbps.',
}

# ---------- JSON persistence ----------

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def record_score(mode_key, score):
    scores = load_json(SCORE_FILE)
    entry = {"score": score, "ts": datetime.now().isoformat(timespec="seconds")}
    scores.setdefault(mode_key, []).append(entry)
    scores[mode_key] = sorted(scores[mode_key], key=lambda x: x["score"], reverse=True)[:10]
    save_json(SCORE_FILE, scores)

def print_high_scores():
    scores = load_json(SCORE_FILE)
    if not scores:
        print(yellow("No high scores yet."))
        return
    print(bold("\nHigh Scores"))
    for mode in sorted(scores.keys()):
        print(cyan(f"\n{mode}:"))
        for i, s in enumerate(scores[mode], 1):
            print(f" {i:>2}. {s['score']}  {s['ts']}")
    print()

# ---------- UI helpers ----------

def clear():
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass

def press_enter():
    try:
        input(yellow("\n[Enter] to continue... "))
    except EOFError:
        pass

def ask_choice_with_hint(prompt, lo, hi, hint_code=None):
    while True:
        s = input(yellow(f"{prompt} ")).strip().lower()
        if s == "h":
            if hint_code and hint_code in WIFI_HINTS:
                print(cyan("Hint:"), WIFI_HINTS[hint_code])
            else:
                print(yellow("No hint for this one."))
            continue
        if s.isdigit():
            v = int(s)
            if lo <= v <= hi:
                return v
        print(red(f"Enter a number between {lo} and {hi}, or 'h' for hint."))

def choose_study_set():
    print(bold("\nChoose your study set:"))
    print("1) Core (Network+)")
    print("2) Expanded (Full IEEE 802)")
    while True:
        s = input(yellow("Select 1–2: ")).strip()
        if s == "1":
            return STANDARDS_CORE[:]
        if s == "2":
            return STANDARDS_EXPANDED[:]
        print(red("Please enter 1 or 2."))

# ---------- Shared helpers ----------

def pick_n_unique(items, n):
    return random.sample(items, k=min(n, len(items)))

def make_mc_variants(target, pool, options=4):
    wrongs = [s for s in pool if s is not target]
    picks = pick_n_unique(wrongs, options - 1) + [target]
    random.shuffle(picks)
    # Variant A: code -> name
    prompt_a = bold(f"What does {target['code']} define? (type 'h' for hint)")
    choices_a = [p["name"] for p in picks]
    ans_a = picks.index(target)
    # Variant B: name -> code
    prompt_b = bold(f"Which code matches: {target['name']}? (type 'h' for hint)")
    choices_b = [p["code"] for p in picks]
    ans_b = picks.index(target)
    return (prompt_a, choices_a, ans_a), (prompt_b, choices_b, ans_b), picks

def make_mc_question(pool):
    correct = random.choice(pool)
    wrongs = [s for s in pool if s is not correct]
    picks = pick_n_unique(wrongs, 3) + [correct]
    random.shuffle(picks)
    return correct, picks

# ---------- Flashcards ----------

def mode_flashcards(pool):
    clear()
    print(bold("Flashcards — self-paced"))
    cards = pool[:]
    random.shuffle(cards)
    for s in cards:
        print(cyan("\n—"))
        print(bold(s["code"]), "-", s["name"])
        if s.get("aka"):
            aka = [a for a in s["aka"] if a]
            if aka:
                print(yellow("AKA:"), ", ".join(aka))
        print(s["summary"])
        ans = input(yellow("Press [Enter] for next, or type 'q' to quit: ")).strip().lower()
        if ans == "q":
            break
    print(green("\nFlashcard session complete."))

# ---------- SRS (text Anki) ----------

def load_srs():
    return load_json(SRS_FILE)

def ensure_cards_in_srs(data, pool):
    for s in pool:
        data.setdefault(s["code"], {"interval": 1, "due": 0, "seen": 0, "correct": 0})
    return data

def next_due_cards(data, pool):
    now = time.time()
    due = [s for s in pool if data[s["code"]]["due"] <= now]
    if not due:
        # if nothing is due yet, take the soonest one
        return [min(pool, key=lambda x: data[x["code"]]["due"])]
    return due

def update_card(data, code, success):
    now = time.time()
    d = data[code]
    d["seen"] += 1
    if success:
        d["correct"] += 1
        d["interval"] = min(int(d["interval"] * 2), 64)
    else:
        d["interval"] = 1
    # interval in minutes; multiply by 60 seconds
    d["due"] = now + d["interval"] * 60
    data[code] = d

def show_progress(data, pool):
    if not pool:
        print(yellow("No cards in this study set."))
        return
    levels = [data[s["code"]]["interval"] for s in pool]
    avg = sum(levels) / len(levels)
    mastered = sum(1 for s in pool if data[s["code"]]["interval"] >= 32)
    print(yellow(f"\nAverage interval (min): {avg:.1f}"))
    print(green(f"Cards mastered (interval >= 32): {mastered}/{len(pool)}"))

def mode_anki(pool):
    clear()
    print(bold("Anki — Spaced Repetition Review"))
    data = ensure_cards_in_srs(load_srs(), pool)
    session_reviewed = 0
    while True:
        due = next_due_cards(data, pool)
        random.shuffle(due)
        for s in due:
            clear()
            meta = data[s["code"]]
            print(cyan(f"{s['code']} — {s['name']}"))
            print(yellow(f"Interval: {meta['interval']}  Seen: {meta['seen']}  Correct: {meta['correct']}"))
            ans = input(yellow("Recall it, then press [Enter] to reveal (or 'q' to quit): ")).strip().lower()
            if ans == "q":
                save_json(SRS_FILE, data)
                print(green(f"\nSession complete. Reviewed {session_reviewed} cards."))
                show_progress(data, pool)
                press_enter()
                return
            print(bold("Summary ->"), s["summary"])
            success = input(green("Did you recall it correctly? (y/n): ")).strip().lower().startswith("y")
            update_card(data, s["code"], success)
            session_reviewed += 1
            time.sleep(0.2)

# ---------- Anki MC (full deck) ----------

def mode_anki_mc_full(pool):
    clear()
    print(bold("Anki MC — Full Deck Mastery"))
    print(yellow("Type 'h' for hint, 'q' to quit at any time.\n"))

    remaining = pool[:]  # cards not yet mastered
    random.shuffle(remaining)
    mastered = []
    total_attempts = 0
    correct_attempts = 0

    while remaining:
        card = remaining[0]
        total_attempts += 1

        clear()
        print(cyan(f"Card {len(mastered)+1}/{len(pool)}  |  Mastered: {len(mastered)}  |  Remaining: {len(remaining)}"))

        variant_a, variant_b, picks = make_mc_variants(card, pool)
        prompt, choices, answer_idx = random.choice([variant_a, variant_b])

        print(prompt)
        for i, ch in enumerate(choices, 1):
            print(f"  {i}) {ch}")

        user = input(yellow("\nYour choice ('h' for hint, 'q' to quit): ")).strip().lower()

        if user in ("q", "quit", "exit"):
            print(red("\nExiting early..."))
            press_enter()
            return

        if user == "h":
            if card["code"] in WIFI_HINTS:
                print(cyan("\nHint:"), WIFI_HINTS[card["code"]])
            else:
                print(yellow("\n(No hint for this standard.)"))
            time.sleep(1.5)
            continue

        if not user.isdigit():
            print(red("Invalid input. Try again."))
            time.sleep(1.2)
            continue

        guess = int(user) - 1
        if 0 <= guess < len(choices) and picks[guess] is card:
            print(green("\nCorrect!"))
            correct_attempts += 1
            mastered.append(card)
            remaining.pop(0)
            time.sleep(0.8)
        else:
            print(red("\nIncorrect."))
            print(yellow(f"Correct answer -> {choices[answer_idx]}"))
            # move card to end for retry
            remaining.append(remaining.pop(0))
            time.sleep(1.4)

    clear()
    accuracy = (correct_attempts / total_attempts) * 100 if total_attempts else 0.0
    print(green("All cards mastered!"))
    print(bold(f"Total Attempts: {total_attempts}"))
    print(bold(f"Accuracy: {accuracy:.1f}%"))
    press_enter()

# ---------- Games ----------

def mode_mc(pool, reverse=False):
    """10-question MC game with time-based bonuses."""
    clear()
    print(bold("Multiple Choice (10 questions with time bonuses)"))
    score = 0

    for q in range(10):
        correct, picks = make_mc_question(pool)
        print(cyan(f"\nQ{q+1}/10"))

        if reverse:
            print(bold(f"Which code matches: {correct['name']}? (type 'h' for hint)"))
            for i, p in enumerate(picks, 1):
                print(f"  {i}) {p['code']}")
        else:
            print(bold(f"What does {correct['code']} define? (type 'h' for hint)"))
            for i, p in enumerate(picks, 1):
                print(f"  {i}) {p['name']}")

        start = time.time()
        choice = ask_choice_with_hint("Your choice:", 1, len(picks), hint_code=correct["code"])
        elapsed = time.time() - start

        chosen = picks[choice - 1]
        if chosen is correct:
            # time-based bonus
            if elapsed < 2:
                points = 150
            elif elapsed < 5:
                points = 125
            else:
                points = 100
            score += points
            print(green(f"Correct in {elapsed:.1f}s -> +{points} points"))
        else:
            print(red(f"Incorrect. Correct was {correct['code']} — {correct['name']}"))

    print(bold(f"\nFinal Score: {score}"))
    key = "MC_Reverse_TimeBonus" if reverse else "MC_TimeBonus"
    record_score(key, score)
    press_enter()

def mode_streak(pool):
    clear()
    print(bold("Streak Survival — miss one and done"))
    streak = 0
    while True:
        correct, picks = make_mc_question(pool)
        print(cyan(f"\nWhat does {correct['code']} define? (type 'h' for hint)"))
        for i, p in enumerate(picks, 1):
            print(f"  {i}) {p['name']}")
        c = ask_choice_with_hint("Your choice:", 1, len(picks), hint_code=correct["code"])
        if picks[c - 1] is correct:
            streak += 1
            print(green(f"Correct! Streak {streak}"))
        else:
            print(red(f"Incorrect. Correct was {correct['code']} — {correct['name']}"))
            break
    print(bold(f"Final streak: {streak}"))
    record_score("Streak", streak)
    press_enter()

def mode_speedrun(pool, seconds=60):
    clear()
    print(bold("60s Speedrun (type 'h' for hint)"))
    score = 0
    start = time.time()

    def time_left():
        return max(0, int(seconds - (time.time() - start)))

    while time_left() > 0:
        correct, picks = make_mc_question(pool)
        print(cyan(f"\n{correct['code']} — {time_left()}s left"))
        for i, p in enumerate(picks, 1):
            print(f"  {i}) {p['name']}")
        try:
            c = ask_choice_with_hint("Your choice:", 1, len(picks), hint_code=correct["code"])
        except KeyboardInterrupt:
            print("\n" + yellow("Exiting early..."))
            break
        if picks[c - 1] is correct:
            score += 100
            print(green("Correct! +100"))
        else:
            score -= 25
            print(red(f"Incorrect. -25 (Correct: {correct['name']})"))
    print(bold(f"\nFinal Score: {score}"))
    record_score("Speedrun60", score)
    press_enter()

# ---------- Instructions ----------

INSTRUCTIONS = """
How to Use IEEE 802 Trainer v7

Study Set:
  - Core: Network+ essentials (802.3, 802.11 variants, 802.1Q, 802.1X, 802.15)
  - Expanded: Broader IEEE 802 family

Learning Modes:
  - Flashcards: simple front/back review.
  - Anki: text-based SRS. You self-grade (y/n) and intervals adjust.
  - Anki MC (Full Deck): multiple choice over the entire deck until each card
    has been answered correctly once. Wrong answers get recycled. Type 'h' for
    hints on Wi-Fi standards.

Games:
  - Multiple Choice (Code -> Name): 10 questions, time bonuses for faster answers.
  - Reverse Multiple Choice (Name -> Code): same but reversed.
  - Streak Survival: keep going until you miss one.
  - 60s Speedrun: answer as many as you can in 60s; correct +100, wrong -25.

Hints:
  - On any MC-style question, type 'h' to see mnemonic hints for Wi-Fi standards.
"""

# ---------- Menus ----------

def menu_learning(pool):
    while True:
        clear()
        print(bold("Learning Modes"))
        print("1) Flashcards")
        print("2) Anki (Spaced Repetition)")
        print("3) Anki MC (Full Deck Mastery)")
        print("4) Reset SRS Progress")
        print("5) Instructions")
        print("6) Back")
        c = ask_choice_with_hint("Choose (1-6):", 1, 6)
        if c == 1:
            mode_flashcards(pool)
        elif c == 2:
            mode_anki(pool)
        elif c == 3:
            mode_anki_mc_full(pool)
        elif c == 4:
            sure = input(red("Reset ALL SRS progress? (y/n): ")).strip().lower().startswith("y")
            if sure:
                try:
                    if os.path.exists(SRS_FILE):
                        os.remove(SRS_FILE)
                        print(green("SRS progress reset."))
                    else:
                        print(yellow("No SRS data found."))
                except Exception as e:
                    print(red(f"Could not reset SRS: {e}"))
                time.sleep(1.2)
        elif c == 5:
            clear()
            print(INSTRUCTIONS)
            press_enter()
        elif c == 6:
            return

def menu_games(pool):
    while True:
        clear()
        print(bold("Game Modes"))
        print("1) Multiple Choice (Code -> Name, time bonus)")
        print("2) Reverse MC (Name -> Code, time bonus)")
        print("3) Streak Survival")
        print("4) 60s Speedrun")
        print("5) Back")
        c = ask_choice_with_hint("Choose (1-5):", 1, 5)
        if c == 1:
            mode_mc(pool, reverse=False)
        elif c == 2:
            mode_mc(pool, reverse=True)
        elif c == 3:
            mode_streak(pool)
        elif c == 4:
            mode_speedrun(pool)
        elif c == 5:
            return

def main_menu():
    while True:
        clear()
        print(bold("IEEE 802 Trainer v7 — Time Bonus + Full-Deck Anki MC"))
        print("1) Learning Modes")
        print("2) Game Modes")
        print("3) View High Scores")
        print("4) Quit")
        c = ask_choice_with_hint("Choose (1-4):", 1, 4)
        if c == 1:
            pool = choose_study_set()
            menu_learning(pool)
        elif c == 2:
            pool = choose_study_set()
            menu_games(pool)
        elif c == 3:
            clear()
            print_high_scores()
            press_enter()
        elif c == 4:
            print(green("Goodbye!"))
            break

if __name__ == "__main__":
    try:
        random.seed()
        main_menu()
    except KeyboardInterrupt:
        print("\n" + yellow("Exited."))
