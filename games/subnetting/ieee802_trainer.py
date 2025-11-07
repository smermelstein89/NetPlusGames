#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IEEE 802 Trainer v5 — Cross‑Platform, Core+Expanded, Anki MC Mastery
--------------------------------------------------------------------
✅ Cross‑platform: Windows, macOS, Linux (Python 3.8+)
✅ Study set chooser: Core (Network+) or Expanded (full family)
✅ Learning Modes:
   • Flashcards
   • Anki (Spaced Repetition)
   • Anki MC (Single‑Card Mastery: answer MC until 2 correct, then done)
   • Reset SRS Progress
   • Instructions
✅ Game Modes: Multiple Choice, Reverse, Streak, 60s Speedrun
✅ Persistence: High scores (JSON) + SRS progress (JSON)
"""

import json, os, random, sys, time
from datetime import datetime

# -------- Files --------
SCORE_FILE = "ieee802_scores.json"
SRS_FILE   = "ieee802_srs.json"
RNG = random.Random()

# -------- Colors (safe) --------
def _tty(): 
    try: return sys.stdout.isatty()
    except: return False
def _c(code, t): return f"\033[{code}m{t}\033[0m" if _tty() else t
def green(s):  return _c("92", s)
def red(s):    return _c("91", s)
def yellow(s): return _c("93", s)
def cyan(s):   return _c("96", s)
def bold(s):   return _c("1", s)

# -------- Datasets --------
# Core set — Network+ relevant
STANDARDS_CORE = [
    {"code":"802.1Q","name":"VLAN Tagging","aka":[],"summary":"Adds VLAN ID to Ethernet frames for segmentation.","core":True},
    {"code":"802.1X","name":"Port‑Based Access Control","aka":["NAC","EAPoL"],"summary":"Authenticates devices at the switch/AP using RADIUS.","core":True},
    {"code":"802.3","name":"Ethernet","aka":[],"summary":"Wired LAN physical & MAC (copper & fiber).","core":True},
    {"code":"802.11a","name":"Wi‑Fi 1","aka":[],"summary":"5 GHz, 54 Mb/s, OFDM (legacy).","core":True},
    {"code":"802.11b","name":"Wi‑Fi 2","aka":[],"summary":"2.4 GHz, 11 Mb/s, DSSS (legacy).","core":True},
    {"code":"802.11g","name":"Wi‑Fi 3","aka":[],"summary":"2.4 GHz, 54 Mb/s, OFDM (legacy).","core":True},
    {"code":"802.11n","name":"Wi‑Fi 4","aka":[],"summary":"2.4/5 GHz, MIMO, up to 600 Mb/s.","core":True},
    {"code":"802.11ac","name":"Wi‑Fi 5","aka":[],"summary":"5 GHz, MU‑MIMO, 80/160 MHz channels.","core":True},
    {"code":"802.11ax","name":"Wi‑Fi 6/6E","aka":[],"summary":"2.4/5/6 GHz, OFDMA, improved efficiency.","core":True},
    {"code":"802.15.1","name":"Bluetooth (classic)","aka":["Bluetooth"],"summary":"Short‑range WPAN personal networking.","core":True},
    {"code":"802.15.4","name":"Low‑Rate WPAN","aka":["Zigbee/Thread base"],"summary":"IoT mesh foundations at low power/data rates.","core":True},
]

# Expanded set — fuller 802 family (curated)
STANDARDS_EXPANDED = [
    # Umbrella
    {"code":"802","name":"IEEE 802 Overview","aka":["802 family"],"summary":"LAN/MAN standards umbrella.","core":False},
    # 802.1 family
    {"code":"802.1D","name":"Bridging & Spanning Tree (STP)","aka":["STP"],"summary":"Loop prevention in Layer 2 topologies.","core":True},
    {"code":"802.1w","name":"Rapid Spanning Tree (RSTP)","aka":["RSTP"],"summary":"Faster convergence vs. STP.","core":True},
    {"code":"802.1s","name":"Multiple Spanning Tree (MSTP)","aka":["MSTP"],"summary":"Maps VLANs to STP instances.","core":True},
    {"code":"802.1Q","name":"VLAN Tagging","aka":["VLANs"],"summary":"802.1Q tag in Ethernet frames for VLAN ID.","core":True},
    {"code":"802.1p","name":"Layer 2 QoS/PCP","aka":["Class of Service"],"summary":"Priority bits inside 802.1Q header.","core":True},
    {"code":"802.1X","name":"Port‑Based Network Access Control","aka":["NAC","EAPoL"],"summary":"Supplicant–Authenticator–RADIUS framework.","core":True},
    {"code":"802.1AB","name":"LLDP","aka":["Link Layer Discovery Protocol"],"summary":"Vendor‑neutral neighbor discovery.","core":True},
    {"code":"802.1AX","name":"Link Aggregation","aka":["LACP"],"summary":"Bundles links for redundancy/capacity.","core":True},
    {"code":"802.1ad","name":"Q‑in‑Q VLAN Stacking","aka":["Provider Bridging"],"summary":"SP VLAN tunneling of customer VLANs.","core":False},
    {"code":"802.1AE","name":"MACsec","aka":["MAC Security"],"summary":"L2 link encryption & integrity.","core":False},
    # 802.2
    {"code":"802.2","name":"Logical Link Control","aka":["LLC"],"summary":"Upper sublayer of Data Link (historical).","core":False},
    # 802.3 Ethernet family
    {"code":"802.3","name":"Ethernet","aka":[],"summary":"Wired LAN physical & MAC for Ethernet.","core":True},
    {"code":"802.3u","name":"Fast Ethernet","aka":["100BASE‑TX"],"summary":"100 Mb/s Ethernet.","core":True},
    {"code":"802.3ab","name":"Gigabit Ethernet over Copper","aka":["1000BASE‑T"],"summary":"1 Gb/s over twisted pair.","core":True},
    {"code":"802.3z","name":"Gigabit Ethernet over Fiber","aka":["1000BASE‑SX/LX"],"summary":"1 Gb/s over fiber.","core":True},
    {"code":"802.3ae","name":"10 Gigabit Ethernet","aka":["10GbE"],"summary":"10 Gb/s Ethernet over fiber.","core":True},
    {"code":"802.3an","name":"10GBASE‑T","aka":["10GbE Copper"],"summary":"10 Gb/s over copper (Cat6a).","core":False},
    {"code":"802.3ba","name":"40/100 Gigabit Ethernet","aka":[],"summary":"Higher‑speed Ethernet.","core":False},
    {"code":"802.3bj","name":"100GbE Backplane/Copper","aka":[],"summary":"High‑speed backplane/copper specs.","core":False},
    {"code":"802.3by","name":"25 Gigabit Ethernet","aka":["25GbE"],"summary":"25 Gb/s Ethernet.","core":False},
    {"code":"802.3cd","name":"50/100/200 GbE (PAM4)","aka":[],"summary":"Higher speeds via PAM4.","core":False},
    {"code":"802.3ck","name":"100/200/400 GbE Copper","aka":[],"summary":"Very high‑speed electrical interfaces.","core":False},
    {"code":"802.3af","name":"Power over Ethernet (PoE)","aka":["PoE"],"summary":"~15.4W at PSE.","core":True},
    {"code":"802.3at","name":"PoE+ (Type 2)","aka":["PoE+"],"summary":"~30W at PSE.","core":True},
    {"code":"802.3bt","name":"PoE++ (Types 3/4)","aka":["4‑pair PoE"],"summary":"~60–90W depending on class.","core":True},
    # 802.11 Wi‑Fi family
    {"code":"802.11","name":"Wireless LAN (Wi‑Fi)","aka":["Wi‑Fi"],"summary":"Base Wi‑Fi standard.","core":True},
    {"code":"802.11a","name":"Wi‑Fi 1","aka":[],"summary":"5 GHz; 54 Mb/s.","core":True},
    {"code":"802.11b","name":"Wi‑Fi 2","aka":[],"summary":"2.4 GHz; 11 Mb/s.","core":True},
    {"code":"802.11g","name":"Wi‑Fi 3","aka":[],"summary":"2.4 GHz; 54 Mb/s.","core":True},
    {"code":"802.11n","name":"Wi‑Fi 4 (MIMO)","aka":["Wi‑Fi 4"],"summary":"2.4/5 GHz; MIMO.","core":True},
    {"code":"802.11ac","name":"Wi‑Fi 5 (VHT)","aka":["Wi‑Fi 5"],"summary":"5 GHz; MU‑MIMO; 80/160 MHz.","core":True},
    {"code":"802.11ax","name":"Wi‑Fi 6/6E (OFDMA)","aka":["Wi‑Fi 6","Wi‑Fi 6E"],"summary":"2.4/5/6 GHz; efficiency.","core":True},
    {"code":"802.11be","name":"Wi‑Fi 7 (EHT)","aka":["Wi‑Fi 7"],"summary":"Wider channels; MLO.","core":False},
    {"code":"802.11i","name":"Robust Security Networks","aka":["RSN"],"summary":"Introduced WPA2 (AES‑CCMP).","core":True},
    {"code":"802.11e","name":"QoS Enhancements","aka":["WMM"],"summary":"Traffic prioritization.","core":False},
    {"code":"802.11k","name":"Radio Resource Mgmt","aka":[],"summary":"Neighbor reports for roaming.","core":False},
    {"code":"802.11r","name":"Fast BSS Transition","aka":["Fast Roaming"],"summary":"Accelerates roaming handoffs.","core":False},
    {"code":"802.11v","name":"Wireless Network Mgmt","aka":[],"summary":"Network‑assisted roaming/management.","core":False},
    {"code":"802.11w","name":"Protected Mgmt Frames","aka":["PMF"],"summary":"Secures select mgmt frames.","core":False},
    # 802.15
    {"code":"802.15.1","name":"Bluetooth (classic)","aka":["Bluetooth"],"summary":"Short‑range WPAN.","core":True},
    {"code":"802.15.4","name":"Low‑Rate WPAN","aka":["Zigbee base","Thread base"],"summary":"IoT low‑power mesh.","core":True},
    # Others
    {"code":"802.16","name":"WiMAX","aka":[],"summary":"Broadband wireless MAN.","core":False},
    {"code":"802.17","name":"Resilient Packet Ring","aka":["RPR"],"summary":"Dual counter‑rotating ring MANs.","core":False},
    {"code":"802.20","name":"Mobile Broadband Wireless Access","aka":[],"summary":"Mobile MAN (historical).","core":False},
    {"code":"802.21","name":"Media‑Independent Handover","aka":[],"summary":"Handover across heterogeneous nets.","core":False},
    {"code":"802.22","name":"Wireless Regional Area Networks","aka":["WRAN"],"summary":"Cognitive radio in TV whitespace.","core":False},
]

# Utility to choose dataset
def choose_study_set():
    print(bold("\n📚 Choose your study set:"))
    print("1) Core (Network+)")
    print("2) Expanded (Full IEEE 802)")
    while True:
        s = input(yellow("Select 1–2: ")).strip()
        if s in ("1","2"): return STANDARDS_CORE if s=="1" else STANDARDS_EXPANDED
        print(red("Please enter 1 or 2."))

# -------- Persistence --------
def load_json(p):
    if not os.path.exists(p): return {}
    try: return json.load(open(p,"r",encoding="utf-8"))
    except: return {}
def save_json(p,d):
    try: json.dump(d, open(p,"w",encoding="utf-8"), indent=2)
    except: pass

def record_score(mode_key, score):
    scores = load_json(SCORE_FILE)
    entry = {"score":score,"ts":datetime.now().isoformat(timespec="seconds")}
    scores.setdefault(mode_key,[]).append(entry)
    scores[mode_key] = sorted(scores[mode_key], key=lambda x: x["score"], reverse=True)[:10]
    save_json(SCORE_FILE, scores)

def print_high_scores():
    scores = load_json(SCORE_FILE)
    if not scores:
        print(yellow("No high scores yet.")); return
    print(bold("\n🏆 High Scores"))
    for k in sorted(scores.keys()):
        print(cyan(f"\n{k}:"))
        for i,s in enumerate(scores[k],1):
            print(f" {i:>2}. {s['score']}  {s['ts']}")
    print()

# -------- UI helpers --------
def clear():
    try: os.system("cls" if os.name=="nt" else "clear")
    except: pass
def press_enter():
    try: input(yellow("\n[Enter] to continue... "))
    except EOFError: pass
def ask_int(prompt, lo, hi):
    while True:
        s = input(prompt).strip()
        if s.isdigit():
            v = int(s)
            if lo <= v <= hi: return v
        print(red(f"Enter a number between {lo} and {hi}."))

# -------- Shared quiz helpers --------
def pick_n_unique(items, n):
    return random.sample(items, k=min(n, len(items)))

def make_mc_variants(target, pool, options=4):
    """Return two MC variants: (code->name) and (name->code) tuples of (prompt, choices, answer_index)."""
    # Build choices
    wrongs = [s for s in pool if s is not target]
    picks = pick_n_unique(wrongs, options-1) + [target]
    random.shuffle(picks)
    # Variant A: Code -> Name
    prompt_a = bold(f"What does {target['code']} define?")
    choices_a = [p["name"] for p in picks]
    ans_a = picks.index(target)
    # Variant B: Name -> Code
    prompt_b = bold(f"Which code matches: {target['name']}?")
    choices_b = [p["code"] for p in picks]
    ans_b = picks.index(target)
    return (prompt_a, choices_a, ans_a), (prompt_b, choices_b, ans_b)

# -------- Learning: Flashcards --------
def mode_flashcards(pool):
    clear(); print(bold("📇 Flashcards — self‑paced"))
    cards = pool[:]; random.shuffle(cards)
    for s in cards:
        print(cyan("\n—")); print(bold(s["code"]), "-", s["name"])
        if s.get("aka"): 
            aka = [a for a in s["aka"] if a]
            if aka: print(yellow("AKA:"), ", ".join(aka))
        print(s["summary"])
        ans = input(yellow("Press [Enter] for next, or type 'q' to quit: ")).strip().lower()
        if ans == "q": break
    print(green("\nFlashcard session complete."))

# -------- Learning: Anki (SRS) --------
def load_srs():
    data = load_json(SRS_FILE)
    # Initialize defaults on demand (done per study session)
    return data

def ensure_cards_in_srs(data, pool):
    for s in pool:
        data.setdefault(s["code"], {"interval":1,"due":0,"seen":0,"correct":0})
    return data

def next_due_cards(data, pool):
    now = time.time()
    due = [s for s in pool if data[s["code"]]["due"] <= now]
    if not due:
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
    d["due"] = now + d["interval"] * 60  # minutes for demo scale; change to *3600 for hours
    data[code] = d

def show_progress(data, pool):
    if not pool: 
        print(yellow("No cards in this study set.")); return
    levels = [data[s["code"]]["interval"] for s in pool]
    avg = sum(levels)/len(levels)
    mastered = sum(1 for s in pool if data[s["code"]]["interval"] >= 32)
    print(yellow(f"\nAverage interval (min): {avg:.1f}"))
    print(green(f"Cards mastered (interval ≥ 32): {mastered}/{len(pool)}"))

def mode_anki(pool):
    clear(); print(bold("🧩 Anki — Spaced Repetition Review"))
    data = ensure_cards_in_srs(load_srs(), pool)
    session_reviewed = 0
    while True:
        due = next_due_cards(data, pool); random.shuffle(due)
        for s in due:
            clear(); meta = data[s["code"]]
            print(cyan(f"{s['code']} — {s['name']}"))
            print(yellow(f"Interval:{meta['interval']}  Seen:{meta['seen']}  Correct:{meta['correct']}"))
            _ = input(yellow("Recall the summary, then press [Enter] to reveal (or 'q' to quit): ")).strip().lower()
            if _ == "q":
                save_json(SRS_FILE, data)
                print(green(f"\nSession complete. Reviewed {session_reviewed} cards."))
                show_progress(data, pool); press_enter(); return
            print(bold("Summary →"), s["summary"])
            success = input(green("Did you recall it correctly? (y/n): ")).strip().lower().startswith("y")
            update_card(data, s["code"], success); session_reviewed += 1
            time.sleep(0.2)

# -------- Learning: Anki MC (single‑card mastery) --------
def mode_anki_mc(pool):
    """
    Pick ONE due card and keep quizzing multiple‑choice on it until the user
    answers correctly twice (total). Then end. SRS is updated each attempt.
    """
    clear(); print(bold("🧠 Anki MC — Single‑Card Mastery"))
    data = ensure_cards_in_srs(load_srs(), pool)
    # Choose a target: prefer due; otherwise earliest due
    due = next_due_cards(data, pool)
    target = random.choice(due)
    correct_needed = 2
    correct_count = 0
    attempts = 0

    while correct_count < correct_needed:
        attempts += 1
        clear()
        variant_a, variant_b = make_mc_variants(target, pool, options=4)
        prompt, choices, answer_idx = random.choice([variant_a, variant_b])
        print(cyan(f"Mastering: {target['code']} — {target['name']}  ({correct_count}/{correct_needed} correct so far)"))
        print(prompt)
        for i, ch in enumerate(choices, 1):
            print(f"  {i}) {ch}")
        choice = ask_int(yellow("Your choice: "), 1, len(choices))
        success = (choice - 1 == answer_idx)
        if success:
            print(green("✔ Correct!"))
            correct_count += 1
        else:
            print(red("✘ Incorrect."))
            # Reveal correct
            print(yellow("Correct answer →"), choices[answer_idx])
        # Update SRS for the target only
        update_card(data, target["code"], success)
        time.sleep(0.2)

    save_json(SRS_FILE, data)
    print(green(f"\nMastered {target['code']} — {target['name']} in {attempts} attempts (2 correct)."))
    press_enter()

# -------- Games --------
def make_mc_question_code_to_name(pool):
    correct = random.choice(pool)
    wrongs = [s for s in pool if s is not correct]
    picks = pick_n_unique(wrongs, 3) + [correct]
    random.shuffle(picks)
    return correct, picks

def mode_mc(pool, reverse=False):
    clear(); print(bold("🧠 Multiple Choice"))
    score = 0
    for r in range(10):
        correct, picks = make_mc_question_code_to_name(pool)
        print(cyan(f"\nQ{r+1}/10"))
        if reverse:
            print(bold(f"Which code matches: {correct['name']}?"))
            for i,p in enumerate(picks,1): print(f"  {i}) {p['code']}")
        else:
            print(bold(f"What does {correct['code']} define?"))
            for i,p in enumerate(picks,1): print(f"  {i}) {p['name']}")
        c = ask_int(yellow("Your choice: "),1,len(picks))
        if picks[c-1] is correct:
            print(green("✔ +100")); score += 100
        else:
            print(red(f"✘  {correct['code']} — {correct['name']}"))
    print(bold(f"\nScore: {score}")); record_score("MultipleChoice_Rev" if reverse else "MultipleChoice", score)

def mode_streak(pool):
    clear(); print(bold("🔥 Streak Survival — miss one and done"))
    streak = 0
    while True:
        correct,picks = make_mc_question_code_to_name(pool)
        print(cyan(f"\nWhat does {correct['code']} define?"))
        for i,p in enumerate(picks,1): print(f"  {i}) {p['name']}")
        c = ask_int(yellow("Your choice: "),1,len(picks))
        if picks[c-1] is correct:
            streak += 1; print(green(f"✔ Streak {streak}"))
        else:
            print(red(f"✘  {correct['code']} — {correct['name']}")); break
    print(bold(f"Final streak: {streak}")); record_score("Streak", streak)

def mode_speedrun(pool, seconds=60):
    clear(); print(bold(f"⏱ {seconds}s Speedrun"))
    score = 0; start = time.time()
    def left(): return max(0, int(seconds - (time.time()-start)))
    while left() > 0:
        correct, picks = make_mc_question_code_to_name(pool)
        print(cyan(f"\n{correct['code']} — {left()}s left"))
        for i,p in enumerate(picks,1): print(f"  {i}) {p['name']}")
        try:
            c = ask_int(yellow("Your choice: "),1,len(picks))
        except KeyboardInterrupt:
            print("\n"+yellow("Exiting early...")); break
        if picks[c-1] is correct: score += 100; print(green("✔ +100"))
        else: score -= 25; print(red(f"✘ −25 (Correct: {correct['name']})"))
    print(bold(f"\nFinal Score: {score}")); record_score("Speedrun60", score)

# -------- Instructions --------
INSTRUCTIONS = f"""
{bold('How to Use IEEE 802 Trainer v5')}

