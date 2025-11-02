def choose_difficulty():
    print("\n🎮 Select Difficulty:")
    print("1) Casual   – 30 s per question (easiest)")
    print("2) Standard – 15 s per question (default)")
    print("3) Speedrun – 7 s per question (hardcore)")
    choice = input("> ").strip()

    if choice == "1":
        return 30.0
    elif choice == "3":
        return 7.0
    else:
        return 15.0

# In your play() function, replace BASE_TIME with a local variable:
def play(name, data):
    base_time = choose_difficulty()      # <— user picks it here
    print(f"\nYou selected {base_time}s base time per question.\n")

    # use base_time instead of global BASE_TIME inside get_time_for_question:
    def get_time_for_question(q):
        if q < 10: return base_time - q*1
        elif q < 20: return base_time - 9 - (q-9)*2
        elif q < 30: return base_time - 9 - 10*2 - (q-19)*3
        elif q < 40: return base_time - 9 - 10*2 - 10*3 - (q-29)*4
        else:
            reduction = 9 + 20 + 30 + (q-39)*5
            return max(base_time - reduction, MIN_TIME)

    # rest of play() logic stays the same
