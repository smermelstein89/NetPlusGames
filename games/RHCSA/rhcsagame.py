import os
import json
import time
import shlex
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional


# ===============================
# CONFIG
# ===============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEVELS_DIR = os.path.join(BASE_DIR, "levels")
HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscores.json")
UNLOCK_SCORE_THRESHOLD = 300
DIFFICULTIES = {
    "1": {"name": "Casual", "hint_penalty": 10, "speed_bonus_time": 20},
    "2": {"name": "Standard", "hint_penalty": 25, "speed_bonus_time": 15},
    "3": {"name": "Exam Mode", "hint_penalty": 100, "speed_bonus_time": 10}
}


ALLOWED_COMMANDS = {
    "date",
    "file",
    "wc",
    "head",
    "tail",
    "timedatectl",
    "passwd",
}


# ===============================
# DATA STRUCTURE
# ===============================

@dataclass
class Step:
    id: str
    prompt: str
    validator: Optional[Callable[[str], bool]] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None


# ===============================
# UTILITY FUNCTIONS
# ===============================

def execute_command(cmd: str) -> str:
    """
    Execute whitelisted system commands safely.
    """
    parts = shlex.split(cmd)

    if not parts:
        return ""

    base = parts[0]

    if base not in ALLOWED_COMMANDS:
        return f"bash: {base}: command not found"

    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error executing command: {e}"


def create_default_level():
    default_level = {
        "level_name": "CLI Basics",
        "description": "Fundamental shell commands",
        "steps": [
            {
                "id": "CLI-01",
                "prompt": "Display the current date and time.",
                "validator": "exact",
                "answer": "date",
                "hint": "Single command.",
                "explanation": "date shows system time."
            },
            {
                "id": "CLI-02",
                "prompt": "Display time in 24-hour format.",
                "validator": "contains",
                "answer": "%R",
                "hint": "Use a format string.",
                "explanation": "date +%R prints HH:MM."
            }
        ]
    }

    default_path = os.path.join(LEVELS_DIR, "cli_basics.json")

    with open(default_path, "w") as f:
        json.dump(default_level, f, indent=4)

    print("Created default level: cli_basics.json")


def load_levels():
    if not os.path.exists(LEVELS_DIR):
        os.makedirs(LEVELS_DIR)

    json_files = [
        f for f in os.listdir(LEVELS_DIR)
        if f.endswith(".json")
    ]

    if not json_files:
        create_default_level()
        json_files = ["cli_basics.json"]

    levels = []

    for file in json_files:
        full_path = os.path.join(LEVELS_DIR, file)
        with open(full_path, "r") as f:
            levels.append(json.load(f))

    return levels



def save_highscore(level_name, player_name, score):
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            scores = json.load(f)
    else:
        scores = {}

    if level_name not in scores:
        scores[level_name] = []

    scores[level_name].append({"name": player_name, "score": score})
    scores[level_name] = sorted(
        scores[level_name],
        key=lambda x: x["score"],
        reverse=True
    )[:10]

    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(scores, f, indent=4)

    return scores[level_name]



# ===============================
# GAME ENGINE
# ===============================

