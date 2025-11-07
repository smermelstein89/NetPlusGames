#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IEEE 802 Trainer — Memorize the 802 Standards (CLI)
---------------------------------------------------
✅ Cross-platform: macOS, Linux, Windows (Python 3.8+)
✅ Modes: Flashcards • Multiple Choice (Code→Name) • Reverse (Name→Code)
         Streak Survival • 60s Speedrun
✅ Study Sets: Core (most common for certs) or Full (broader coverage)
✅ High Scores: Saved locally per mode & study set
✅ Clean timing logic (no signals/threads), color-safe output

Run:
  macOS/Linux:  python3 ieee802_trainer.py
  Windows:      py ieee802_trainer.py

Tip: Resize your terminal for comfy reading.
"""

import json
import os
import random
import sys
import time
from datetime import datetime

SCORE_FILE = "ieee802_scores.json"
RNG = random.Random()

# ------------- ANSI Color (safe fallback on Windows) -------------
def supports_color():
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        # Windows 10+ usually supports ANSI in modern terminals; keep it simple
        return True
    return True

USE_COLOR = supports_color()

def c(code, text):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

def green(s): return c("92", s)
def red(s):   return c("91", s)
def yellow(s):return c("93", s)
def cyan(s):  return c("96", s)
def bold(s):  return c("1", s)

# ------------- Data: IEEE 802 Standards -------------
# Each entry: code, name, aka, summary, tag (core=True if commonly tested)
STANDARDS_FULL = [
    # 802 base umbrella
    {"code": "802", "name": "IEEE 802 Overview", "aka": ["802 family"], "summary": "LAN/MAN standards umbrella from physical to data link.", "core": False},
    # 802.1 family (bridging, VLANs, auth, LLDP, LACP, MACsec, etc.)
    {"code": "802.1D", "name": "Bridging & Spanning Tree (STP)", "aka": ["STP"], "summary": "Legacy STP for loop prevention in Layer 2 topologies.", "core": True},
    {"code": "802.1w", "name": "Rapid Spanning Tree (RSTP)", "aka": ["RSTP"], "summary": "Faster convergence than classic STP.", "core": True},
    {"code": "802.1s", "name": "Multiple Spanning Tree (MSTP)", "aka": ["MSTP"], "summary": "Maps VLANs into spanning tree instances.", "core": True},
    {"code": "802.1Q", "name": "VLAN Tagging", "aka": ["VLANs"], "summary": "Adds 802.1Q tag to Ethernet frames for VLAN identification.", "core": True},
    {"code": "802.1p", "name": "Layer 2 QoS/PCP", "aka": ["Class of Service"], "summary": "Priority bits (PCP) inside 802.1Q header for QoS.", "core": True},
    {"code": "802.1X", "name": "Port-Based Network Access Control", "aka": ["NAC", "EAP over LAN"], "summary": "Supplicant–Authenticator–RADIUS framework for access control.", "core": True},
    {"code": "802.1AB", "name": "LLDP", "aka": ["Link Layer Discovery Protocol"], "summary": "Vendor-neutral neighbor discovery at Layer 2.", "core": True},
    {"code": "802.1AX", "name": "Link Aggregation", "aka": ["LACP"], "summary": "Bundles links for redundancy/capacity; defines LACP.", "core": True},
    {"code": "802.1ad", "name": "Q-in-Q VLAN Stacking", "aka": ["Provider Bridging"], "summary": "Service provider VLAN tunneling of customer VLANs.", "core": False},
    {"code": "802.1AE", "name": "MACsec", "aka": ["MAC Security"], "summary": "Encryption and integrity for Layer 2 links.", "core": False},

    # 802.2 LLC (historical)
    {"code": "802.2", "name": "Logical Link Control", "aka": ["LLC"], "summary": "Upper sublayer of Data Link; largely historical.", "core": False},

    # 802.3 family (Ethernet, PoE)
    {"code": "802.3", "name": "Ethernet", "aka": [], "summary": "Wired LAN physical & MAC for Ethernet.", "core": True},
    {"code": "802.3u", "name": "Fast Ethernet", "aka": ["100BASE-TX"], "summary": "100 Mb/s Ethernet.", "core": True},
    {"code": "802.3ab", "name": "Gigabit Ethernet over Copper", "aka": ["1000BASE-T"], "summary": "1 Gb/s over twisted pair.", "core": True},
    {"code": "802.3z", "name": "Gigabit Ethernet over Fiber", "aka": ["1000BASE-SX/LX"], "summary": "1 Gb/s over fiber.", "core": True},
    {"code": "802.3ae", "name": "10 Gigabit Ethernet", "aka": ["10GbE"], "summary": "10 Gb/s Ethernet over fiber.", "core": True},
    {"code": "802.3an", "name": "10GBASE-T", "aka": ["10GbE Copper"], "summary": "10 Gb/s over copper (Cat6a).", "core": False},
    {"code": "802.3ba", "name": "40/100 Gigabit Ethernet", "aka": [], "summary": "Higher-speed Ethernet over fiber/copper.", "core": False},
    {"code": "802.3bj", "name": "100GbE Backplane/Copper", "aka": [], "summary": "High-speed backplane/copper specs.", "core": False},
    {"code": "802.3by", "name": "25 Gigabit Ethernet", "aka": ["25GbE"], "summary": "25 Gb/s Ethernet over fiber.", "core": False},
    {"code": "802.3cd", "name": "50/100/200 GbE (PAM4)", "aka": [], "summary": "Higher speeds using PAM4.", "core": False},
    {"code": "802.3ck", "name": "100/200/400 GbE Copper", "aka": [], "summary": "Electrical interfaces for very high speeds.", "core": False},
    {"code": "802.3af", "name": "Power over Ethernet (PoE)", "aka": ["PoE"], "summary": "Up to ~15.4W at PSE.", "core": True},
    {"code": "802.3at", "name": "PoE+ (Type 2)", "aka": ["PoE+"], "summary": "Up to ~30W at PSE.", "core": True},
    {"code": "802.3bt", "name": "PoE++ (Types 3/4)", "aka": ["4-pair PoE"], "summary": "Up to ~60–90W depending on class.", "core": True},

    # 802.11 family (Wi-Fi)
    {"code": "802.11", "name": "Wireless LAN (Wi-Fi)", "aka": ["Wi-Fi"], "summary": "Base Wi-Fi standard.", "core": True},
    {"code": "802.11a", "name": "5 GHz OFDM", "aka": [], "summary": "54 Mb/s in 5 GHz; legacy.", "core": True},
    {"code": "802.11b", "name": "2.4 GHz DSSS", "aka": [], "summary": "11 Mb/s in 2.4 GHz; legacy.", "core": True},
    {"code": "802.11g", "name": "2.4 GHz OFDM", "aka": [], "summary": "54 Mb/s in 2.4 GHz; legacy.", "core": True},
    {"code": "802.11n", "name": "Wi-Fi 4 (MIMO)", "aka": ["Wi-Fi 4"], "summary": "2.4/5 GHz; MIMO; higher throughput.", "core": True},
    {"code": "802.11ac", "name": "Wi-Fi 5 (VHT)", "aka": ["Wi-Fi 5"], "summary": "5 GHz; wider channels; MU-MIMO.", "core": True},
    {"code": "802.11ax", "name": "Wi-Fi 6/6E (OFDMA)", "aka": ["Wi-Fi 6", "Wi-Fi 6E"], "summary": "OFDMA, 2.4/5/6 GHz; improved efficiency.", "core": True},
    {"code": "802.11be", "name": "Wi-Fi 7 (EHT)", "aka": ["Wi-Fi 7"], "summary": "Even wider channels, Multi-Link Operation.", "core": False},
    {"code": "802.11i", "name": "Robust Security Networks", "aka": ["RSN"], "summary": "Introduced WPA2 (AES-CCMP).", "core": True},
    {"code": "802.11e", "name": "QoS Enhancements", "aka": ["WMM"], "summary": "Traffic prioritization for voice/video.", "core": False},
    {"code": "802.11k", "name": "Radio Resource Management", "aka": [], "summary": "Neighbor reports for roaming.", "core": False},
    {"code": "802.11r", "name": "Fast BSS Transition", "aka": ["Fast Roaming"], "summary": "Accelerates roaming handoffs.", "core": False},
    {"code": "802.11v", "name": "Wireless Network Management", "aka": [], "summary": "Network-assisted roaming/management.", "core": False},
    {"code": "802.11w", "name": "Protected Management Frames", "aka": ["PMF"], "summary": "Secures select 802.11 mgmt frames.", "core": False},

    # 802.15 (WPAN)
    {"code": "802.15.1", "name": "Bluetooth (classic)", "aka": ["Bluetooth"], "summary": "Short-range WPAN; classic Bluetooth base.", "core": True},
    {"code": "802.15.4", "name": "Low-Rate WPAN", "aka": ["Zigbee base", "Thread base"], "summary": "Basis for Zigbee/Thread (IoT).", "core": True},

    # 802.16, .17, .20, .21, .22 (less core)
    {"code": "802.16", "name": "WiMAX", "aka": [], "summary": "Broadband wireless MAN.", "core": False},
    {"code": "802.17", "name": "Resilient Packet Ring", "aka": ["RPR"], "summary": "Dual counter-rotating ring MANs.", "core": False},
    {"code": "802.20", "name": "Mobile Broadband Wireless Access", "aka": [], "summary": "Mobile MAN (historical).", "core": False},
    {"code": "802.21", "name": "Media-Independent Handover", "aka": [], "summary": "Handover across heterogeneous networks.", "core": False},
    {"code": "802.22", "name": "Wireless Regional Area Networks", "aka": ["WRAN"], "summary": "Cognitive radio in TV whitespace.", "core": False},
]

def study_set(core_only: bool):
    if core_only:
        return [s for s in STANDARDS_FULL if s["core"]]
    return list(STANDARDS_FULL)

# ------------- Persistence (High Scores) -------------
def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {}
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_scores(data):
    try:
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def record_score(mode_key, core_only, score, meta=None):
    tag = f"{mode_key}::{'CORE' if core_only else 'FULL'}"
    scores = load_scores()
    entry = {
        "score": score,
        "meta": meta or {},
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    scores.setdefault(tag, [])
    scores[tag].append(entry)
    # keep top 10 by score
    scores[tag] = sorted(scores[tag], key=lambda x: x["score"], reverse=True)[:10]
    save_scores(scores)

def print_high_scores():
    scores = load_scores()
    if not scores:
        print(yellow("No high scores yet. Play some rounds!"))
        return
    print(bold("\n🏆 High Scores"))
    for k in sorted(scores.keys()):
        print(cyan(f"\n{k}:"))
        for i, s in enumerate(scores[k], 1):
            meta = s.get("meta", {})
            extra = f"  ({meta.get('notes','')})" if meta.get("notes") else ""
            print(f"  {i:>2}. {s['score']:<5}  {s['ts']}{extra}")
    print("")

# ------------- Utility -------------
def clear():
    # Keep it simple and predictable
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def press_enter():
    input(yellow("\n[Enter] to continue... "))

def pick_n_unique(items, n):
    return RNG.sample(items, k=min(n, len(items)))

def ask_int(prompt, lo, hi):
    while True:
        s = input(prompt).strip()
        if s.isdigit():
            v = int(s)
            if lo <= v <= hi:
                return v
        print(red(f"Enter a number between {lo} and {hi}."))

# ------------- Instructions -------------
INSTRUCTIONS = f"""
{bold('How to Use IEEE 802 Trainer')}

