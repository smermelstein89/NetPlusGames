#!/usr/bin/env python3
"""
CIDR Flash — Level 0: Learning Mode (Anki)
------------------------------------------
Repetition-based flashcard trainer with three modes:
 1. CIDR → Mask (Octet)
 2. Mask → CIDR
 3. Mixed (both directions for full mastery)
"""
import ipaddress, json, os, random, time

SCOREFILE = "cidr_flash_scores.json"
MODE_KEYS = {
    "cidr2mask": "lv0_learning_cidr2mask",
    "mask2cidr": "lv0_learning_mask2cidr",
    "mixed": "lv0_learning_mixed"
}

# ---------- CIDR Reference ----------
CIDR_TABLE = [
    {"cidr": i, "mask": str(ipaddress.ip_network(f"0.0.0.0/{i}").netmask)}
    for i in range(0, 33)
]
MASK_TO_CIDR = {entry["mask"]: entry["cidr"] for entry in CIDR_TABLE}


# ---------- Score Handling ----------
def _blank_scores():
    return {v: [] for v in MODE_KEYS.values()}

def load_scores():
    if not os.path.exists(SCOREFILE):
        return _blank_scores()
    try:
        with open(SCOREFILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):  # legacy
            print("⚙️  Detected old score format — converting automatically.")
            newdata = _blank_scores()
            newdata[MODE_KEYS["cidr2mask"]] = data
            save_scores(newdata)
            data = newdata
    except Exception:
        data = _blank_scores()
    for k in _blank_scores():
        data.setdefault(k, [])
    return data

def save_scores(scores):
    with open(SCOREFILE, "w") as f:
        json.dump(scores, f, indent=2)

def record_score(mode_key, name, mastered, attempts, duration):
    scores = load_scores()
    total = 33 if mode_key != MODE_KEYS["mixed"] else 66
    percent = round(100 * mastered / total, 1)
    scores[mode_key].append({
        "name": name,
        "score": mastered,
        "attempted": attempts,
        "percent": percent,
        "duration": round(duration, 1),
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    scores[mode_key] = sorted(scores[mode_key],
                              key=lambda x: x["score"], reverse=True)[:10]
    save_scores(scores)

def print_highscores(mode_key):
    scores = load_scores()[mode_key]
    label = mode_key.split("_")[-1]
    print(f"\n🏆 High-Scores — CIDR Flash Lv0 ({label.title()}) 🏆")
    if not scores:
        print("  (none yet)")
        return
    for i, s in enumerate(scores, start=1):
        print(f"{i:2d}. {s['name']:<12} {s['score']:>2}  "
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
    return f"Correct: /{cidr} = {mask}  |  {32 - cidr} host bits → block {block}"


# ---------- Learning Engine ----------
def learning_session(name, mode_key, direction):
    print(f"\n📚 CIDR Flash Lv0 — {direction.replace('_','→')} Mode")
    print("Repetition until all mastered. Type h for hint, q to quit.\n")

    # Build review pool
    if direction == "mixed":
        review_pool = [{"cidr": c["cidr"], "mask": c["mask"], "dir": d}
                       for c in CIDR_TABLE for d in ["cidr_to_mask", "mask_to_cidr"]]
    else:
        review_pool = [{"cidr": c["cidr"], "mask": c["mask"], "dir": direction} for c in CIDR_TABLE]
    random.shuffle(review_pool)

    mastered = set()
    total = len(review_pool)
    attempts = 0
    start_time = time.time()

    while review_pool:
        q = review_pool.pop(0)
        cidr, mask, dirn = q["cidr"], q["mask"], q["dir"]
        attempts += 1

        if dirn == "cidr_to_mask":
            print(f"\nCIDR /{cidr}")
            ans = input("Mask (h for hint, q to quit): ").strip()
            if ans.lower() in ["q", "quit", "exit"]:
                print("🚪 Exiting early.\n")
                break
            if ans.lower() == "h":
                print("💡", get_hint(cidr))
                ans = input("Try again: ").strip()
            if ans == mask:
                print("✅ Correct!")
                mastered.add((cidr, dirn))
            else:
                print("❌", get_mem_tip(cidr, mask))
                review_pool.append(q)

        else:  # mask_to_cidr
            print(f"\nMask {mask}")
            ans = input("CIDR prefix (h for hint, q to quit): /").strip()
            if ans.lower() in ["q", "quit", "exit"]:
                print("🚪 Exiting early.\n")
                break
            if ans.lower() == "h":
                print("💡", get_hint(cidr))
                ans = input("Try again (number only): /").strip()
            if ans.startswith("/"): ans = ans[1:]
            if ans == str(cidr):
                print("✅ Correct!")
                mastered.add((cidr, dirn))
            else:
                print("❌", get_mem_tip(cidr, mask))
                review_pool.append(q)

        remaining = total - len(mastered)
        print(f"Progress: {len(mastered)}/{total} mastered, {remaining} remaining")

        if not review_pool and remaining > 0:
            review_pool = [c for c in [{"cidr": c["cidr"], "mask": c["mask"], "dir": d}
                        for c in CIDR_TABLE for d in ([direction] if direction!="mixed" else ["cidr_to_mask","mask_to_cidr"])]
                        if (c["cidr"], c["dir"]) not in mastered]
            random.shuffle(review_pool)

    duration = time.time() - start_time
    print(f"\n🎓 Session complete! Mastered {len(mastered)}/{total}.")
    record_score(mode_key, name, len(mastered), attempts, duration)
    print_highscores(mode_key)


# ---------- Main Menu ----------
def main():
    print("=== 🧮 CIDR Flash Lv0 — Learning Mode (Anki) ===")
    name = input("Enter your name: ").strip() or "Anonymous"

    while True:
        print("""
Choose a Learning Path:
1) CIDR → Mask (33 cards)
2) Mask → CIDR (33 cards)
3) Mixed (both directions, 66 cards)
4) View High-Scores
5) Quit
""")
        ch = input("> ").strip()
        if ch == "1":
            learning_session(name, MODE_KEYS["cidr2mask"], "cidr_to_mask")
        elif ch == "2":
            learning_session(name, MODE_KEYS["mask2cidr"], "mask_to_cidr")
        elif ch == "3":
            learning_session(name, MODE_KEYS["mixed"], "mixed")
        elif ch == "4":
            for key in MODE_KEYS.values():
                print_highscores(key)
        elif ch in ["5", "q", "quit", "exit"]:
            print("Goodbye 👋")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

