#!/usr/bin/env python3
"""
7-Second Subnetting Game v2.5 — Cross-Platform Stable Edition
-------------------------------------------------------------
- Type 'h' for a context-aware hint (small point penalty).
- Type 'q' at ANY prompt to quit back to the menu.
- After each question:
  • 10-step solution key
  • Clear Right/Wrong for Magic, Network, Broadcast (+ your answers)
  • Question score, penalties, and running total

- "Interactive Tutorial" in the menu: new randomized example every time,
  you provide each step of the 7-second method (with hints).
- High scores saved in highscores.json
"""

import ipaddress
import json
import os
import random
import time
import sys

HIGHSCORE_FILE = "highscores.json"

# Scoring knobs
PTS_MAGIC = 1.0
PTS_NETWORK = 2.0
PTS_BROADCAST = 2.0
HINT_PENALTY = 0.5


# ----------------------- Persistence / UI -----------------------

def load_highscores():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_highscores(highscores):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(highscores, f, indent=2)


def print_highscores(highscores):
    if not highscores:
        print("\nNo high scores yet!\n")
        return
    print("\n🏆 HIGH SCORES 🏆")
    top = sorted(highscores, key=lambda x: (x["score"], -x["time"]), reverse=True)[:10]
    for i, entry in enumerate(top, start=1):
        print(f"{i}. {entry['name']} — {entry['score']:.1f} pts — {entry['time']:.1f}s avg")


# ----------------------- Subnet Math Helpers -----------------------

def mask_from_cidr(cidr):
    return str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)


def mask_octets_from_cidr(cidr):
    return list(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed)


def calculate_magic_number(cidr):
    for o in mask_octets_from_cidr(cidr):
        if o != 255:
            return 256 - o
    return 1


def changed_octet_index(cidr):
    for i, o in enumerate(mask_octets_from_cidr(cidr)):
        if o != 255:
            return i
    return 3


def network_broadcast(ip, cidr):
    net = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
    return str(net.network_address), str(net.broadcast_address)


def host_range(ip, cidr):
    net = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
    if net.prefixlen >= 31:
        return None
    hosts = list(net.hosts())
    return str(hosts[0]), str(hosts[-1])


def blocks_in_octet(magic):
    return [(i, min(i + magic - 1, 255)) for i in range(0, 256, magic)]


