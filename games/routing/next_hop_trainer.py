#!/usr/bin/env python3
"""
Next Hop Trainer — Network+ CLI Game
------------------------------------
✅ Cross-platform: Windows, macOS, Linux (no signals/threads)
✅ Modes: Classic, Speedrun (60s), Practice/Instruction
✅ Longest-prefix match logic with metric tie-breaker
✅ High-score tracking per mode
✅ Clear per-question feedback + where you went off
"""

import ipaddress
import json
import os
import random
import sys
import time
from datetime import datetime

SCORE_FILE = "next_hop_trainer_scores.json"

# ----------------------------- Utilities -----------------------------

def clear():
    # Safe cross-platform clear
    os.system('cls' if os.name == 'nt' else 'clear')

def press_enter():
    input("\nPress Enter to continue...")

def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {"classic": [], "speedrun": []}
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"classic": [], "speedrun": []}
            data.setdefault("classic", [])
            data.setdefault("speedrun", [])
            return data
    except Exception:
        return {"classic": [], "speedrun": []}

def save_score(mode, name, points):
    data = load_scores()
    data[mode].append({"name": name, "points": points, "ts": datetime.now().isoformat(timespec="seconds")})
    # keep only top 20 per mode
    data[mode] = sorted(data[mode], key=lambda x: x["points"], reverse=True)[:20]
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def show_high_scores():
    data = load_scores()
    clear()
    print("🏆 High Scores")
    print("\n-- Classic --")
    if not data["classic"]:
        print("  (no scores yet)")
    else:
        for i, r in enumerate(data["classic"], 1):
            print(f"  {i:2d}. {r['name']:<14}  {r['points']:>6}  ({r['ts']})")
    print("\n-- Speedrun (60s) --")
    if not data["speedrun"]:
        print("  (no scores yet)")
    else:
        for i, r in enumerate(data["speedrun"], 1):
            print(f"  {i:2d}. {r['name']:<14}  {r['points']:>6}  ({r['ts']})")
    press_enter()

def maybe_reset_scores():
    clear()
    print("⚠️  Reset all scores?")
    ans = input("Type 'RESET' to confirm, or press Enter to cancel: ").strip()
    if ans == "RESET":
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"classic": [], "speedrun": []}, f)
        print("Scores reset.")
    else:
        print("Canceled.")
    press_enter()

def choose_int(prompt, low, high, allow_quit=True):
    while True:
        val = input(prompt).strip().lower()
        if allow_quit and val in ("q", "quit", "exit"):
            return None
        try:
            n = int(val)
            if low <= n <= high:
                return n
        except ValueError:
            pass
        print(f"Please enter a number {low}-{high} (or 'q' to quit).")

# ----------------------- Routing Table Generation -----------------------

IFACES = ["eth0", "eth1", "eth2", "wan0", "lan0", "uplink", "dmz0"]
NHOPS  = ["10.0.0.1", "10.0.1.1", "192.168.0.1", "172.16.0.1", "203.0.113.1", "198.51.100.1"]

def random_network(min_prefix=8, max_prefix=28):
    # Generate a random IPv4 network with a random prefix
    # Keep it in RFC1918 or TEST-NET to avoid odd visuals
    blocks = [
        ipaddress.IPv4Network("10.0.0.0/8"),
        ipaddress.IPv4Network("172.16.0.0/12"),
        ipaddress.IPv4Network("192.168.0.0/16"),
        ipaddress.IPv4Network("198.51.100.0/24"),
        ipaddress.IPv4Network("203.0.113.0/24"),
    ]
    base = random.choice(blocks)
    pfx = random.randint(min_prefix, max_prefix)
    # pick a random subnet within base with prefix pfx
    # take a random host and summarize
    rnd_ip_int = int(base.network_address) + random.randint(0, base.num_addresses - 1)
    rnd_ip = ipaddress.IPv4Address(rnd_ip_int)
    net = ipaddress.IPv4Network((rnd_ip, pfx), strict=False)
    return net