Study Sets:
  • {bold('Core')}: most frequently cited/asked set (great for exams like Network+).
  • {bold('Full')}: broader coverage beyond the essentials.

Game Modes:
  1) {bold('Flashcards')} — Self-paced review. Flip terms and summaries quickly.
  2) {bold('Multiple Choice (Code → Name)')} — Given a code like 802.1Q, pick the correct name.
  3) {bold('Reverse (Name → Code)')} — Given the name/summary, choose the code.
  4) {bold('Streak Survival')} — Keep answering MC questions until you miss one.
  5) {bold('60s Speedrun')} — Answer as many as you can in 60 seconds.

Scoring:
  • Multiple Choice & Reverse: +100 for correct, 0 for wrong.
  • Streak Survival: score = consecutive correct answers.
  • Speedrun: +100 per correct, -25 per wrong; time-boxed to 60 seconds.
  • High scores are saved per mode and study set.

Tips:
  • Start with Flashcards (Core) to build the mental map.
  • Move to Multiple Choice, then Reverse.
  • Use Streak and Speedrun to pressure-test recall.
  • Revisit Full set to expand your horizon.

Good luck! {green('You got this.')}
"""

# ------------- Game Logic -------------
def mode_flashcards(pool):
    clear()
    print(bold("📇 Flashcards — self-paced"))
    cards = pool[:]
    RNG.shuffle(cards)
    for s in cards:
        print(cyan("\n—"))
        print(bold(s["code"]), "-", s["name"])
        if s["aka"]:
            print(yellow("AKA:"), ", ".join(s["aka"]))
        print(s["summary"])
        ans = input(yellow("Press [Enter] for next, or type 'q' to quit: ")).strip().lower()
        if ans == "q":
            break
    print(green("\nFlashcard session complete."))

def make_mc_question_code_to_name(pool, options=4):
    correct = RNG.choice(pool)
    wrongs = [s for s in pool if s is not correct]
    picks = pick_n_unique(wrongs, options - 1) + [correct]
    RNG.shuffle(picks)
    return correct, picks

def make_mc_question_name_to_code(pool, options=4):
    correct = RNG.choice(pool)
    wrongs = [s for s in pool if s is not correct]
    picks = pick_n_unique(wrongs, options - 1) + [correct]
    RNG.shuffle(picks)
    return correct, picks

def mode_mc(pool, reverse=False, rounds=10):
    clear()
    title = "🧠 Multiple Choice — Name → Code" if reverse else "🧠 Multiple Choice — Code → Name"
    print(bold(title))
    score = 0
    for r in range(1, rounds + 1):
        print(cyan(f"\nQ{r}/{rounds}"))
        if reverse:
            correct, picks = make_mc_question_name_to_code(pool)
            print(bold(f"Which code matches this?"))
            print(f"Name: {correct['name']}")
            if correct["aka"]:
                print(yellow("AKA:"), ", ".join(correct["aka"]))
            print(f"Summary: {correct['summary']}")
            for i, p in enumerate(picks, 1):
                print(f"  {i}) {p['code']}")
        else:
            correct, picks = make_mc_question_code_to_name(pool)
            print(bold(f"What does {correct['code']} define?"))
            for i, p in enumerate(picks, 1):
                aka = f"  [{', '.join(p['aka'])}]" if p['aka'] else ""
                print(f"  {i}) {p['name']}{aka}")
        choice = ask_int(yellow("Your choice: "), 1, len(picks))
        chosen = picks[choice - 1]
        is_correct = (chosen is correct)
        if is_correct:
            print(green("✔ Correct! +100"))
            score += 100
        else:
            print(red(f"✘ Incorrect. Correct answer: {correct['code']} — {correct['name']}"))
    print(bold(f"\nFinal Score: {score}"))
    return score

def mode_streak(pool):
    clear()
    print(bold("🔥 Streak Survival — miss one and done"))
    score = 0
    qn = 0
    while True:
        qn += 1
        print(cyan(f"\nQ{qn}"))
        correct, picks = make_mc_question_code_to_name(pool)
        print(bold(f"What does {correct['code']} define?"))
        for i, p in enumerate(picks, 1):
            aka = f"  [{', '.join(p['aka'])}]" if p['aka'] else ""
            print(f"  {i}) {p['name']}{aka}")
        choice = ask_int(yellow("Your choice: "), 1, len(picks))
        chosen = picks[choice - 1]
        if chosen is correct:
            score += 1
            print(green(f"✔ Correct! Streak: {score}"))
        else:
            print(red(f"✘ Incorrect. Correct answer: {correct['code']} — {correct['name']}"))
            print(bold(f"\nYour streak: {score}"))
            return score

def mode_speedrun(pool, seconds=60):
    clear()
    print(bold(f"⏱ 60s Speedrun — answer as many as you can"))
    start = time.time()
    score = 0
    qn = 0

    def time_left():
        return max(0.0, seconds - (time.time() - start))

    while time_left() > 0:
        qn += 1
        print(cyan(f"\nQ{qn} — {time_left():.0f}s left"))
        # Randomly choose direction to keep it spicy
        reverse = RNG.random() < 0.4
        if reverse:
            correct, picks = make_mc_question_name_to_code(pool)
            print(bold(f"Which code matches this?"))
            print(f"Name: {correct['name']}")
            if correct["aka"]:
                print(yellow("AKA:"), ", ".join(correct["aka"]))
            print(f"Summary: {correct['summary']}")
            for i, p in enumerate(picks, 1):
                print(f"  {i}) {p['code']}")
        else:
            correct, picks = make_mc_question_code_to_name(pool)
            print(bold(f"What does {correct['code']} define?"))
            for i, p in enumerate(picks, 1):
                aka = f"  [{', '.join(p['aka'])}]" if p['aka'] else ""
                print(f"  {i}) {p['name']}{aka}")
        # Time-aware input: if time expires mid-question, we’ll still accept and tally
        choice = None
        while choice is None:
            try:
                choice = ask_int(yellow("Your choice: "), 1, len(picks))
            except KeyboardInterrupt:
                print("\n" + yellow("Exiting Speedrun early..."))
                return max(0, score)
        chosen = picks[choice - 1]
        if chosen is correct:
            print(green("✔ Correct! +100"))
            score += 100
        else:
            print(red(f"✘ Incorrect. −25"))
            print(yellow(f"Correct: {correct['code']} — {correct['name']}"))
            score -= 25
    print(bold(f"\nFinal Score: {score}"))
    return max(0, score)

# ------------- Menus -------------
def choose_study_set():
    print(bold("\n📚 Choose a study set:"))
    print("1) Core (most likely to appear on certs & interviews)")
    print("2) Full (broader coverage)")
    sel = ask_int(yellow("Select 1–2: "), 1, 2)
    return sel == 1

def main_menu():
    clear()
    print(bold("IEEE 802 Trainer"))
    print("Memorize the 802 standards fast—mix modes, track scores, master both core and full sets.\n")
    print(bold("Main Menu"))
    print("1) Instructions")
    print("2) Flashcards")
    print("3) Multiple Choice (Code → Name)")
    print("4) Reverse (Name → Code)")
    print("5) Streak Survival")
    print("6) 60s Speedrun")
    print("7) View High Scores")
    print("8) Quit")
    return ask_int(yellow("Choose 1–8: "), 1, 8)

def run():
    RNG.seed()  # system entropy
    while True:
        sel = main_menu()
        if sel == 1:
            clear()
            print(INSTRUCTIONS)
            press_enter()

        elif sel in (2, 3, 4, 5, 6):
            core_only = choose_study_set()
            pool = study_set(core_only)
            if not pool:
                print(red("No items in selected study set!"))
                press_enter()
                continue

            if sel == 2:
                mode_flashcards(pool)
            elif sel == 3:
                score = mode_mc(pool, reverse=False, rounds=10)
                record_score("MC_CodeToName", core_only, score, {"notes": "10 Q"})
            elif sel == 4:
                score = mode_mc(pool, reverse=True, rounds=10)
                record_score("MC_NameToCode", core_only, score, {"notes": "10 Q"})
            elif sel == 5:
                score = mode_streak(pool)
                record_score("Streak", core_only, score, {"notes": "Longest run in a session"})
            elif sel == 6:
                score = mode_speedrun(pool, seconds=60)
                record_score("Speedrun60", core_only, score, {"notes": "60s round"})
            press_enter()

        elif sel == 7:
            clear()
            print_high_scores()
            press_enter()

        elif sel == 8:
            print(green("\nThanks for training! See you next session."))
            break

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n" + yellow("Session ended. Goodbye!"))