Study Set:
  • {bold('Core')} — the Network+ essentials (802.3, 802.11 variants, 802.1Q, 802.1X, 802.15).
  • {bold('Expanded')} — broader 802.x coverage for mastery.

Learning Modes:
  • Flashcards — quick, self‑paced review.
  • Anki — spaced repetition (interval doubles on correct, resets on wrong).
  • Anki MC — picks one due card and quizzes via multiple‑choice until you answer it correctly {bold('twice')}. Then the session ends.

Games:
  • Multiple Choice (Code→Name / Reverse), Streak, and 60s Speedrun — great for pressure‑testing recall.

Persistence:
  • High scores saved in {SCORE_FILE}
  • Spaced repetition memory saved in {SRS_FILE}
"""

# -------- Menus --------
def menu_learning(pool):
    while True:
        clear(); print(bold("📚 Learning Modes"))
        print("1) Flashcards")
        print("2) Anki (Spaced Repetition)")
        print("3) Anki MC (Single‑Card Mastery)")
        print("4) Reset SRS Progress")
        print("5) Instructions")
        print("6) Back")
        c = ask_int(yellow("Choose: "),1,6)
        if c==1: mode_flashcards(pool); press_enter()
        elif c==2: mode_anki(pool)
        elif c==3: mode_anki_mc(pool)
        elif c==4:
            if input(red("Reset ALL SRS progress? y/n: ")).strip().lower().startswith("y"):
                if os.path.exists(SRS_FILE): 
                    try: os.remove(SRS_FILE); print(green("SRS reset."))
                    except Exception as e: print(red(f"Could not remove: {e}"))
                else: print(yellow("No SRS data found."))
                time.sleep(1)
        elif c==5: clear(); print(INSTRUCTIONS); press_enter()
        elif c==6: return

def menu_games(pool):
    while True:
        clear(); print(bold("🎮 Game Modes"))
        print("1) Multiple Choice (Code → Name)")
        print("2) Reverse (Name → Code)")
        print("3) Streak Survival")
        print("4) 60s Speedrun")
        print("5) Back")
        c = ask_int(yellow("Choose: "),1,5)
        if c==1: mode_mc(pool, reverse=False); press_enter()
        elif c==2: mode_mc(pool, reverse=True); press_enter()
        elif c==3: mode_streak(pool); press_enter()
        elif c==4: mode_speedrun(pool); press_enter()
        elif c==5: return

def main_menu():
    while True:
        clear(); print(bold("IEEE 802 Trainer v5 — Cross‑Platform Edition"))
        print("1) Learning Modes")
        print("2) Game Modes")
        print("3) View High Scores")
        print("4) Quit")
        c = ask_int(yellow("Choose: "),1,4)
        if c==1:
            pool = choose_study_set()
            menu_learning(pool)
        elif c==2:
            pool = choose_study_set()
            menu_games(pool)
        elif c==3:
            clear(); print_high_scores(); press_enter()
        elif c==4:
            print(green("Goodbye!")); break

if __name__=="__main__":
    try: random.seed(); main_menu()
    except KeyboardInterrupt: print("\n"+yellow("Exited."))