def build_routing_table(difficulty=2):
    """
    difficulty 1: 4-5 entries, minimal overlap + default route
    difficulty 2: 6-7 entries, some overlaps + default route
    difficulty 3: 8-10 entries, multiple overlaps + default + equal-prefix tie to test metrics
    """
    sizes = {1: (4,5), 2: (6,7), 3: (8,10)}
    lo, hi = sizes.get(difficulty, (6,7))
    n = random.randint(lo, hi)

    routes = []
    prefixes = []
    # ensure a default route appears
    default_route = {
        "dest": ipaddress.IPv4Network("0.0.0.0/0"),
        "next_hop": random.choice(NHOPS),
        "iface": random.choice(IFACES),
        "metric": random.randint(1, 20),
        "desc": "Default"
    }
    routes.append(default_route)

    # start with a few broader routes
    for _ in range(n-1):
        # sprinkle overlaps by biasing prefix range
        if difficulty == 1:
            net = random_network(12, 24)
        elif difficulty == 2:
            net = random_network(10, 28)
        else:
            # more chance of close overlaps
            net = random_network(8, 28)

        prefixes.append(net)
        routes.append({
            "dest": net,
            "next_hop": random.choice(NHOPS),
            "iface": random.choice(IFACES),
            "metric": random.randint(1, 20),
            "desc": ""
        })

    # In higher difficulty create at least one equal-prefix tie breaker by metric
    if difficulty >= 3 and len(routes) >= 3:
        base = random_network(20, 26)
        r1 = {
            "dest": base,
            "next_hop": random.choice(NHOPS),
            "iface": random.choice(IFACES),
            "metric": 10,
            "desc": "Tie A"
        }
        r2 = {
            "dest": base,
            "next_hop": random.choice([nh for nh in NHOPS if nh != r1["next_hop"]]),
            "iface": random.choice(IFACES),
            "metric": 5,  # strictly better metric
            "desc": "Tie B"
        }
        routes.append(r1)
        routes.append(r2)

    # De-duplicate any identical destinations by keeping the best metric
    unique = {}
    for r in routes:
        key = (str(r["dest"]),)
        if key not in unique or r["metric"] < unique[key]["metric"]:
            unique[key] = r
    routes = list(unique.values())

    # shuffle for realism
    random.shuffle(routes)
    return routes

def choose_destination_ip(routes):
    """
    60% chance: choose an IP that actually matches one of the non-default routes (to test longest prefix).
    40% chance: choose something that falls only to default.
    """
    if random.random() < 0.6:
        # pick a non-default route and choose an IP inside it (not network/bcast)
        non_default = [r for r in routes if r["dest"].prefixlen != 0]
        if non_default:
            r = random.choice(non_default)
            net = r["dest"]
            # pick a usable host if possible
            if net.num_addresses > 2:
                host_index = random.randint(1, net.num_addresses - 2)
                return ipaddress.IPv4Address(int(net.network_address) + host_index)
            else:
                return net.network_address
    # otherwise pick random address from private/test ranges
    pool = [
        ipaddress.IPv4Network("10.0.0.0/8"),
        ipaddress.IPv4Network("172.16.0.0/12"),
        ipaddress.IPv4Network("192.168.0.0/16"),
        ipaddress.IPv4Network("198.51.100.0/24"),
        ipaddress.IPv4Network("203.0.113.0/24"),
        ipaddress.IPv4Network("8.8.8.0/24"),
    ]
    base = random.choice(pool)
    rnd_ip = int(base.network_address) + random.randint(0, base.num_addresses - 1)
    return ipaddress.IPv4Address(rnd_ip)

def longest_prefix_match(routes, ip):
    """
    Returns (best_route, matches_sorted)
    matches_sorted is all matching routes sorted by (prefixlen desc, metric asc).
    """
    matches = []
    for r in routes:
        if ip in r["dest"]:
            matches.append(r)
    # sort: longest prefix first, then metric ascending
    matches_sorted = sorted(matches, key=lambda r: (r["dest"].prefixlen, -1 * (10**9) + 0), reverse=False)
    # The above trick is ugly; do clearer:
    matches_sorted = sorted(matches, key=lambda r: (-r["dest"].prefixlen, r["metric"]))
    best = matches_sorted[0] if matches_sorted else None
    return best, matches_sorted

def render_table(routes):
    # Pretty print routing table
    lines = []
    lines.append("+---- Routing Table --------------------------------------------------+")
    lines.append("| Destination        | Next Hop        | Iface    | Metric | Note     |")
    lines.append("+---------------------------------------------------------------------+")
    for r in routes:
        dst = f"{str(r['dest']):<18}"
        nh  = f"{r['next_hop']:<15}"
        ifc = f"{r['iface']:<8}"
        met = f"{r['metric']:>6}"
        note = f"{r.get('desc',''):<8}"
        lines.append(f"| {dst} | {nh} | {ifc} | {met} | {note} |")
    lines.append("+---------------------------------------------------------------------+")
    return "\n".join(lines)

