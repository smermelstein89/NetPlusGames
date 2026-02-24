#!/usr/bin/env python3
"""
Subnet Network Address Trainer — v1.0 (Cross-Platform)

Features
- Two games:
  A) Network Address Sprint (IP + CIDR -> network address)
  B) Block Range Challenge (same task, but shows the magic number hint)
- Per-question timer (default 7s), Speedrun and Streak modes
- Difficulty levels tweak timer and CIDR ranges
- High-score tracking in a JSON file
- Clean exit and robust input handling

Run:
  python subnet_network_trainer.py
"""

import ipaddress
import json
import os
import random
import sys
import time
from datetime import datetime

SCORE_FILE = "subnet_network_trainer_scores.json"

# ----------------------------- Utilities -----------------------------

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

def record_high_score(mode_key, difficulty_key, value):
    scores = load_scores()
    scores.setdefault(mode_key, {})
    prev = scores[mode_key].get(difficulty_key)
    if prev is None or value > prev:
        scores[mode_key][difficulty_key] = value
        save_scores(scores)
        return True
    return False

def get_high_score(mode_key, difficulty_key):
    scores = load_scores()
    return scores.get(mode_key, {}).get(difficulty_key)

def clear_screen():
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass

def pause(msg="Press Enter to continue..."):
    try:
        input(msg)
    except (EOFError, KeyboardInterrupt):
        pass

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ------------------------- Problem Generation ------------------------

PRIVATE_BLOCKS = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
]

def rand_private_ip():
    net = random.choice(PRIVATE_BLOCKS)
    # Pick a host at random (avoid .0 for cleanliness, but fine either way)
    ip_int = int(net.network_address) + random.randint(1, int(net.num_addresses) - 2)
    return ipaddress.IPv4Address(ip_int)

def rand_cidr(min_cidr=8, max_cidr=30):
    return random.randint(min_cidr, max_cidr)

def network_of(ip_str, cidr):
    net = ipaddress.IPv4Network(f"{ip_str}/{cidr}", strict=False)
    return str(net.network_address)

def magic_number_for_cidr(cidr):
    """
    Returns (octet_index, magic_number). octet_index is 1..4.
    """
    mask = ipaddress.IPv4Network(f"0.0.0.0/{cidr}").netmask.exploded  # e.g., '255.255.240.0'
    parts = list(map(int, mask.split(".")))
    for i, p in enumerate(parts):
        if p != 255:
            # magic number = 256 - mask_octet
            return (i + 1, 256 - p)
    return (4, 1)  # /32 case, degenerate (no change); default safe fallback

# --------------------------- Input Helpers ---------------------------

def timed_input(prompt, time_limit):
    """
    Cross-platform timing: measure elapsed time from prompt until input returns.
    If user exceeds time_limit, we still read their answer but mark as 'too slow'.
    Returns (answer_str, elapsed, timed_out_bool).
    """
    start = time.perf_counter()
    try:
        ans = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ("", time.perf_counter() - start, True)
    elapsed = time.perf_counter() - start
    return (ans, elapsed, elapsed > time_limit)

def validate_ip_str(s):
    try:
        ipaddress.IPv4Address(s)
        return True
    except Exception:
        return False

# ----------------------------- Difficulty ----------------------------

DIFFICULTIES = {
    "1": {"name": "Casual",   "per_q_time": 10.0, "min_cidr": 16, "max_cidr": 28},
    "2": {"name": "Standard", "per_q_time": 7.0,  "min_cidr": 12, "max_cidr": 28},
    "3": {"name": "Expert",   "per_q_time": 5.0,  "min_cidr": 8,  "max_cidr": 30},
}

def choose_difficulty():
    while True:
        clear_screen()
        print("🎮 Select Difficulty")
        for k, v in DIFFICULTIES.items():
            print(f" {k}) {v['name']}  – per-question time {v['per_q_time']}s, CIDR {v['min_cidr']}–{v['max_cidr']}")
        print(" Q) Back to main menu")
        choice = input("> ").strip().lower()
        if choice == "q":
            return None
        if choice in DIFFICULTIES:
            return DIFFICULTIES[choice]

# ------------------------------ Modes --------------------------------

