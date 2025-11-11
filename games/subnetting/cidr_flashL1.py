#!/usr/bin/env python3
"""
CIDR Flash — Level 1: Mask → CIDR
---------------------------------
Given a subnet mask, identify the correct CIDR prefix (e.g. 255.255.255.0 → /24).
"""

import ipaddress, json, os, random, time

SCOREFILE = "cidr_flash_scores.json"
MODE_KEY = "lv1_mask2cidr"

# ---------- CIDR Reference ----------
CIDR_TABLE = [
    {"cidr": i, "mask": str(ipaddress.ip_network(f"0.0.0.0/{i}").netmask)}
    for i in range(0, 33)
]
MASK_TO_CIDR = {entry["mask"]: entry["cidr"] for entry in CIDR_TABLE}

# ---------- Score Handling ----------
def _blank_scores():
    return {MODE_KEY: []}

def load_scores():
    if not os.path.exists(SCOREFILE):
        return _blank_scores()
    try:
        with open(SCOREFILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):  # legacy format
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

def record_score(name, score, rounds, duration):
    scores = load_scores()
    percent = round(100 * score / rounds, 1)
    scores[MODE_KEY].append({
        "name": name,
        "score": score,
        "rounds": rounds,
        "percent": percent,
        "duration": round(duration, 1),
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    scores[MODE_KEY] = sorted(scores[MODE_KEY],
                              key=lambda x: x["score"], reverse=True)[:10]
    save_scores(scores)

def print_highscores():
    scores = load_scores()[MODE_KEY]
    print(f"\n🏆 High-Scores — CIDR Flash Lv1 (Mask → CIDR) 🏆")
    if not scores:
        print("  (none yet)")
        return
    for i, s in enumerate(scores, start=1):
        print(f"{i:2d}. {s['name']:<12} {s['score']:>2}/10  "
              f"{s['percent']:>5.1f}%  {s['duration']:>4.1f}s  {s['time']}")
    print()

# ---------- Helpers ----------
def get_hint(cidr):
    if cidr >= 24:
        return f"/{cidr} → last octet partial (.0, .128, .192, .224 …)"
    elif cidr >= 16:
        return f"/{cidr} → third octet changes (255.255.X.0)"
    else:
        return f"/{cidr} → second octet changes (Class A/B sized networks)"

def get_mem_tip(cidr, mask):
    block = 2 ** (32 - cidr)
    return f"Correct: /{cidr}  ({mask}) | {32 - cidr} host bits → block {block}"

# ---------- Core Quiz ----------
def run_quiz(name, rounds=10):
    print("\n🎯 CIDR Flash Lv1 — Mask → CIDR Conversion")
    print("Type h for hint, q to quit.\n")

    score = 0
    start_time = time.time()

    for i in range(1, rounds + 1):
        q = random.choice(CIDR_TABLE)
        mask, cidr = q["mask"], q["cidr"]

        print(f"Q{i}: Mask {mask}")
        ans = input("CIDR prefix (h for hint, q to quit): /").strip()
        if ans.lower() in ["q", "quit", "exit"]:
            print("🚪 Exiting early.\n")
            break
        if ans.lower() == "h":
            print("💡", get_hint(cidr))
            ans = input("Try again (number only): /").strip()
            if ans.lower() in ["q", "quit", "exit"]:
                print("🚪 Exiting early.\n")
                break

        if ans.startswith("/"):
            ans = ans[1:]

        if ans == str(cidr):
            print("✅ Correct!\n")
            score += 1
        else:
            print("❌", get_mem_tip(cidr, mask), "\n")

    duration = time.time() - start_time
    print(f"\n🏁 {name}, you scored {score}/{rounds} ({100*score/rounds:.1f}%)")
    record_score(name, score, rounds, duration)
    print_highscores()

# ---------- Main ----------
def main():
    print("=== 🧮 CIDR Flash Lv1 — Mask → CIDR ===")
    name = input("Enter your name: ").strip() or "Anonymous"

    while True:
        print("""
1) Start Quiz
2) View High-Scores
3) Quit
""")
        choice = input("> ").strip()
        if choice == "1":
            run_quiz(name)
        elif choice == "2":
            print_highscores()
        elif choice in ["3", "q", "quit", "exit"]:
            print("Goodbye 👋")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