def ask_question(difficulty=2, practice=False):
    """
    Returns a dict with:
      {
        'correct': bool,
        'time': float,
        'points': int,
        'explain': str,
        'your_choice': {'type': 'next_hop' or 'iface', 'value': str},
        'answer': {'next_hop': str, 'iface': str},
        'ip': IPv4Address,
        'routes': [..]
      }
    """
    routes = build_routing_table(difficulty)
    ip = choose_destination_ip(routes)
    best, matches = longest_prefix_match(routes, ip)

    explain = []
    explain.append(render_table(routes))
    explain.append(f"\n📬 Destination IP: {ip}")
    if not best:
        explain.append("No routes matched. (This should not happen with a default present.)")

    # Build options: we’ll let player answer either by Next Hop or Interface.
    correct_next = best["next_hop"]
    correct_if = best["iface"]

    # Candidate choices:
    nhops = sorted({r["next_hop"] for r in routes})
    ifaces = sorted({r["iface"] for r in routes})

    # Show the summary/hints in practice mode
    if practice:
        explain.append("\nHow to choose next hop:")
        explain.append("1) Find ALL routes whose destination contains the IP.")
        explain.append("2) Select the route with the LONGEST prefix length (/xx).")
        explain.append("3) If there’s a tie on prefix length, choose the LOWEST metric.")
        explain.append("\nMatches (sorted: longest prefix, then lowest metric):")
        if matches:
            for idx, m in enumerate(matches, 1):
                explain.append(f"   {idx}. {m['dest']}  metric={m['metric']}  → next-hop {m['next_hop']}  iface {m['iface']}")
        else:
            explain.append("   (No match — default would apply if present.)")

    print("\n" + "\n".join(explain))
    print("\nAnswer format:")
    print("  Type 'nh' to answer by Next Hop, or 'if' to answer by Interface.")
    print("  Or type 'q' to quit this question.")
    t0 = time.time()
    while True:
        mode = input("\nChoose answer type [nh/if]: ").strip().lower()
        if mode in ("q", "quit", "exit"):
            return {"quit": True}

        if mode == "nh":
            print("\nAvailable next hops:")
            for i, nh in enumerate(nhops, 1):
                print(f"  {i}) {nh}")
            idx = choose_int("Select next hop number: ", 1, len(nhops))
            if idx is None:
                return {"quit": True}
            choice = nhops[idx-1]
            elapsed = time.time() - t0
            correct = (choice == correct_next)
            points, detail = score_question(correct, elapsed)
            feedback = build_feedback(ip, routes, best, matches, choice, "next-hop", detail)
            return {
                "quit": False, "correct": correct, "time": elapsed, "points": points,
                "explain": feedback,
                "your_choice": {"type": "next_hop", "value": choice},
                "answer": {"next_hop": correct_next, "iface": correct_if},
                "ip": ip, "routes": routes
            }

        if mode == "if":
            print("\nAvailable interfaces:")
            for i, ifc in enumerate(ifaces, 1):
                print(f"  {i}) {ifc}")
            idx = choose_int("Select interface number: ", 1, len(ifaces))
            if idx is None:
                return {"quit": True}
            choice = ifaces[idx-1]
            elapsed = time.time() - t0
            correct = (choice == correct_if)
            points, detail = score_question(correct, elapsed)
            feedback = build_feedback(ip, routes, best, matches, choice, "interface", detail)
            return {
                "quit": False, "correct": correct, "time": elapsed, "points": points,
                "explain": feedback,
                "your_choice": {"type": "iface", "value": choice},
                "answer": {"next_hop": correct_next, "iface": correct_if},
                "ip": ip, "routes": routes
            }

        print("Please enter 'nh' or 'if' (or 'q' to quit).")

def score_question(correct, elapsed):
    """
    Simple scoring:
      - Correct: 100 base + time bonus (max +50 if <= 5s, linearly decreases to 0 by 20s)
      - Wrong: 0
    """
    if not correct:
        return 0, "Wrong (0 pts)."
    base = 100
    # time bonus from 5s (50pts) down to 20s (0pts), clipped
    if elapsed <= 5:
        bonus = 50
    elif elapsed >= 20:
        bonus = 0
    else:
        # linear
        bonus = int(round(50 * (20 - elapsed) / 15))
    return base + bonus, f"Correct: 100 base + {bonus} time bonus = {base+bonus} pts."

