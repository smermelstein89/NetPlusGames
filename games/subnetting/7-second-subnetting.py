#!/usr/bin/env python3
"""
7-Second Subnetting Game (with Hints)
-------------------------------------
Practice subnetting using the magic number method.
Type 'h' at any answer prompt to get a hint (penalty applied).

Tracks high scores in highscores.json.
"""

import ipaddress
import json
import os
import random
import time

HIGHSCORE_FILE = "highscores.json"

def load_highscores():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f)
    return []

def save_highscores(highscores):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(highscores, f, indent=2)

def print_highscores(highscores):
    if not highscores:
        print("\nNo high scores yet!\n")
        return
    print("\n🏆 HIGH SCORES 🏆")
    for i, entry in enumerate(sorted(highscores, key=lambda x: x["score"], reverse=True)[:10], start=1):
        print(f"{i}. {entry['name']} — {entry['score']} pts — {entry['time']:.1f}s avg")

def generate_random_ip():
    private_ranges = [("10.0.0.0", 8), ("172.16.0.0", 12), ("192.168.0.0", 16)]
    base, base_prefix = random.choice(private_ranges)
    network = ipaddress.ip_network(f"{base}/{base_prefix}", strict=False)
    host = random.choice(list(network.hosts()))
    return str(host)

def generate_random_cidr():
    return random.randint(16, 30)

def calculate_magic_number(cidr):
    mask = (0xffffffff << (32 - cidr)) & 0xffffffff
    mask_octets = [
        (mask >> 24) & 0xff,
        (mask >> 16) & 0xff,
        (mask >> 8) & 0xff,
        mask & 0xff
    ]
    for octet in mask_octets:
        if octet != 255:
            return 256 - octet
    return 1

def get_network_info(ip, cidr):
    net = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
    return str(net.network_address), str(net.broadcast_address)

def hint_magic_number(cidr):
    # show subnet mask & octet breakdown
    mask = str(ipaddress.ip_network(f"0.0.0.0/{cidr}").netmask)
    return f"Mask: {mask} → 256 - last non-255 octet = ?"

def hint_network_address(ip, cidr):
    magic = calculate_magic_number(cidr)
    return f"Check the octet where the mask changes. Subnets go by {magic}s."

def hint_broadcast_address():
    return "Broadcast = last address in the subnet (network + block_size - 1)."

def play_round():
    ip = generate_random_ip()
    cidr = generate_random_cidr()
    magic = calculate_magic_number(cidr)
    net, bc = get_network_info(ip, cidr)

    print(f"\n🔹 IP: {ip}/{cidr}")
    print("Type your answers (or 'h' for a hint).")

    start = time.time()
    score = 0
    penalties = 0

    # --- Magic Number ---
    user_magic = input("Magic number: ").strip()
    if user_magic.lower() == "h":
        print("💡 Hint:", hint_magic_number(cidr))
        penalties += 1
        user_magic = input("Magic number: ").strip()
    if user_magic == str(magic):
        score += 1

    # --- Network Address ---
    user_net = input("Network address: ").strip()
    if user_net.lower() == "h":
        print("💡 Hint:", hint_network_address(ip, cidr))
        penalties += 1
        user_net = input("Network address: ").strip()
    if user_net == net:
        score += 2

    # --- Broadcast Address ---
    user_bc = input("Broadcast address: ").strip()
    if user_bc.lower() == "h":
        print("💡 Hint:", hint_broadcast_address())
        penalties += 1
        user_bc = input("Broadcast address: ").strip()
    if user_bc == bc:
        score += 2

    elapsed = time.time() - start
    penalty_points = penalties * 0.5
    score = max(0, score - penalty_points)

    print(f"\n✅ Correct answers:")
    print(f"   Magic number: {magic}")
    print(f"   Network: {net}")
    print(f"   Broadcast: {bc}")
    print(f"⏱  Time: {elapsed:.1f}s  |  Score this round: {score} (−{penalty_points} hint penalty)\n")

    return score, elapsed

def main():
    print("=== 🧮 7-Second Subnetting Game (with Hints) ===")
    highscores = load_highscores()
    print_highscores(highscores)

    name = input("\nEnter your name: ").strip() or "Anonymous"

    total_score = 0
    total_time = 0
    rounds = int(input("How many rounds? (e.g., 5): "))

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
