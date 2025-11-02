#!/usr/bin/env python3
"""
7-Second Subnetting Game (Hints + Step-by-Step Explanations)
------------------------------------------------------------
- Press 'h' at any prompt for a context-aware hint (small point penalty).
- If any answer is wrong, the game prints a step-by-step solution:
  * Mask & changing octet
  * Magic number
  * Which range/block the IP falls into
  * Network, broadcast, and host range
- High scores persisted to highscores.json

Author: You + ChatGPT
"""

import ipaddress
import json
import os
import random
import time

HIGHSCORE_FILE = "highscores.json"


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


# ----------------------- Question generation -----------------------

def generate_random_ip():
    # Random host within a private range
    private_ranges = [
        ("10.0.0.0", 8),
        ("172.16.0.0", 12),   # 172.16.0.0–172.31.255.255
        ("192.168.0.0", 16)
    ]
    base, base_prefix = random.choice(private_ranges)
    net = ipaddress.ip_network(f"{base}/{base_prefix}", strict=False)
    return str(random.choice(list(net.hosts())))

def generate_random_cidr():
    # Cover a realistic practice band; feel free to tweak
    return random.randint(16, 30)


# ----------------------- Subnet math helpers -----------------------

def mask_from_cidr(cidr):
    return str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)

def mask_octets_from_cidr(cidr):
    m = ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask.packed
    return list(m)

def calculate_magic_number(cidr):
    # Magic = 256 - (first non-255 octet of mask)
    for o in mask_octets_from_cidr(cidr):
        if o != 255:
            return 256 - o
    return 1

def changed_octet_index(cidr):
    # 0-based index of where the mask first differs from 255
    for i, o in enumerate(mask_octets_from_cidr(cidr)):
        if o != 255:
            return i
    return 3  # default to last octet (shouldn't happen for /0–/32)

def network_broadcast(ip, cidr):
    net = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
    return str(net.network_address), str(net.broadcast_address)

def host_range(ip, cidr):
    net = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
    if net.prefixlen >= 31:
        return None  # /31 and /32 have no usable host range
    first = str(list(net.hosts())[0])
    last  = str(list(net.hosts())[-1])
    return first, last

def blocks_in_octet(magic):
    # ranges: 0–(magic-1), magic–(2*magic-1), ... up to 255
    blocks = []
    start = 0
    while start < 256:
        end = min(start + magic - 1, 255)
        blocks.append((start, end))
        start += magic
    return blocks

def locate_block(value, magic):
    # returns (start, end) such that start <= value <= end
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
            f"Take that IP octet value ({ip_oct[mi]}), find the {magic}-block it falls into; "
            f"network is the block start with later octets set to 0.")

def hint_broadcast_address(cidr):
    magic = calculate_magic_number(cidr)
    return (f"Broadcast = (network octet + {magic} − 1) at the changing octet, "
            f"with later octets set to 255.")


# ----------------------- Explanation when wrong -----------------------

def step_by_step_explanation(ip, cidr, user_magic, user_net, user_bc):
    correct_net, correct_bc = network_broadcast(ip, cidr)
    m = calculate_magic_number(cidr)
    mask = mask_from_cidr(cidr)
    ip_oct = list(map(int, ip.split(".")))
    mi = changed_octet_index(cidr)
    blocks = blocks_in_octet(m)
    start, end = locate_block(ip_oct[mi], m)

    # Build network & broadcast via “manual” 7-second logic (for clarity)
    net_oct = ip_oct[:]  # copy
    bc_oct  = ip_oct[:]
    net_oct[mi] = start
    bc_oct[mi]  = end
    for j in range(mi + 1, 4):
        net_oct[j] = 0
        bc_oct[j]  = 255
    manual_net = ".".join(map(str, net_oct))
    manual_bc  = ".".join(map(str, bc_oct))

    host_rng = host_range(ip, cidr)

    print("\n🔍 Step-by-step solution (7-second method):")
    print(f"1) Given IP/CIDR: {ip}/{cidr}")
    print(f"2) Convert CIDR → Mask: /{cidr} → {mask}")
    print(f"3) Find changing octet: first non-255 in mask is octet #{mi+1}")
    print(f"4) Magic number = 256 − (mask octet) = {m}")
    print(f"5) Look at IP’s changing octet value: {ip_oct[mi]}")
    print(f"6) Subnet blocks in that octet go by {m}: "
          + ", ".join([f"{a}-{b}" for (a,b) in blocks[:min(7, len(blocks))]])
          + (" ..." if len(blocks) > 7 else ""))
    print(f"7) {ip_oct[mi]} falls in block {start}-{end}")
    print(f"8) Network = set changing octet to block start and later octets to 0 → {manual_net}")
    print(f"9) Broadcast = set changing octet to block end and later octets to 255 → {manual_bc}")
    if host_rng:
        print(f"10) Host range = {host_rng[0]} – {host_rng[1]}")
    else:
        print("10) /31 or /32 → no usable host range")

    # Point out exactly what was wrong
    wrongs = []
    if user_magic is not None and user_magic != str(m):
        wrongs.append(f"• Magic number you gave: {user_magic} (correct: {m})")
    if user_net is not None and user_net != correct_net:
        wrongs.append(f"• Network you gave: {user_net} (correct: {correct_net})")
    if user_bc is not None and user_bc != correct_bc:
        wrongs.append(f"• Broadcast you gave: {user_bc} (correct: {correct_bc})")

    if wrongs:
        print("\n❌ Where things went off:")
        for line in wrongs:
            print(line)

    print("")  # spacing