class RHCSAGame:

    def __init__(self):
        self.steps = []
        self.score = 0
        self.streak = 0
        self.level_name = ""
        self.start_time = None
        self.difficulty = None
    def select_difficulty(self):
        clear_screen()
        print("Select Difficulty:\n")

        for key, diff in DIFFICULTIES.items():
            print(f"{key}. {diff['name']}")

        choice = input("\nChoice: ").strip()
        self.difficulty = DIFFICULTIES.get(choice, DIFFICULTIES["2"])

    def build_validator(self, step_data):
        vtype = step_data.get("validator")

        if vtype == "exact":
            return lambda cmd: cmd.strip() == step_data["answer"]

        if vtype == "contains":
            return lambda cmd: step_data["answer"] in cmd

        if vtype == "starts_with":
            return lambda cmd: cmd.startswith(step_data["answer"])

        return None

    def load_level(self, level_data):
        self.level_name = level_data["level_name"]
        self.steps = []

        for s in level_data["steps"]:
            step = Step(
                id=s["id"],
                prompt=s["prompt"],
                validator=self.build_validator(s),
                hint=s.get("hint"),
                explanation=s.get("explanation")
            )
            self.steps.append(step)

    def run(self):
        print("\n==============================")
        print("🟥 RHCSA TRAINING PLATFORM 🟥")
        print("==============================")
        print(f"\nLevel: {self.level_name}")
        print("Type 'hint' for help. Ctrl+C to exit.\n")

        for index, step in enumerate(self.steps, 1):
            self.run_step(index, step)

        print("\n🏁 Level Complete!")
        print(f"Final Score: {self.score}")

        player = input("Enter your name for the leaderboard: ")
        scores = save_highscore(self.level_name, player, self.score)

        print("\n🏆 HIGH SCORES 🏆")
        for i, entry in enumerate(scores, 1):
            print(f"{i}. {entry['name']} - {entry['score']}")

    def run_step(self, index, step):
        print(f"\nSTEP {index}: {step.id}")
        print("-" * 40)
        print(step.prompt)

        attempts = 0
        hint_used = False
        self.start_time = time.time()

        while True:
            user_input = input("\n[RHC-SA PRACTICE] student@workstation$ ").strip()

            if not user_input:
                continue

            if user_input.lower() == "hint":
                if step.hint:
                    print(f"💡 Hint: {step.hint}")
                    hint_used = True
                else:
                    print("No hint available.")
                continue

            attempts += 1

            if step.validator and step.validator(user_input):

                elapsed = time.time() - self.start_time
                output = execute_command(user_input)

                if output:
                    print(output)

                points = 100
                points -= (attempts - 1) * 10

                if hint_used:
                    points -= 25

                if elapsed < 15:
                    points += 20

                self.streak += 1
                if self.streak >= 3:
                    points += 50

                points = max(points, 0)
                self.score += points

                print("✔ Correct")
                print(f"🏅 +{points} points")
                print(f"🔥 Streak: {self.streak}")
                print(f"💯 Total Score: {self.score}")

                if step.explanation:
                    print(f"📘 {step.explanation}")

                break

            else:
                self.streak = 0
                output = execute_command(user_input)
                if output:
                    print(output)
                print("✖ Incorrect. Try again or type 'hint'.")
        game = RHCSAGame()
        game.select_difficulty()
        game.load_level(levels[level_choice])
        game.run() 
        

# ===============================
# LEADERBOARD
# ===============================
def show_leaderboard():
    clear_screen()
    print("\n🏆 HIGH SCORES 🏆\n")

    if not os.path.exists(HIGHSCORE_FILE):
        print("No scores recorded yet.")
        input("\nPress Enter to return...")
        return

    with open(HIGHSCORE_FILE, "r") as f:
        scores = json.load(f)

    for level, entries in scores.items():
        print(f"\n=== {level} ===")
        for i, entry in enumerate(entries, 1):
            print(f"{i}. {entry['name']} - {entry['score']}")

    input("\nPress Enter to return to the main menu...")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def is_level_unlocked(level_name):
    if not os.path.exists(HIGHSCORE_FILE):
        return True

    with open(HIGHSCORE_FILE, "r") as f:
        scores = json.load(f)

    if level_name not in scores:
        return True

    top_score = max(entry["score"] for entry in scores[level_name])
    return top_score >= UNLOCK_SCORE_THRESHOLD
if not unlocked_levels[level_choice]:
    print("Level locked. Achieve required score to unlock.")
    input("Press Enter to continue...")
    continue


# ===============================
# MAIN
# ===============================

def main():
    while True:
        levels = load_levels()

        clear_screen()
        print("==============================")
        print("🟥 RHCSA TRAINING PLATFORM 🟥")
        print("==============================")
        print("1. Play Level")
        print("2. View Leaderboard")
        print("3. Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            if not levels:
                print("No levels available.")
                continue

            print("\nAvailable Levels:\n")

            unlocked_levels = []

            for i, lvl in enumerate(levels, 1):
                unlocked = is_level_unlocked(lvl["level_name"])
                status = "🔓" if unlocked else "🔒"
                print(f"{i}. {status} {lvl['level_name']} - {lvl.get('description','')}")
                unlocked_levels.append(unlocked)


            try:
                level_choice = int(input("\nSelect a level: ")) - 1
                if level_choice < 0 or level_choice >= len(levels):
                    print("Invalid selection.")
                    continue
            except ValueError:
                print("Invalid input.")
                continue

            game = RHCSAGame()
            game.load_level(levels[level_choice])
            clear_screen()
            game.run()
            input("\nPress Enter to return to the main menu...")

        elif choice == "2":
            show_leaderboard()

        elif choice == "3":
            print("Goodbye.")
            break

        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()