def build_feedback(ip, routes, best, matches, choice, choice_type, score_detail):
    lines = []
    lines.append("\n──────── Result Breakdown ────────")
    lines.append(render_table(routes))
    lines.append(f"\nDestination IP: {ip}")
    lines.append("\nAll matching routes (sorted by longest prefix then lowest metric):")
    if matches:
        for idx, m in enumerate(matches, 1):
            lines.append(f"  {idx}. {m['dest']}  metric={m['metric']}  → next-hop {m['next_hop']}  iface {m['iface']}")
    else:
        lines.append("  (No specific match; default applies.)")
    lines.append("\nFinal selection:")
    lines.append(f"  → {best['dest']} (/{best['dest'].prefixlen})  metric={best['metric']}")
    lines.append(f"  ✓ Next Hop: {best['next_hop']}   ✓ Interface: {best['iface']}")
    if choice_type == "next-hop":
        if choice == best["next_hop"]:
            lines.append("✅ You chose the correct next hop.")
        else:
            # find where they went off
            wrong = None
            for m in matches:
                if m["next_hop"] == choice:
                    wrong = m
                    break
            if wrong is None:
                lines.append("❌ Your next hop doesn’t match any chosen route.")
            else:
                lines.append("❌ You chose a next hop from a non-best match.")
                lines.append(f"   Where you went off: {wrong['dest']} (/{wrong['dest'].prefixlen}) metric={wrong['metric']}")
                if wrong["dest"].prefixlen < best["dest"].prefixlen:
                    lines.append("   Reason: Not the longest prefix.")
                elif wrong["dest"].prefixlen == best["dest"].prefixlen and wrong["metric"] > best["metric"]:
                    lines.append("   Reason: Tie on prefix length; your route has a worse metric.")
    else:
        if choice == best["iface"]:
            lines.append("✅ You chose the correct interface.")
        else:
            wrong = None
            for m in matches:
                if m["iface"] == choice:
                    wrong = m
                    break
            if wrong is None:
                lines.append("❌ Your interface doesn’t match any chosen route.")
            else:
                lines.append("❌ You chose an interface from a non-best match.")
                lines.append(f"   Where you went off: {wrong['dest']} (/{wrong['dest'].prefixlen}) metric={wrong['metric']}")
                if wrong["dest"].prefixlen < best["dest"].prefixlen:
                    lines.append("   Reason: Not the longest prefix.")
                elif wrong["dest"].prefixlen == best["dest"].prefixlen and wrong["metric"] > best["metric"]:
                    lines.append("   Reason: Tie on prefix length; your route has a worse metric.")

    lines.append(f"\nScoring: {score_detail}")
    lines.append("──────────────────────────────────")
    return "\n".join(lines)

# ----------------------------- Game Modes -----------------------------

def choose_difficulty():
    clear()
    print("🎮 Select Difficulty")
    print("1) Beginner  – fewer routes, minimal overlap")
    print("2) Standard  – some overlaps, default present")
    print("3) Expert    – multiple overlaps + metric tie-breaks")
    ans = choose_int("Choose 1-3: ", 1, 3)
    if ans is None:
        return None
    return ans

def mode_classic():
    diff = choose_difficulty()
    if diff is None:
        return
    clear()
    print("Classic Mode")
    n_q = choose_int("How many questions? (3-20, or 'q' to quit): ", 3, 20)
    if n_q is None:
        return
    total_points = 0
    correct_count = 0
    for i in range(1, n_q+1):
        clear()
        print(f"Question {i}/{n_q} — type 'q' anytime to stop")
        result = ask_question(difficulty=diff, practice=False)
        if result.get("quit"):
            print("\nExiting Classic mode early.")
            break
        print(result["explain"])
        total_points += result["points"]
        correct_count += 1 if result["correct"] else 0
        print(f"\nQuestion score: {result['points']} pts")
        print(f"Running total:  {total_points} pts  |  Correct: {correct_count}/{i}")
        press_enter()

    # Final summary and save score
    clear()
    print("📊 Classic Mode Summary")
    print(f"Questions answered: {i if 'i' in locals() else 0}")
    print(f"Correct:            {correct_count}")
    print(f"Total points:       {total_points}")
    name = input("\nEnter your name for the high-score board (or leave blank to skip): ").strip()
    if name:
        save_score("classic", name, total_points)
        print("Saved to high scores! 🎉")
    press_enter()

