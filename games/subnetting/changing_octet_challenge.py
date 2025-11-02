#!/usr/bin/env python3
"""
Changing Octet Challenge v4 — Full Menu + Timed Round System
-------------------------------------------------------------
Each question has its own 10 s countdown.
 +1 s bonus after every 5-correct streak.
Stores a named high-score leaderboard.
"""

import ipaddress, json, os, random, signal, sys, time

PROGRESS_FILE = "subnet_snap_progress.json"
BASE_POINTS = 100
BONUS_MULTIPLIER = 1.5
HINT_PENALTY = 50
WRONG_PENALTY = 75
STREAK_BONUS_TIME = 1.0
QUESTION_TIME = 10.0

# -------- utilities --------
def detect_octet(cidr:int)->int:
    for i,b in enumerate(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed,1):
        if b!=255: return i
    return 4

def visual_explanation(cidr:int)->str:
    mask=str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    bits=".".join(f"{b:08b}" for b in ipaddress.ip_network(f'0.0.0.0/{cidr}').netmask.packed)
    o=detect_octet(cidr)
    return (f"\n💡  /{cidr}  →  {mask}\nBinary: {bits}\nChanging octet = {o} "
            f"({['1st','2nd','3rd','4th'][o-1]})\n")

def load_scores():
    if os.path.exists(PROGRESS_FILE):
        try: return json.load(open(PROGRESS_FILE))
        except: pass
    return {"scores":{}}

def save_scores(data):
    with open(PROGRESS_FILE,"w") as f: json.dump(data,f,indent=2)

def show_highscores(data):
    print("\n🏆 High Scores")
    all_scores=[]
    for name,info in data["scores"].items():
        all_scores.append((info.get("highscore",0),name))
    for i,(s,n) in enumerate(sorted(all_scores,reverse=True)[:10],1):
        print(f"{i:>2}. {n:<15} {s}")
    if not all_scores: print("(no scores yet)")
    print()

# -------- timer helper --------
class Timeout(Exception): pass
def handler(signum, frame): raise Timeout
signal.signal(signal.SIGALRM, handler)

# -------- main game --------
def play(name,data):
    high=data["scores"].get(name,{"highscore":0,"best_streak":0})
    highscore=high.get("highscore",0)
    best_streak=high.get("best_streak",0)

    score=0; streak=0; mult=1.0

    print(f"\nWelcome {name}! Your current high score: {highscore}\n")
    print("Identify which octet (1-4) changes for the CIDR or mask.")
    print("10 s per question → 5-streak adds +1 s. 'h' = hint, 'q' = quit.\n")

    while True:
        cidr=random.randint(0,30)
        mask=str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
        qtype=random.choice(["cidr","mask"])
        disp=f"/{cidr}" if qtype=="cidr" else mask
        label="CIDR" if qtype=="cidr" else "Subnet Mask"

        print(f"📘 {label}: {disp}  | Score:{score} x{mult:.1f} | Time: {QUESTION_TIME:.1f}s")
        signal.alarm(int(QUESTION_TIME))
        try:
            start=time.time()
            ans=input("👉 Which octet changes (1-4)? ").strip().lower()
            signal.alarm(0)
        except Timeout:
            print("\n⏰ Time up!")
            break

        elapsed=time.time()-start
        if ans in ("q","quit","exit"): break
        if ans in ("h","hint"):
            print(visual_explanation(cidr))
            score=max(0,score-HINT_PENALTY)
            continue
        if not ans.isdigit() or not (1<=int(ans)<=4):
            print("Enter 1–4 or 'h' or 'q'."); continue

        correct=detect_octet(cidr)
        if int(ans)==correct:
            base=BASE_POINTS
            if elapsed<=3: base+=50
            if streak and streak%5==0:
                QUESTION_TIME_PLUS=STREAK_BONUS_TIME
                print(f"⚡ 5-Streak! +{QUESTION_TIME_PLUS:.0f}s bonus next round!")
            if streak and streak%5==0: mult*=BONUS_MULTIPLIER
            pts=int(base*mult)
            score+=pts; streak+=1
            best_streak=max(best_streak,streak)
            print(f"✅ Correct! +{pts} pts (Streak {streak})\n")
        else:
            print(f"❌ Wrong → {correct} ({['1st','2nd','3rd','4th'][correct-1]})")
            print(visual_explanation(cidr))
            score=max(0,score-WRONG_PENALTY)
            streak=0; mult=1.0
            print(f"💀 -{WRONG_PENALTY} pts | Score {score}\n")

    # ---- save results ----
    data["scores"].setdefault(name,{})
    data["scores"][name]["highscore"]=max(highscore,score)
    data["scores"][name]["best_streak"]=max(best_streak,streak)
    save_scores(data)
    print(f"\n=== Session End ===\nScore:{score}  Best Streak:{best_streak}\n")
    print(f"🏆 High Score ({name}): {data['scores'][name]['highscore']}\n")

# -------- main menu --------
def main():
    data=load_scores()
    while True:
        print("=== Changing Octet Challenge v4 ===")
        print("1) Start new game")
        print("2) View high scores")
        print("3) Quit")
        c=input("> ").strip()
        if c=="1":
            name=input("Enter your name: ").strip() or "Player"
            play(name,data)
        elif c=="2":
            show_highscores(data)
        elif c=="3":
            print("Goodbye!"); break
        else:
            print("Choose 1-3.\n")

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt:
        print("\nInterrupted."); sys.exit(0)
