#!/usr/bin/env python3
"""
Magic Number Sprint — Timed Subnet Reflex Trainer
-------------------------------------------------
Identify the "magic number" (block size) for a CIDR or subnet mask.

 • Start menu + player names
 • Global high-score leaderboard
 • 10 s base timer that shrinks as questions progress
 • +1 s per 5-streak
 • Multipliers, hints, penalties
"""

import ipaddress, json, os, random, signal, sys, time
from datetime import datetime

SCORE_FILE = "magic_number_sprint_scores.json"
BASE_TIME = 10.0
STREAK_BONUS_TIME = 1.0
BASE_POINTS = 100
BONUS_MULTIPLIER = 1.5
HINT_PENALTY = 50
WRONG_PENALTY = 75
MIN_TIME = 2.0

# ---------- helpers ----------
def detect_octet(cidr:int)->int:
    for i,b in enumerate(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed,1):
        if b!=255: return i
    return 4

def magic_number(cidr:int)->int:
    """Return increment size (magic number) in changing octet."""
    net = ipaddress.ip_network(f"0.0.0.0/{cidr}")
    octet = detect_octet(cidr)
    mask_bytes = list(net.netmask.packed)
    val = 256 - mask_bytes[octet-1]
    return val if val>0 else 256

def visual_hint(cidr:int)->str:
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    octet = detect_octet(cidr)
    mnum = magic_number(cidr)
    return (f"\n💡 /{cidr} → {mask}\nChanging octet: {octet}\n"
            f"Magic number = {mnum}\nExample ranges in that octet:\n"
            + ", ".join(f"{i}-{i+mnum-1}" for i in range(0,256,mnum)[:8]) + " ...\n")

# ---------- data ----------
def load_scores():
    if os.path.exists(SCORE_FILE):
        try:
            data = json.load(open(SCORE_FILE))
            if not isinstance(data, dict): data={}
        except Exception: data={}
    else: data={}
    data.setdefault("players",{})
    data.setdefault("runs",[])
    return data

def save_scores(data):
    with open(SCORE_FILE,"w") as f: json.dump(data,f,indent=2)

def show_highscores(data):
    print("\n🏆 Magic Number Sprint High Scores")
    if not data["runs"]:
        print("(no runs yet)\n"); return
    top = sorted(data["runs"], key=lambda x:x["score"], reverse=True)[:10]
    for i,r in enumerate(top,1):
        print(f"{i:>2}. {r['name']:<12} {r['score']:>6}  "
              f"({r['streak']} streak, {r['time']})")
    print()

# ---------- timer ----------
class Timeout(Exception): pass
def handler(signum, frame): raise Timeout
signal.signal(signal.SIGALRM, handler)

def get_time_for_question(q):
    """Dynamic shrinking timer like Changing Octet v5."""
    if q<10: return BASE_TIME-q*1
    elif q<20: return BASE_TIME-9-(q-9)*2
    elif q<30: return BASE_TIME-9-10*2-(q-19)*3
    elif q<40: return BASE_TIME-9-10*2-10*3-(q-29)*4
    else:
        reduction = 9+20+30+(q-39)*5
        return max(BASE_TIME-reduction, MIN_TIME)

# ---------- main game ----------
def play(name,data):
    p=data["players"].get(name,{"highscore":0,"best_streak":0})
    high=p.get("highscore",0); best=p.get("best_streak",0)
    score=0; streak=0; mult=1.0; extra_time=0.0; q=0
    print(f"\nWelcome {name}! Personal high score: {high}\n")

    while True:
        q+=1
        base_t=max(get_time_for_question(q),MIN_TIME)
        time_limit=base_t+extra_time; extra_time=0
        if time_limit<=0: print("\n🕑 Timer exhausted!"); break

        cidr=random.randint(0,30)
        mask=str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
        qtype=random.choice(["cidr","mask"])
        disp=f"/{cidr}" if qtype=="cidr" else mask
        label="CIDR" if qtype=="cidr" else "Subnet Mask"
        answer=magic_number(cidr)

        print(f"\nQ{q} | {label}: {disp} | Score:{score} x{mult:.1f} | Time:{time_limit:.1f}s")

        signal.alarm(int(time_limit))
        try:
            start=time.time()
            ans=input("👉 Enter magic number: ").strip().lower()
            signal.alarm(0)
        except Timeout:
            print("\n⏰ Time up!"); break

        elapsed=time.time()-start
        if ans in ("q","quit","exit"): break
        if ans in ("h","hint"):
            print(visual_hint(cidr))
            score=max(0,score-HINT_PENALTY)
            continue
        if not ans.isdigit():
            print("Enter a number, 'h', or 'q'."); continue

        ans_int=int(ans)
        if ans_int==answer:
            base=BASE_POINTS
            if elapsed<=3: base+=50
            if streak and streak%5==0:
                mult*=BONUS_MULTIPLIER; extra_time+=STREAK_BONUS_TIME
                print(f"⚡ 5-Streak! +{STREAK_BONUS_TIME:.0f}s bonus, x{mult:.1f} multiplier!")
            pts=int(base*mult); score+=pts; streak+=1
            best=max(best,streak)
            print(f"✅ Correct! +{pts} pts (Streak {streak})\n")
        else:
            print(f"❌ Wrong → {answer}")
            print(visual_hint(cidr))
            score=max(0,score-WRONG_PENALTY)
            streak=0; mult=1.0
            print(f"💀 -{WRONG_PENALTY} pts | Score {score}\n")

        if time_limit<=MIN_TIME:
            print("🕒 Timer minimum reached — game complete!")
            break

    # record
    data["players"].setdefault(name,{})
    data["players"][name]["highscore"]=max(high,score)
    data["players"][name]["best_streak"]=max(best,streak)
    data["runs"].append({
        "name":name,"score":score,"streak":best,
        "time":datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    data["runs"]=data["runs"][-500:]
    save_scores(data)
    print(f"\n=== Session End ===\nScore:{score} | Best Streak:{best}")
    print(f"🏆 {name}'s High Score: {data['players'][name]['highscore']}\n")

# ---------- menu ----------
def main():
    data=load_scores()
    while True:
        print("=== Magic Number Sprint ===")
        print("1) Start new game")
        print("2) View global high scores")
        print("3) Quit")
        c=input("> ").strip()
        if c=="1":
            name=input("Enter your name: ").strip() or "Player"
            play(name,data)
        elif c=="2": show_highscores(data)
        elif c=="3":
            print("Goodbye!"); break
        else: print("Choose 1-3.\n")

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt:
        print("\nInterrupted."); sys.exit(0)