def ask_network_question(show_magic=False, min_cidr=12, max_cidr=28, per_q_time=7.0):
    ip = str(rand_private_ip())
    cidr = rand_cidr(min_cidr, max_cidr)
    correct = network_of(ip, cidr)

    print("\nGiven:")
    print(f"  IP:   {ip}")
    print(f"  CIDR: /{cidr}")
    if show_magic:
        octet, mn = magic_number_for_cidr(cidr)
        print(f"  Hint: Magic number = {mn} in octet #{octet}")

    ans, elapsed, late = timed_input(f"→ Enter the network address: ", per_q_time)
    if ans.lower() in ("q", "quit", "exit"):
        return ("quit", 0.0)
    if not validate_ip_str(ans):
        print(f"✖ Invalid IP format. Correct: {correct}")
        return (False, elapsed)
    if late:
        print(f"⏱ Too slow ({elapsed:.2f}s ≥ {per_q_time:.0f}s). Correct: {correct}")
        return (False, elapsed)
    if ans == correct:
        print(f"✔ Correct in {elapsed:.2f}s!")
        return (True, elapsed)
    else:
        print(f"✖ Incorrect. You answered {ans}. Correct: {correct}")
        return (False, elapsed)

def mode_network_sprint(diff):
    """
    Classic: fixed per-question timer; score = correct answers (tie-breaker: total time).
    """
    clear_screen()
    print("🏁 Network Address Sprint — Classic")
    print("Type Q to quit any time.\n")
    total_correct = 0
    total_time = 0.0
    while True:
        res, elapsed = ask_network_question(
            show_magic=False,
            min_cidr=diff["min_cidr"],
            max_cidr=diff["max_cidr"],
            per_q_time=diff["per_q_time"],
        )
        if res == "quit":
            break
        if res:
            total_correct += 1
        total_time += elapsed
    print(f"\nResult: {total_correct} correct  | Total time: {total_time:.2f}s")
    mode_key = "classic"
    diff_key = diff["name"]
    is_high = record_high_score(mode_key, diff_key, total_correct)
    if is_high:
        print("🏆 New high score!")
    else:
        hs = get_high_score(mode_key, diff_key)
        if hs is not None:
            print(f"High score ({diff_key}): {hs}")
    pause()

def mode_speedrun(diff):
    """
    Speedrun: 60 seconds total. No per-question limit; just the global clock.
    """
    clear_screen()
    print("⏳ 60-Second Speedrun")
    print("Answer as many as you can in 60 seconds. Type Q to stop early.\n")
    duration = 60.0
    start = time.perf_counter()
    total_correct = 0
    attempts = 0
    while True:
        remaining = duration - (time.perf_counter() - start)
        if remaining <= 0:
            print("\nTime's up!")
            break

        # For fairness, cap a per-question soft limit to what's left, but do not force timeout
        per_q_soft = max(3.0, min(diff["per_q_time"], remaining))
        res, elapsed = ask_network_question(
            show_magic=False,
            min_cidr=diff["min_cidr"],
            max_cidr=diff["max_cidr"],
            per_q_time=per_q_soft,
        )
        if res == "quit":
            break
        attempts += 1
        if res:
            total_correct += 1

        if time.perf_counter() - start >= duration:
            print("\nTime's up!")
            break

    print(f"\nResult: {total_correct} correct in 60s (attempts: {attempts})")
    mode_key = "speedrun60"
    diff_key = diff["name"]
    is_high = record_high_score(mode_key, diff_key, total_correct)
    if is_high:
        print("🏆 New high score!")
    else:
        hs = get_high_score(mode_key, diff_key)
        if hs is not None:
            print(f"High score ({diff_key}): {hs}")
    pause()

def mode_streak(diff, show_magic=False):
    """
    Streak: go until you miss or time out. Score = longest streak this run.
    """
    clear_screen()
    title = "Streak (with Magic Hint)" if show_magic else "Streak"
    print(f"🔥 {title}")
    print("Go until you miss. Type Q to quit.\n")
    streak = 0
    best = 0
    while True:
        res, _ = ask_network_question(
            show_magic=show_magic,
            min_cidr=diff["min_cidr"],
            max_cidr=diff["max_cidr"],
            per_q_time=diff["per_q_time"],
        )
        if res == "quit":
            break
        if res:
            streak += 1
            best = max(best, streak)
            print(f"Streak: {streak}\n")
        else:
            print("Streak ended.\n")
            break
    print(f"Best streak: {best}")
    mode_key = "streak_magic" if show_magic else "streak"
    diff_key = diff["name"]
    is_high = record_high_score(mode_key, diff_key, best)
    if is_high:
        print("🏆 New high score!")
    else:
        hs = get_high_score(mode_key, diff_key)
        if hs is not None:
            print(f"High score ({diff_key}): {hs}")
    pause()

