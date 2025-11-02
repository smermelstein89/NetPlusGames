#!/usr/bin/env python3
"""
Subnet Snap — Smart Learning Path (Level 6)
-------------------------------------------
Supernetting practice: /0–/8.
 - Multiple choice (recognize global and class-A supernets)
 - Visual hints showing which octet changes
 - 10 correct in a row to finish
 - Saves progress in subnet_snap_progress.json
"""

import ipaddress, json, os, random, sys
from collections import deque

PROGRESS_FILE = "subnet_snap_progress.json"
LEVEL = 6
TARGET_STREAK = 10
CHOICES = 4

# ----- Pool: /0 .. /8 -----
CIDRS = list(range(0, 9))
CARDS = [{"cidr": c, "mask": str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask)} for c in CIDRS]

# ---------- Progress ----------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE,"r") as f: return json.load(f)
        except Exception: pass
    return {"current_level": 6, "best_streak": 0, "high_score": 0}

def save_progress(p):
    with open(PROGRESS_FILE,"w") as f: json.dump(p,f,indent=2)

# ---------- Helpers ----------
def block_size_from_cidr(cidr): return 2 ** (32 - cidr)

def detect_changing_octet(cidr:int)->int:
    mask_bytes=list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)
    for i,b in enumerate(mask_bytes,1):
        if b!=255: return i
    return 4

def build_ranges(cidr:int):
    """Return (octet, ranges, block_size_per_that_octet)."""
    size=block_size_from_cidr(cidr)
    octet=detect_changing_octet(cidr)
    div=[1,256,256**2,256**3][4-octet]
    step=max(1,size//div)
    start=0; ranges=[]
    while start<256:
        end=min(start+step-1,255)
        ranges.append((start,end))
        start+=step
    return octet,ranges,step

def visual_hint(cidr:int)->str:
    mask=str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    octet,ranges,step=build_ranges(cidr)
    shown=ranges[:8]
    ranges_text="\n  ".join([f"{a:>3}–{b:<3}" for a,b in shown])+("  ..." if len(ranges)>8 else "")
    return (
        f"\n💡 Hint for /{cidr}\n"
        f"Mask: {mask}\n"
        f"Changing octet: {octet}\n"
        f"Block size: {step}\n"
        f"Subnet ranges (octet {octet}):\n  {ranges_text}\n"
        f"These are very large networks — each step jumps by {step} in octet {octet}.\n"
    )

def make_choices(correct,pool,direction):
    others=[c for c in pool if c!=correct]
    distractors=random.sample(others,k=min(CHOICES-1,len(others)))
    picks=[correct]+distractors
    random.shuffle(picks)
    if direction=="cidr_to_mask":
        return [str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask) for c in picks]
    else:
        return [str(c) for c in picks]

def ask_mc_question(card):
    cidr,mask=card["cidr"],card["mask"]
    direction=random.choice(["cidr_to_mask","mask_to_cidr"])
    pool=CIDRS[:]
    if direction=="cidr_to_mask":
        correct_value=mask
        choices=make_choices(cidr,pool,direction)
        prompt=f"\n🟦 CIDR: /{cidr}\nSelect the matching subnet mask:"
    else:
        correct_value=str(cidr)
        choices=make_choices(cidr,pool,direction)
        prompt=f"\n🟩 Subnet mask: {mask}\nSelect the matching CIDR (number only):"
    print(prompt)
    for i,opt in enumerate(choices,1): print(f"  {i}. {opt}")
    print("  h. hint   q. quit")
    was_hint=False
    while True:
        ans=input("> ").strip().lower()
        if ans in ("q","quit","exit"): return False,was_hint,True
        if ans=="h":
            print(visual_hint(cidr)); was_hint=True; continue
        if ans.isdigit():
            idx=int(ans)
            if 1<=idx<=len(choices):
                picked=choices[idx-1]; ok=(picked==correct_value)
                if ok: print("✅ Correct!")
                else:
                    print(f"❌ Incorrect.\nCorrect answer: {correct_value}")
                    print(visual_hint(cidr))
                return ok,was_hint,False
        print("Choose 1-4, 'h', or 'q'.")

# ---------- Main ----------
def main():
    prog=load_progress()
    if prog.get("current_level",1)>6:
        print("📈 You already cleared Level 6 previously. (Progress loaded)")
    print("=== 🧮 Subnet Snap — Level 6 (/0–/8 Supernets) ===")
    print("Focus: supernets & class-A summarization. Get 10 correct in a row to finish.\n")

    deck=deque(CARDS); random.shuffle(deck)
    score=0; streak=0
    best_streak=prog.get("best_streak",0); high_score=prog.get("high_score",0)

    while True:
        if not deck: deck=deque(CARDS); random.shuffle(deck)
        card=deck.popleft()
        ok,hint,quit=ask_mc_question(card)
        if quit: break
        if ok:
            score+=1; streak+=1; best_streak=max(best_streak,streak)
            print(f"Score:{score}  Streak:{streak}  Best:{best_streak}")
        else:
            streak=0; deck.appendleft(card)
            print(f"Score:{score}  Streak reset  Best:{best_streak}")
        if streak>=TARGET_STREAK:
            print("\n🏆 LEVEL COMPLETE! You mastered supernet CIDRs (/0–/8)!")
            prog["current_level"]=max(prog.get("current_level",6),LEVEL+1)
            break

    prog["best_streak"]=max(prog.get("best_streak",0),best_streak)
    prog["high_score"]=max(prog.get("high_score",0),score)
    save_progress(prog)
    print("\n=== Session Summary ===")
    print(f"Final Score:{score}  Best Streak:{best_streak}")
    print(f"Saved Level:{prog['current_level']}  | High Score:{prog['high_score']}")
    print("🎓 You’ve completed Subnet Snap training through Level 6 — you now understand ALL CIDR ranges!")

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