def locate_block(value, magic):
    start = (value // magic) * magic
    end = min(start + magic - 1, 255)
    return start, end


# ----------------------- Hints -----------------------

def hint_magic_number(cidr):
    return f"Mask is {mask_from_cidr(cidr)} → Magic = 256 − (first non-255 octet)."


def hint_network_address(ip, cidr):
    mi = changed_octet_index(cidr)
    magic = calculate_magic_number(cidr)
    octet_names = ["1st", "2nd", "3rd", "4th"]
    ip_oct = list(map(int, ip.split(".")))
    return (f"Changing octet is the {octet_names[mi]} (mask {mask_from_cidr(cidr)}). "
            f"Take IP octet value {ip_oct[mi]}, find its {magic}-block; "
            f"network = block start, later octets → 0.")


def hint_broadcast_address(cidr):
    magic = calculate_magic_number(cidr)
    return f"Broadcast = (network octet + {magic} − 1), later octets → 255."


# ----------------------- Input helpers -----------------------

class QuitGame(Exception):
    pass


def ask(prompt):
    """Input with 'q' to quit, returns stripped string."""
    s = input(prompt).strip()
    if s.lower() == 'q':
        raise QuitGame()
    return s


def ask_with_hint(prompt, hint_text, penalties_counter):
    """Input that supports 'h' for a hint and 'q' to quit."""
    s = input(prompt).strip()
    if s.lower() == 'q':
        raise QuitGame()
    if s.lower() == 'h':
        print("💡 Hint:", hint_text)
        penalties_counter[0] += 1
        s = input(prompt).strip()
        if s.lower() == 'q':
            raise QuitGame()
    return s


# ----------------------- Step-by-Step Explanation -----------------------

def step_by_step_explanation(ip, cidr, user_magic, user_net, user_bc):
    correct_net, correct_bc = network_broadcast(ip, cidr)
    m = calculate_magic_number(cidr)
    mask = mask_from_cidr(cidr)
    ip_oct = list(map(int, ip.split(".")))
    mi = changed_octet_index(cidr)
    blocks = blocks_in_octet(m)
    start, end = locate_block(ip_oct[mi], m)

    net_oct = ip_oct[:]
    bc_oct = ip_oct[:]
    net_oct[mi], bc_oct[mi] = start, end
    for j in range(mi + 1, 4):
        net_oct[j], bc_oct[j] = 0, 255
    manual_net = ".".join(map(str, net_oct))
    manual_bc = ".".join(map(str, bc_oct))
    host_rng = host_range(ip, cidr)

    print("\n🔍 Step-by-step solution (10 steps):")
    print(f"1) Given IP/CIDR: {ip}/{cidr}")
    print(f"2) Convert CIDR → Mask: /{cidr} → {mask}")
    print(f"3) Find changing octet: first non-255 in mask is octet #{mi+1}")
    print(f"4) Magic number = 256 − (mask octet) = {m}")
    print(f"5) Changing-octet value in IP = {ip_oct[mi]}")
    print(f"6) Subnet blocks in that octet go by {m}: "
          + ", ".join([f"{a}-{b}" for (a, b) in blocks[:min(7, len(blocks))]])
          + (" ..." if len(blocks) > 7 else ""))
    print(f"7) {ip_oct[mi]} falls in block {start}-{end}")
    print(f"8) Network = set changing octet to block start and later octets to 0 → {manual_net}")
    print(f"9) Broadcast = set changing octet to block end and later octets to 255 → {manual_bc}")
    if host_rng:
        print(f"10) Host range = {host_rng[0]} – {host_rng[1]}")
    else:
        print("10) /31 or /32 → no usable host range")

    # Clear Right/Wrong recap
    print("\n🧾 Your answers vs correct:")
    print(f"• Magic number:   you → {user_magic!s:<5} | correct → {m} | "
          f"{'✅' if user_magic == str(m) else '❌'}")
    print(f"• Network address: you → {user_net:<15} | correct → {manual_net} | "
          f"{'✅' if user_net == manual_net else '❌'}")
    print(f"• Broadcast addr:  you → {user_bc:<15} | correct → {manual_bc} | "
          f"{'✅' if user_bc == manual_bc else '❌'}")

    wrongs = []
    if user_magic != str(m):
        wrongs.append(f"• Magic number you gave: {user_magic} (correct: {m})")
    if user_net != manual_net:
        wrongs.append(f"• Network you gave: {user_net} (correct: {manual_net})")
    if user_bc != manual_bc:
        wrongs.append(f"• Broadcast you gave: {user_bc} (correct: {manual_bc})")

    if wrongs:
        print("\n❌ Where you went off:")
        for w in wrongs:
            print(w)
    print("")


# ----------------------- Question -----------------------

def generate_random_ip():
    # Use private ranges for realism
    private_ranges = [
        ("10.0.0.0", 8),
        ("172.16.0.0", 12),
        ("192.168.0.0", 16),
    ]
    base, base_prefix = random.choice(private_ranges)
    net = ipaddress.ip_network(f"{base}/{base_prefix}", strict=False)
    return str(random.choice(list(net.hosts())))


def generate_random_cidr():
    return random.randint(16, 30)


def play_question(qnum, total_qs, running_total):
    ip = generate_random_ip()
    cidr = generate_random_cidr()
    magic = calculate_magic_number(cidr)
    correct_net, correct_bc = network_broadcast(ip, cidr)

    print(f"\n🔹 Question {qnum} of {total_qs}  (type 'h' for hint, 'q' to quit)")
    print(f"IP: {ip}/{cidr}")

    start = time.time()
    penalties = [0]  # mutable for hint counting
    q_points_earned = 0.0
    breakdown = []

    # Magic Number
    try:
        user_magic = ask_with_hint("Magic number: ", hint_magic_number(cidr), penalties)
    except QuitGame:
        return None  # signal quit

    if user_magic == str(magic):
        q_points_earned += PTS_MAGIC
        breakdown.append(f"+{PTS_MAGIC:.1f} Magic")
    else:
        breakdown.append("0.0 Magic")

    # Network
    try:
        user_net = ask_with_hint("Network address: ", hint_network_address(ip, cidr), penalties)
    except QuitGame:
        return None

    net_correct = (user_net == correct_net)
    if net_correct:
        q_points_earned += PTS_NETWORK
        breakdown.append(f"+{PTS_NETWORK:.1f} Network")
    else:
        breakdown.append("0.0 Network")

    # Broadcast
    try:
        user_bc = ask_with_hint("Broadcast address: ", hint_broadcast_address(cidr), penalties)
    except QuitGame:
        return None

    bc_correct = (user_bc == correct_bc)
    if bc_correct:
        q_points_earned += PTS_BROADCAST
        breakdown.append(f"+{PTS_BROADCAST:.1f} Broadcast")
    else:
        breakdown.append("0.0 Broadcast")

    elapsed = time.time() - start
    penalty_points = penalties[0] * HINT_PENALTY
    # --- Time-based bonus ---
    # Faster than 7 seconds earns up to +1.5 pts; slower loses up to −1 pt.
    if elapsed <= 7:
        time_bonus = round((7 - elapsed) * 0.2, 2)   # e.g., 5 s = +0.4 pts
    else:
        time_bonus = round(-(elapsed - 7) * 0.1, 2)  # e.g., 10 s = −0.3 pts
    time_bonus = max(min(time_bonus, 1.5), -1.0)

    # Final question score
    q_score = max(0.0, q_points_earned - penalty_points + time_bonus)
    running_total += q_score

    # Show definitive answers
    print(f"\n✅ Correct answers:")
    print(f"   Magic number: {magic}")
    print(f"   Network:      {correct_net}")
    print(f"   Broadcast:    {correct_bc}")
    hr = host_range(ip, cidr)
    print(f"   Host range:   {hr[0]} – {hr[1]}" if hr else "   Host range:   (none for /31 or /32)")

    # Right/Wrong recap + 10-step explainer
    step_by_step_explanation(ip, cidr, user_magic, user_net, user_bc)

    # Scores
    print("📊 Scoring:")
    print("   Breakdown: " + ", ".join(breakdown) +
        (f", −{penalties[0]*HINT_PENALTY:.1f} hints" if penalties[0] else "") +
        f", {time_bonus:+.1f} time bonus")
    print(f"   Question Score: {q_score:.1f}  |  Time: {elapsed:.1f}s")
    print(f"   Running Total:  {running_total:.1f} points\n")


    return q_score, elapsed, running_total


# ----------------------- Interactive Tutorial -----------------------

def interactive_tutorial():
    """New randomized example each time; user provides each step."""
    ip = generate_random_ip()
    cidr = generate_random_cidr()
    mask = mask_from_cidr(cidr)
    mi = changed_octet_index(cidr)
    magic = calculate_magic_number(cidr)
    ip_oct = list(map(int, ip.split(".")))
    start, end = locate_block(ip_oct[mi], magic)
    correct_net, correct_bc = network_broadcast(ip, cidr)
    hr = host_range(ip, cidr)

    print("\n📘 Interactive Tutorial — new example")
    print("Type 'h' for a hint or 'q' to quit tutorial.\n")
    print(f"Given: IP/CIDR → {ip}/{cidr}\n")

    # 1) Mask
    try:
        s = ask_with_hint("1) What is the subnet mask? ",
                          f"/{cidr} → {mask}", [0])
    except QuitGame:
        return
    print("   ✅ Correct!" if s == mask else f"   ❌ Correct: {mask}")

    # 2) Changing octet (1-4)
    try:
        s = ask_with_hint("2) Which octet changes? (1-4): ",
                          "First non-255 octet in the mask.", [0])
    except QuitGame:
        return
    try:
        given_idx = int(s)
    except ValueError:
        given_idx = -1
    print("   ✅ Correct!" if given_idx == mi + 1 else f"   ❌ Correct: {mi+1}")

    # 3) Magic number
    try:
        s = ask_with_hint("3) Magic number (256 - mask octet): ",
                          hint_magic_number(cidr), [0])
    except QuitGame:
        return
    print("   ✅ Correct!" if s == str(magic) else f"   ❌ Correct: {magic}")

    # 4) Which block does the changing octet fall into? (format: start-end)
    try:
        s = ask_with_hint(f"4) The IP’s changing-octet value is {ip_oct[mi]}. "
                          f"Which {magic}-block? (e.g., {start}-{end}): ",
                          "Compute start = (val//magic)*magic; end = start+magic-1.", [0])
    except QuitGame:
        return
    print("   ✅ Correct!" if s == f"{start}-{end}" else f"   ❌ Correct: {start}-{end}")

    # 5) Network address
    try:
        s = ask_with_hint("5) Network address: ",
                          hint_network_address(ip, cidr), [0])
    except QuitGame:
        return
    print("   ✅ Correct!" if s == correct_net else f"   ❌ Correct: {correct_net}")

    # 6) Broadcast address
    try:
        s = ask_with_hint("6) Broadcast address: ",
                          hint_broadcast_address(cidr), [0])
    except QuitGame:
        return
    print("   ✅ Correct!" if s == correct_bc else f"   ❌ Correct: {correct_bc}")

    # 7/8) Hosts if applicable
    if hr:
        try:
            s = ask_with_hint("7) First usable host: ",
                              "Network + 1 in the last octet (unless /31 or /32).", [0])
        except QuitGame:
            return
        print("   ✅ Correct!" if s == hr[0] else f"   ❌ Correct: {hr[0]}")
        try:
            s = ask_with_hint("8) Last usable host: ",
                              "Broadcast − 1 in the last octet (unless /31 or /32).", [0])
        except QuitGame:
            return
        print("   ✅ Correct!" if s == hr[1] else f"   ❌ Correct: {hr[1]}")
        steps_done = 8
    else:
        steps_done = 6

    print("\n🎯 Tutorial recap complete! Press Enter to return to the menu.")
    input()


# ----------------------- Game Loop -----------------------

def play_game():
    highscores = load_highscores()
    print_highscores(highscores)
    name = input("\nEnter your name: ").strip() or "Anonymous"

    while True:
        try:
            total_qs = int(input("How many questions would you like? (e.g., 5): ").strip())
            if total_qs > 0:
                break
        except ValueError:
            pass
        print("Please enter a positive integer.\n")

    total_score, total_time = 0.0, 0.0
    running_total = 0.0

    for q in range(1, total_qs + 1):
        try:
            result = play_question(q, total_qs, running_total)
        except QuitGame:
            print("\n⬅ Exiting to main menu...\n")
            return
        if result is None:
            print("\n⬅ Exiting to main menu...\n")
            return
        q_score, t_elapsed, running_total = result
        total_score += q_score
        total_time += t_elapsed

    avg_time = total_time / total_qs if total_qs else 0.0
    print(f"\n🏁 Final Score: {total_score:.1f} pts")
    print(f"⌛ Avg Time per Question: {avg_time:.1f}s")

    highscores.append({"name": name, "score": total_score, "time": avg_time})
    save_highscores(highscores)
    print_highscores(highscores)

    input("\nPress Enter to return to main menu...")


# ----------------------- Menu -----------------------

def main_menu():
    while True:
        print("\n=== 🧮 7-Second Subnetting Game ===")
        print("1) Play Game")
        print("2) Interactive Tutorial (new example)")
        print("3) View High Scores")
        print("4) Quit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            play_game()
        elif choice == "2":
            interactive_tutorial()
        elif choice == "3":
            print_highscores(load_highscores())
            input("\nPress Enter to return to menu...")
        elif choice == "4":
            print("Goodbye! 👋")
            sys.exit(0)
        else:
            print("Invalid selection. Try again.\n")


if __name__ == "__main__":
    main_menu()