def mode_block_range_challenge(diff):
    """
    Block Range Challenge (learning assist):
    Shows the magic number hint for the decisive octet to reinforce block arithmetic.
    Still answer with the network address.
    """
    clear_screen()
    print("📦 Block Range Challenge (Magic Number Assist)")
    print("You’ll see IP, CIDR, and magic number hint. Compute the network address.\n")
    total_correct = 0
    total_time = 0.0
    rounds = 10
    for _ in range(rounds):
        res, elapsed = ask_network_question(
            show_magic=True,
            min_cidr=diff["min_cidr"],
            max_cidr=diff["max_cidr"],
            per_q_time=diff["per_q_time"],
        )
        if res == "quit":
            break
        if res:
            total_correct += 1
        total_time += elapsed
    print(f"\nScore: {total_correct}/{rounds} | Total time: {total_time:.2f}s")
    mode_key = "block_range_10"
    diff_key = diff["name"]
    is_high = record_high_score(mode_key, diff_key, total_correct)
    if is_high:
        print("🏆 New high score!")
    else:
        hs = get_high_score(mode_key, diff_key)
        if hs is not None:
            print(f"High score ({diff_key}): {hs}")
    pause()

# ------------------------------ Help ---------------------------------

INSTRUCTIONS = """
================ How to Play ================

Goal:
  Given an IPv4 address and a CIDR mask, compute the *network address*.

Refresher:
  • Convert (IP / CIDR) into a network: floor the IP to the nearest block boundary.
  • Programmatically: network = IPv4Network(f"{ip}/{cidr}", strict=False).network_address
  • “Magic number” shortcut:
      - Find the first mask octet that isn’t 255.
      - Magic number = 256 - that octet.
      - The network's value in that octet is the largest multiple of magic number ≤ the IP octet.

Example:
  IP = 192.168.35.67, CIDR = /20
  Mask = 255.255.240.0 -> magic number = 16 in the 3rd octet.
  35 floors to multiple of 16 -> 32
  → Network = 192.168.32.0

Games:
  A) Network Address Sprint
     - Classic: Per-question timer. Each correct = +1. Quit when you like.
     - Speedrun 60s: Score as many correct as you can in 60 seconds.
     - Streak: Go until your first miss or timeout.

  B) Block Range Challenge
     - Like Sprint, but we also show the magic number hint for the decisive octet.

Difficulty:
  • Casual: 10s/question, CIDR 16–28
  • Standard: 7s/question,  CIDR 12–28
  • Expert: 5s/question,    CIDR 8–30

Controls:
  • Type your answer as a dotted IPv4 address (e.g., 192.168.32.0)
  • Type Q to return/quit when prompted.

High Scores:
  • Stored per mode & difficulty in 'subnet_network_trainer_scores.json'

Tips:
  • Say the mask aloud to spot the octet that “changes”.
  • Use the magic number to snap the key octet down to its block boundary.
=============================================
"""

def show_instructions():
    clear_screen()
    print(INSTRUCTIONS)
    pause()

def show_high_scores():
    clear_screen()
    data = load_scores()
    if not data:
        print("No high scores yet.")
        pause()
        return
    print("🏆 High Scores\n")
    for mode, bydiff in data.items():
        print(f"[{mode}]")
        for d, val in bydiff.items():
            print(f"  {d}: {val}")
        print()
    pause()

# ------------------------------ Main ---------------------------------

def main_menu():
    while True:
        clear_screen()
        print("=== Subnet Network Address Trainer ===")
        print(f" {now_str()}")
        print("--------------------------------------")
        print(" 1) Play — Network Address Sprint (Classic)")
        print(" 2) Play — Speedrun (60 seconds)")
        print(" 3) Play — Streak")
        print(" 4) Play — Block Range Challenge (Magic Hint)")
        print(" 5) Streak with Magic Hint")
        print(" i) Instructions")
        print(" h) High Scores")
        print(" q) Quit")
        choice = input("> ").strip().lower()

        if choice == "q":
            print("Goodbye!")
            return
        elif choice == "i":
            show_instructions()
        elif choice == "h":
            show_high_scores()
        elif choice in ("1", "2", "3", "4", "5"):
            diff = choose_difficulty()
            if not diff:
                continue
            if choice == "1":
                mode_network_sprint(diff)
            elif choice == "2":
                mode_speedrun(diff)
            elif choice == "3":
                mode_streak(diff, show_magic=False)
            elif choice == "4":
                mode_block_range_challenge(diff)
            elif choice == "5":
                mode_streak(diff, show_magic=True)
        else:
            print("Invalid choice.")
            time.sleep(0.8)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting. Bye!")
