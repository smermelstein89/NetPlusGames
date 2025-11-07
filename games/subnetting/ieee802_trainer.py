#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IEEE 802 Trainer (Spaced Repetition Edition)
--------------------------------------------
CLI tool to memorize IEEE 802 standards using an Anki-like Leitner system.

✅ Cross-platform: macOS, Linux, Windows
✅ Saves progress between runs (ieee802_srs.json)
✅ Supports Core and Full study sets
✅ Recall ratings (1–5): again, hard, good, easy
✅ Promotes/demotes cards automatically
✅ Color-safe output

Run:  python3 ieee802_srs_trainer.py
"""

import json, os, random, sys, time
from datetime import datetime, timedelta

DATA_FILE = "ieee802_srs.json"
RNG = random.Random()

# -------- Color helpers --------
def c(code, text): return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text
def green(s): return c("92", s)
def red(s): return c("91", s)
def yellow(s): return c("93", s)
def cyan(s): return c("96", s)
def bold(s): return c("1", s)

# -------- Dataset (abbreviated for clarity, expand as desired) --------
STANDARDS = [
    {"code": "802.1D", "name": "Bridging / Spanning Tree (STP)"},
    {"code": "802.1Q", "name": "VLAN Tagging"},
    {"code": "802.1X", "name": "Port-Based Network Access Control"},
    {"code": "802.1AX", "name": "Link Aggregation (LACP)"},
    {"code": "802.3", "name": "Ethernet"},
    {"code": "802.3af", "name": "Power over Ethernet (PoE)"},
    {"code": "802.3at", "name": "PoE+ (Type 2)"},
    {"code": "802.3bt", "name": "PoE++ (Type 3/4)"},
    {"code": "802.11", "name": "Wireless LAN (Wi-Fi)"},
    {"code": "802.11n", "name": "Wi-Fi 4 (MIMO)"},
    {"code": "802.11ac", "name": "Wi-Fi 5 (VHT)"},
    {"code": "802.11ax", "name": "Wi-Fi 6/6E (OFDMA)"},
    {"code": "802.11i", "name": "WPA2 / RSN Security"},
    {"code": "802.15.1", "name": "Bluetooth"},
    {"code": "802.15.4", "name": "Low-Rate WPAN (Zigbee/Thread)"},
]

# -------- Persistence --------
def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # initialize new state
    return {s["code"]: {"name": s["name"], "box": 1, "next": None} for s in STANDARDS}

def save_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

# -------- Leitner parameters --------
BOX_INTERVALS = {
    1: timedelta(hours=0),   # review immediately (learning)
    2: timedelta(days=1),
    3: timedelta(days=3),
    4: timedelta(days=7),
    5: timedelta(days=14),
}

def due_cards(state):
    now = datetime.now()
    due = []
    for code, info in state.items():
        next_time = info.get("next")
        if not next_time or datetime.fromisoformat(next_time) <= now:
            due.append(code)
    return due

def schedule_next(info, rating):
    box = info["box"]
    if rating == 1:
        box = 1
    elif rating == 2:
        box = max(1, box - 1)
    elif rating == 3:
        box = min(5, box + 0)  # stay same
    elif rating == 4:
        box = min(5, box + 1)
    elif rating == 5:
        box = min(5, box + 2)

    interval = BOX_INTERVALS[box]
    next_time = datetime.now() + interval
    info["box"] = box
    info["next"] = next_time.isoformat()
    return info

# -------- Core / Full filter --------
CORE_CODES = {
    "802.1D","802.1Q","802.1X","802.1AX",
    "802.3","802.3af","802.3at","802.11","802.11n","802.11ac","802.11ax","802.11i","802.15.1","802.15.4"
}
def filter_set(state, core_only):
    if not core_only: return state
    return {k:v for k,v in state.items() if k in CORE_CODES}

# -------- Main loop --------
def clear(): os.system("cls" if os.name=="nt" else "clear")
def press_enter(): input(yellow("\n[Enter] to continue... "))

def study_session(core_only=False):
    state = load_state()
    subset = filter_set(state, core_only)
    cards = due_cards(subset)
    if not cards:
        print(green("✅ No cards due right now! Come back later."))
        return

    RNG.shuffle(cards)
    total = len(cards)
    print(bold(f"\n🧠 Starting review — {total} card(s) due\n"))
    correct = 0
    for i, code in enumerate(cards,1):
        info = state[code]
        print(cyan(f"\nCard {i}/{total}"))
        print(bold(f"Code: {info['name'] if RNG.random()<0.5 else code}"))
        input(yellow("Think of the answer, then press Enter to show it..."))
        print(f"{green('✔')} {bold(code)} — {info['name']}")
        print("How well did you recall?")
        print("1) Again (forgot)\n2) Hard\n3) Good\n4) Easy\n5) Very easy")
        while True:
            try:
                rating = int(input(yellow("Your rating (1–5): ")).strip())
                if 1 <= rating <= 5: break
            except ValueError:
                pass
            print(red("Enter a number 1–5"))
        schedule_next(info, rating)
        state[code] = info
        if rating >= 3: correct += 1
    save_state(state)
    print(green(f"\nSession complete! {correct}/{total} remembered."))

# -------- Menu --------
def main():
    while True:
        clear()
        print(bold("IEEE 802 Trainer — Spaced Repetition Edition"))
        print("1) Study (Core)\n2) Study (Full)\n3) View Progress\n4) Reset Progress\n5) Quit")
        sel = input(yellow("Select: ")).strip()
        if sel == "1":
            study_session(core_only=True)
            press_enter()
        elif sel == "2":
            study_session(core_only=False)
            press_enter()
        elif sel == "3":
            state = load_state()
            total = len(state)
            boxes = {b:0 for b in range(1,6)}
            for i in state.values(): boxes[i["box"]] += 1
            print(bold("\nProgress by Box:"))
            for b,cnt in boxes.items():
                print(f" Box {b}: {cnt}")
            print(f" Total cards: {total}")
            press_enter()
        elif sel == "4":
            if input(red("Type 'RESET' to confirm: ")).strip().upper() == "RESET":
                os.remove(DATA_FILE) if os.path.exists(DATA_FILE) else None
                print(yellow("Progress reset."))
            press_enter()
        elif sel == "5":
            print(green("Goodbye!"))
            break
        else:
            print(red("Invalid choice"))
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + yellow("Session ended."))
