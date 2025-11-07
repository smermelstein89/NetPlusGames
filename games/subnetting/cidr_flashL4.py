#!/usr/bin/env python3
"""
CIDR Flash — Level 4: Speedrun
------------------------------
One-minute timed challenge mixing CIDR→Mask and Mask→CIDR.
"""

import ipaddress, json, os, random, time

SCOREFILE = "cidr_flash_scores.json"
MODE_KEY  = "lv4_speedrun"

# ---------- CIDR Reference ----------
CIDR_TABLE = [
    {"cidr": i, "mask": str(ipaddress.ip_network(f"0.0.0.0/{i}").netmask)}
    for i in range(0, 33)
]
MASK_TO_CIDR = {e["mask"]: e["cidr"] for e in CIDR_TABLE}

# ---------- Score Handling ----------
def _blank_scores():
    return {MODE_KEY: []}

def load_scores():
    if not os.path.exists(SCOREFILE):
        return _blank_scores()
    try:
        with open(SCOREFILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            print("⚙️  Detected old score format — converting automatically.")
            newdata = _blank_scores()
            newdata[MODE_KEY] = data
            save_scores(newdata)
            data = newdata
    except Exception:
        data = _blank_scores()
    data.setdefault(MODE_KEY, [])
    return data

def save_scores(scores):
    with open(SCOREFILE, "w") as f:
        json.dump(scores, f, indent=2)

def record_score(name, score, duration):
    scores = load_scores()
    scores[MODE_KEY].append({
        "name": name,
        "score": score,
        "duration": round(duration, 1),
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    scores[MODE_KEY] = sorted(scores[MODE_KEY],
                              key=lambda x: x["score"], reverse=True)[:10]
    save_scores(scores)

def print_highscores():
    scores = load_scores()[MODE_KEY]
    print(f"\n🏆 High-Scores — CIDR Flash Lv4 (Speedrun 60 s) 🏆")
    if not scores:
        print("  (none yet)")
        return
    for i, s in enumerate(scores, start=1):
        print(f"{i:2d}. {s['name']:<12} {s['score']:>3} pts  "
              f"{s['duration']:>4.1f}s  {s['time']}")
    print()

# ---------- Helpers ----------
def get_hint(cidr):
    if cidr >= 24:
        return f"/{cidr} → last-octet partial (.0, .128, .192, .224 …)"
    elif cidr >= 16:
        return f"/{cidr} → third-octet changes (255.255.X.0)"
    else:
        return f"/{cidr} → second-octet changes (Class A/B-sized nets)"

def get_mem_tip(cidr, mask):
    block = 2 ** (32 - cidr)
    return f"Correct: /{cidr} = {mask}  |  {32 - cidr} host bits → block {block}"

# ---------- Speedrun ----------
def run_speedrun(name, duration=60):
    print("\n⚡ CIDR Flash Lv4 — 60-Second Speedrun ⚡")
    print("Answer as many as you can.  h = hint, q = quit early.\n")

    end_time = time.time() + duration
    score = 0
    start_time = time.time()

    while time.time() < end_time:
        q = random.choice(CIDR_TABLE)
        direction = random.choice(["cidr_to_mask", "mask_to_cidr"])
        cidr, mask = q["cidr"], q["mask"]

        if direction == "cidr_to_mask":
            prompt = f"/{cidr} → mask? "
            ans = input(prompt).strip()
            if ans.lower() in ["q","quit","exit"]:
                print("🚪 Exiting early.\n"); break
            if ans.lower() == "h":
                print("💡", get_hint(cidr))
                ans = input("Try again: ").strip()
                if ans.lower() in ["q","quit","exit"]:
                    print("🚪 Exiting early.\n"); break
            if ans == mask:
                print("✅"); score += 1
            else:
                print("❌", get_mem_tip(cidr, mask))

        else:  # mask_to_cidr
            prompt = f"{mask} → CIDR? /"
            ans = input(prompt).strip()
            if ans.lower() in ["q","quit","exit"]:
                print("🚪 Exiting early.\n"); break
            if ans.lower() == "h":
                print("💡", get_hint(cidr))
                ans = input("Try again (number only): /").strip()
                if ans.lower() in ["q","quit","exit"]:
                    print("🚪 Exiting early.\n"); break
            if ans.startswith("/"): ans = ans[1:]
            if ans == str(cidr):
                print("✅"); score += 1
            else:
                print("❌", get_mem_tip(cidr, mask))

    elapsed = time.time() - start_time
    print(f"\n🏁 Time’s up!  {name}, you scored {score} points.")
    record_score(name, score, elapsed)
    print_highscores()

# ---------- Main ----------
def main():
    print("=== 🧮 CIDR Flash Lv4 — Speedrun (60 s) ===")
    name = input("Enter your name: ").strip() or "Anonymous"

    while True:
        print("""
1) Start Speedrun
2) View High-Scores
3) Quit
""")
        ch = input("> ").strip()
        if ch == "1":
            run_speedrun(name)
        elif ch == "2":
            print_highscores()
        elif ch in ["3","q","quit","exit"]:
            print("Goodbye 👋"); break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

