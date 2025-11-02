#!/usr/bin/env python3
"""
Changing Octet Challenge v2 — Reflex & Score Edition
----------------------------------------------------
Train subnet reflexes by identifying which octet changes for any CIDR prefix or subnet mask.

Features:
 - Increasing difficulty (starts with /24–/30, expands with score)
 - Time bonuses and penalties
 - Combo multipliers
 - High-score persistence
"""

import ipaddress, random, time, json, os, sys

PROGRESS_FILE = "subnet_snap_progress.json"

# Difficulty thresholds (score → allowed CIDR range)
DIFFICULTY = [
    (0,   range(24, 31)),  # easy: 4th octet
    (15,  range(16, 31)),  # medium: add 3rd octet
    (30,  range(8, 31)),   # hard: add 2nd octet
    (50,  range(0, 31)),   # expert: all octets
]

BASE_POINTS = 100       # base per correct answer
BONUS_MULTIPLIER = 1.5  # combo boost per 5-streak
TIME_BONUS_CUTOFF = 3.0 # seconds threshold for speed bonus
TIME_PENALTY_CUTOFF = 6.0 # slow answer penalty
HINT_PENALTY = 50
WRONG_PENALTY = 75

# ---------- Utilities ----------
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
            with open(PROGRESS_FILE,"r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"changing_octet_highscore": 0, "changing_octet_best_streak": 0}

def save_progress(p):
    with open(PROGRESS_FILE,"w") as f: json.dump(p,f,indent=2)

def pick_cidr(score:int):
    """Pick CIDR range based on difficulty thresholds."""
    allowed = range(24,31)
    for threshold, rng in DIFFICULTY:
        if score >= threshold:
            allowed = rng
    return random.choice(allowed)

# ---------- Game ----------
def play():
    progress = load_progress()
    highscore = progress.get("changing_octet_highscore",0)
    best_streak = progress.get("changing_octet_best_streak",0)
    score = 0
    streak = 0
    multiplier = 1.0

    print("=== 🧮 Changing Octet Challenge v2 — Reflex & Score Edition ===")
    print("Type which octet (1–4) changes for the given CIDR or mask.")
    print("Earn points for fast, correct answers. 10+ streak = big combos!")
    print("Use 'h' for a hint (-50 pts), 'q' to quit.\n")

    while True:
        cidr = pick_cidr(score)
        mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
        question_type = random.choice(["cidr","mask"])
        display = f"/{cidr}" if question_type=="cidr" else mask
        label = "CIDR" if question_type=="cidr" else "Subnet Mask"

        print(f"📘 {label}: {display}")
        start=time.time()
        ans=input("👉 Which octet changes (1–4)? ").strip().lower()
        elapsed=time.time()-start

        if ans in ("q","quit","exit"):
            break
        if ans in ("h","hint"):
            print(visual_explanation(cidr))
            score=max(0,score-HINT_PENALTY)
            print(f"🔹 Hint used (-{HINT_PENALTY} pts). Score:{score}\n")
            continue
        if not ans.isdigit() or not (1<=int(ans)<=4):
            print("Please enter 1–4, 'h', or 'q'.\n")
            continue

        ans_int=int(ans)
        correct=detect_changing_octet(cidr)

        if ans_int==correct:
            base=BASE_POINTS
            # speed bonus
            if elapsed<=TIME_BONUS_CUTOFF: base+=50
            elif elapsed>TIME_PENALTY_CUTOFF: base-=25
            # combo multiplier
            if streak and streak%5==0: multiplier*=BONUS_MULTIPLIER; print("🔥 Combo multiplier increased!")
            points=int(base*multiplier)
            score+=points
            streak+=1
            best_streak=max(best_streak,streak)
            print(f"✅ Correct! Changing octet:{correct} ({['1st','2nd','3rd','4th'][correct-1]})")
            print(f"⏱ {elapsed:.1f}s | +{points} pts | Score:{score} | Streak:{streak} | x{multiplier:.1f}\n")
        else:
            print(f"❌ Wrong! It was {correct} ({['1st','2nd','3rd','4th'][correct-1]}).")
            print(visual_explanation(cidr))
            score=max(0,score-WRONG_PENALTY)
            streak=0
            multiplier=1.0
            print(f"💀 -{WRONG_PENALTY} pts | Score:{score} | Streak reset.\n")

    # Save progress
    progress["changing_octet_highscore"]=max(progress.get("changing_octet_highscore",0),score)
    progress["changing_octet_best_streak"]=max(progress.get("changing_octet_best_streak",0),best_streak)
    save_progress(progress)

    print("\n=== Session Summary ===")
    print(f"Final Score:{score} | Best Streak:{best_streak}")
    print(f"🏆 High Score:{progress['changing_octet_highscore']} | Longest Streak:{progress['changing_octet_best_streak']}")
    print("Progress saved. Great job refining those subnet reflexes!")

# ---------- Main ----------
if __name__=="__main__":
    try: play()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
