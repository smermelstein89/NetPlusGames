
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

ALLOWED_COMMANDS = {
    "date",
    "file",
    "wc",
    "head",
    "tail",
    "timedatectl",
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
# UTILITIES
# ===============================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def execute_command(cmd: str) -> str:
    parts = shlex.split(cmd)
    if not parts:
        return ""
    base = parts[0]
    if base not in ALLOWED_COMMANDS:
        return f"bash: {base}: command not found"
    try:
        result = subprocess.run(parts, capture_output=True, text=True, check=False)
        return result.stdout.strip()
    except Exception as e:
        return f"Error executing command: {e}"


def create_default_level():
    if not os.path.exists(LEVELS_DIR):
        os.makedirs(LEVELS_DIR)

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


def load_levels():
    if not os.path.exists(LEVELS_DIR):
        create_default_level()

    json_files = [f for f in os.listdir(LEVELS_DIR) if f.endswith(".json")]

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

    # 🔥 If old format (list), convert it
    if isinstance(scores, list):
        scores = {"Legacy": scores}

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
        clear_screen()
        print("==============================")
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

        input("\nPress Enter to return to the main menu...")

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


# ===============================
# MAIN
# ===============================

def main():
    while True:
        clear_screen()

        print("==============================")
        print("🟥 RHCSA TRAINING PLATFORM 🟥")
        print("==============================")
        print("1. Play Level")
        print("2. View Leaderboard")
        print("3. Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            levels = load_levels()

            print("\nAvailable Levels:\n")
            for i, lvl in enumerate(levels, 1):
                print(f"{i}. {lvl['level_name']} - {lvl.get('description','')}")

            try:
                level_choice = int(input("\nSelect a level: ")) - 1
                if level_choice < 0 or level_choice >= len(levels):
                    input("Invalid selection. Press Enter to continue...")
                    continue
            except ValueError:
                input("Invalid input. Press Enter to continue...")
                continue

            game = RHCSAGame()
            game.load_level(levels[level_choice])
            game.run()

        elif choice == "2":
            show_leaderboard()

        elif choice == "3":
            print("Goodbye.")
            break

        else:
            input("Invalid selection. Press Enter to continue...")


if __name__ == "__main__":
    main()