def mode_speedrun():
    diff = choose_difficulty()
    if diff is None:
        return
    duration = 60
    clear()
    print("⏱️  Speedrun (60 seconds)")
    print("Answer as many as you can. Points = sum of question points.")
    print("Type 'q' anytime to end early.")
    press_enter()
    total_points = 0
    correct_count = 0
    q_count = 0
    t_end = time.time() + duration

    while time.time() < t_end:
        clear()
        print(f"Time left: {max(0, int(t_end - time.time()))} seconds")
        print(f"Score: {total_points} pts | Correct: {correct_count}/{q_count}")
        result = ask_question(difficulty=diff, practice=False)
        if result.get("quit"):
            print("\nExiting Speedrun early.")
            break
        q_count += 1
        total_points += result["points"]
        correct_count += 1 if result["correct"] else 0
        print(result["explain"])
        print(f"\nQuestion score: {result['points']} pts")
        print(f"Running total:  {total_points} pts")
        # tiny pause so player can glance, but don't block time—use quick prompt
        _ = input("\n(Enter to continue; 'q' to stop early) ").strip().lower()
        if _ in ("q", "quit", "exit"):
            break

    clear()
    print("📊 Speedrun Summary")
    print(f"Questions answered: {q_count}")
    print(f"Correct:            {correct_count}")
    print(f"Total points:       {total_points}")
    name = input("\nEnter your name for the high-score board (or leave blank to skip): ").strip()
    if name:
        save_score("speedrun", name, total_points)
        print("Saved to high scores! 🎉")
    press_enter()

def mode_practice():
    diff = choose_difficulty()
    if diff is None:
        return
    while True:
        clear()
        print("📘 Practice / Instruction Mode")
        print("This mode walks you through each decision step-by-step.")
        print("Type 'q' at any prompt to exit.")
        res = ask_question(difficulty=diff, practice=True)
        if res.get("quit"):
            break
        print(res["explain"])
        # In practice, no points accrue, but show correctness
        if res["your_choice"]["type"] == "next_hop":
            c = "correct" if res["your_choice"]["value"] == res["answer"]["next_hop"] else "wrong"
            print(f"\nYour next hop was {c}.")
        else:
            c = "correct" if res["your_choice"]["value"] == res["answer"]["iface"] else "wrong"
            print(f"\nYour interface choice was {c}.")
        ans = input("\nAnother practice question? [Y/n]: ").strip().lower()
        if ans in ("n", "no", "q", "quit", "exit"):
            break

# ----------------------------- Help Screen -----------------------------

HELP_TEXT = """
📖 Next Hop Trainer — Instructions

Goal
----
Given a destination IP and a routing table, choose the next hop (or interface)
the router will use. The rule is:

1) Longest-Prefix Match:
   Pick the route with the most-specific prefix (largest /xx).
   Example: /27 beats /24 beats /16.

2) Tie-Break by Metric:
   If two (or more) routes have the same prefix length and both match,
   choose the one with the lowest metric.

3) Default Route:
   If no specific route matches, the default route 0.0.0.0/0 applies.

Game Modes
----------
• Classic: Answer a fixed number of questions, earn points per question
  (100 base + up to +50 time bonus). High score is saved.

• Speedrun (60s): As many questions as you can in one minute. Points add up
  just like Classic. High score is saved.

• Practice/Instruction: Step-by-step walk-through of each decision, including
  the list of matching routes sorted by longest prefix then metric.

Controls & Tips
---------------
• You can answer by Next Hop (NH) or by Interface (IF).
• Type 'q' or 'quit' or 'exit' at most inputs to leave a screen or mode.
• Faster correct answers mean higher time bonuses in Classic/Speedrun.
• The routing table is randomized every question, including realistic overlaps.
"""

# ------------------------------- Main Menu -------------------------------

def main_menu():
    while True:
        clear()
        print("Next Hop Trainer — Network+")
        print("---------------------------")
        print("1) Classic (scored)")
        print("2) Speedrun (60s)")
        print("3) Practice / Instruction")
        print("4) View High Scores")
        print("5) Reset Scores")
        print("6) Help / Instructions")
        print("7) Quit")
        choice = input("\nSelect: ").strip().lower()
        if choice in ("7", "q", "quit", "exit"):
            print("Goodbye! 👋")
            return
        if choice == "1":
            mode_classic()
        elif choice == "2":
            mode_speedrun()
        elif choice == "3":
            mode_practice()
        elif choice == "4":
            show_high_scores()
        elif choice == "5":
            maybe_reset_scores()
        elif choice == "6":
            clear()
            print(HELP_TEXT)
            press_enter()
        else:
            print("Please choose 1-7.")
            time.sleep(1.0)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Bye!")