# ----------------------- Game round -----------------------

def play_round():
    ip = generate_random_ip()
    cidr = generate_random_cidr()
    magic = calculate_magic_number(cidr)
    correct_net, correct_bc = network_broadcast(ip, cidr)

    print(f"\n🔹 IP: {ip}/{cidr}")
    print("Type your answers (or 'h' for a hint).")

    start = time.time()
    score = 0.0
    penalties = 0

    # --- Magic Number ---
    user_magic = input("Magic number: ").strip()
    if user_magic.lower() == "h":
        print("💡 Hint:", hint_magic_number(cidr))
        penalties += 1
        user_magic = input("Magic number: ").strip()
    magic_correct = (user_magic == str(magic))
    if magic_correct:
        score += 1

    # --- Network Address ---
    user_net = input("Network address: ").strip()
    if user_net.lower() == "h":
        print("💡 Hint:", hint_network_address(ip, cidr))
        penalties += 1
        user_net = input("Network address: ").strip()
    net_correct = (user_net == correct_net)
    if net_correct:
        score += 2

    # --- Broadcast Address ---
    user_bc = input("Broadcast address: ").strip()
    if user_bc.lower() == "h":
        print("💡 Hint:", hint_broadcast_address(cidr))
        penalties += 1
        user_bc = input("Broadcast address: ").strip()
    bc_correct = (user_bc == correct_bc)
    if bc_correct:
        score += 2

    elapsed = time.time() - start
    penalty_points = penalties * 0.5
    score = max(0.0, score - penalty_points)

    print(f"\n✅ Correct answers:")
    print(f"   Magic number: {magic}")
    print(f"   Network:      {correct_net}")
    print(f"   Broadcast:    {correct_bc}")
    hr = host_range(ip, cidr)
    if hr:
        print(f"   Host range:   {hr[0]} – {hr[1]}")
    else:
        print("   Host range:   (none for /31 or /32)")

    print(f"⏱  Time: {elapsed:.1f}s  |  Score this round: {score:.1f} "
          f"(−{penalty_points:.1f} hint penalty)\n")

    # If anything is wrong, print a step-by-step explanation
    if not (magic_correct and net_correct and bc_correct):
        step_by_step_explanation(ip, cidr, user_magic, user_net, user_bc)

    return score, elapsed


# ----------------------- Main -----------------------

def main():
    print("=== 🧮 7-Second Subnetting Game (Hints + Explanations) ===")
    highscores = load_highscores()
    print_highscores(highscores)

    name = input("\nEnter your name: ").strip() or "Anonymous"

    # rounds input guard
    while True:
        try:
            rounds = int(input("How many rounds? (e.g., 5): ").strip())
            if rounds > 0:
                break
        except ValueError:
            pass
        print("Please enter a positive integer.")

    total_score = 0.0
    total_time = 0.0

    for _ in range(rounds):
        s, t = play_round()
        total_score += s
        total_time += t

    avg_time = total_time / rounds
    print(f"\n🏁 Final Score: {total_score:.1f} points")
    print(f"⌛ Average Time per Round: {avg_time:.1f} seconds")

    highscores.append({
        "name": name,
        "score": total_score,
        "time": avg_time
    })
    save_highscores(highscores)
    print_highscores(highscores)


if __name__ == "__main__":
    main()
