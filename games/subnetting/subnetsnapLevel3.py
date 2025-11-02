#!/usr/bin/env python3
"""
Subnet Snap — Smart Learning Path (Level 3)
-------------------------------------------
Level 3: recognize CIDR <-> Mask for /8–/15.
 - Multiple choice questions
 - Visual block hints (second octet changes)
 - 10 correct in a row to level up
 - Progress shared in subnet_snap_progress.json
"""

import ipaddress, json, os, random, sys
from collections import deque

PROGRESS_FILE = "subnet_snap_progress.json"
LEVEL = 3
TARGET_STREAK = 10
CHOICES = 4

# ----- Pool: /8 .. /15 -----
CIDRS = list(range(8, 16))
CARDS = [{"cidr": c, "mask": str(ipaddress.ip_network(f"0.0.0.0/{c}").netmask)} for c in CIDRS]

# ----- Progress -----
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE,"r") as f: return json.load(f)
        except Exception: pass
    return {"current_level": 3, "best_streak": 0, "high_score": 0}

def save_progress(p):
    with open(PROGRESS_FILE,"w") as f: json.dump(p,f,indent=2)

# ----- Helpers -----
def block_size_from_cidr(cidr): return 2 ** (32 - cidr)

def block_ranges_second_octet(cidr):
    """Return (start,end) ranges for 2nd octet blocks."""
    size = block_size_from_cidr(cidr) // (256*256)  # divide by /16 space
    ranges, start = [], 0
    while start < 256:
        end = min(start + size - 1, 255)
        ranges.append((start, end))
        start += size
    return ranges

def visual_hint(cidr):
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    size = block_size_from_cidr(cidr) // (256*256)
    subs = block_ranges_second_octet(cidr)
    shown = subs[:8]
    ranges_text = "\n  ".join([f"{a:>3}–{b:<3}" for a,b in shown]) + ("  ..." if len(subs)>8 else "")
    return (
        f"\n💡 Hint for /{cidr}\n"
        f"Mask: {mask}\n"
        f"Changing octet: 2nd\n"
        f"Block size in 2nd octet: {size}\n"
        f"Subnet ranges (2nd octet):\n  {ranges_text}\n"
        f"Network addresses start at .{shown[0][0] if shown else 0}.0.0 "
        f"and jump by {size} in the 2nd octet.\n"
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

# ----- Main -----
def main():
    prog=load_progress()
    if prog.get("current_level",1)>3:
        print("📈 You already cleared Level 3 previously. (Progress loaded)")
    print("=== 🧮 Subnet Snap — Level 3 (/8–/15) ===")
    print("Focus: second-octet masks (large networks). Get 10 correct in a row to level up.\n")

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
            print("\n🏆 LEVEL UP! You nailed 10 in a row at Level 3!")
            prog["current_level"]=max(prog.get("current_level",3),LEVEL+1)
            break

    prog["best_streak"]=max(prog.get("best_streak",0),best_streak)
    prog["high_score"]=max(prog.get("high_score",0),score)
    save_progress(prog)
    print("\n=== Session Summary ===")
    print(f"Final Score:{score}  Best Streak:{best_streak}")
    print(f"Saved Level:{prog['current_level']}  | High Score:{prog['high_score']}")
    if prog["current_level"]>3:
        print("🎉 Next time you can unlock Level 4 (mixed practice).")

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
