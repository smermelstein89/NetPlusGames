import random
import time
import os

OCTETS = [255, 254, 252, 248, 240, 224, 192, 128, 0]

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def cidr_from_mask(mask):
    return sum(bin(int(o)).count("1") for o in mask.split("."))

def generate_mask():
    # choose a random octet to "break"
    change_index = random.randint(1, 4)
    mask = []
    for i in range(1, 5):
        if i < change_index:
            mask.append(255)
        elif i == change_index:
            mask.append(random.choice(OCTETS[1:-1]))  # avoid 255 and 0 for realism
        else:
            mask.append(0)
    return ".".join(map(str, mask)), change_index

def choose_difficulty():
    print("\n🎮 Select Difficulty:")
    print("1) Casual   – unlimited time")
    print("2) Standard – 10 seconds per question")
    print("3) Speedrun – 5 seconds per question")
    choice = input("> ").strip()
    if choice == "1":
        return None
    elif choice == "3":
        return 5
    else:
        return 10

def play():
    clear()
    print("🌐 Welcome to Octet Identifier!")
    print("Your task: Identify which octet changed from 255 → something else.\n")
    time_limit = choose_difficulty()
    streak = 0

    while True:
        mask, answer = generate_mask()
        cidr = cidr_from_mask(mask)
        clear()
        print(f"🕹️  Subnet Mask: {mask}  (/{cidr})")
        print("Which octet changed from 255?")
        print("(1) First   (2) Second   (3) Third   (4) Fourth")
        if time_limit:
            print(f"⏱️ You have {time_limit} seconds.")

        start = time.time()
        user_input = input("> ").strip()
        elapsed = time.time() - start

        if time_limit and elapsed > time_limit:
            print("⏰ Time’s up!")
            break

        if user_input not in {"1", "2", "3", "4"}:
            print("⚠️ Invalid input. Use 1–4.")
            time.sleep(1)
            continue

        if int(user_input) == answer:
            streak += 1
            print(f"✅ Correct! Streak: {streak}")
        else:
            print(f"❌ Nope. It changed in octet {answer}.")
            break

        time.sleep(1)

    print(f"\n🏁 Final Streak: {streak}")
    print("Thanks for playing Octet Identifier!")

if __name__ == "__main__":
    play()
