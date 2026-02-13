# step 1: Imports & Data Structures (Top of File)
from dataclasses import dataclass
from typing import Callable, Optional
import datetime
import time
import json
import os

# step 2: Define the Step Object
@dataclass
class Step:
    id: str
    prompt: str
    expected_answer: Optional[str] = None
    validator: Optional[Callable[[str], bool]] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None

# step 3: Simulated “Red Hat” Environment, Mock file system for demonstration purposes
FAKE_FILES = {
    "/home/student/zcat": {
        "type": "ASCII text",
        "lines": [f"Line {i}" for i in range(1, 101)],
        "size": 100
    }
}

# step 4: Validators (Command Logic)
def is_date(cmd):
    return cmd == "date"

def is_date_24h(cmd):
    return cmd.startswith("date") and "%R" in cmd

def is_file_type(cmd):
    return cmd in ["file /home/student/zcat", "file ~/zcat"]

def is_wc(cmd):
    return cmd.startswith("wc") and "zcat" in cmd

def is_head_10(cmd):
    return cmd in ["head /home/student/zcat", "head -n 10 /home/student/zcat"]

def is_tail_10(cmd):
    return cmd in ["tail /home/student/zcat", "tail -n 10 /home/student/zcat"]

def is_repeat_previous(cmd):
    return cmd in ["!!", "!-1"]

def is_tail_20(cmd):
    return cmd.startswith("tail") and "-n 20" in cmd

def is_history_search(cmd):
    return "^R" in cmd

# Step 5 : shell Feedback (This Makes It Feel Real)
def shell_feedback(cmd):
    # Empty command → no feedback, just reprompt
    if not cmd.strip():
        return None

    parts = cmd.split()
    base = parts[0]

    allowed = ["date", "file", "wc", "head", "tail", "!!", "!-1"]

    if base not in allowed and "%R" not in cmd and "^R" not in cmd:
        return f"bash: {base}: command not found"

    return None


# step 6: game engine (Core loop)
class RHCSAGame:
    def __init__(self, steps):
        self.steps = steps
        self.current_step = 0

    def run(self):
        print("\n🟥 RHCSA COMMAND LINE PRACTICE 🟥\n")
        print("Type commands as you would on a Red Hat system.")
        print("Type 'hint' at any time for help.")
        print("Type Ctrl+C to exit.\n")


        while self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.run_step(step)
            self.current_step += 1

        print("\n✅ Lab complete.\n")

    def run_step(self, step):
        print(f"\nSTEP {self.current_step + 1}: {step.id}")
        print("-" * 50)
        print(step.prompt)

        while True:
            user_input = input("\n[RHC-SA PRACTICE] student@workstation$ ").strip()

            # Game-level commands FIRST
            if user_input.lower() == "hint" and step.hint:
                print(f"💡 Hint: {step.hint}")
                continue

            # Empty input → reprompt
            if not user_input:
                continue

            # Shell-like feedback SECOND
            feedback = shell_feedback(user_input)
            if feedback:
                print(feedback)
                continue

            if self.evaluate(step, user_input):
                print("✔ Correct")
                if step.explanation:
                    print(f"📘 {step.explanation}")
                break
            else:
                print("✖ Incorrect. Try again or type 'hint'.")

    def evaluate(self, step, user_input):
        if step.validator:
            return step.validator(user_input)
        if step.expected_answer:
            return user_input == step.expected_answer
        return False
    
# Step 7: Define the Lab Steps: Step Definitions (The Actual Steps)
steps = [
    Step(
        id="CLI-01",
        prompt="Use a command to display the current time and date.",
        validator=is_date,
        hint="There is a single command for this.",
        explanation="The date command displays the system date and time."
    ),

    Step(
        id="CLI-02",
        prompt="Display the current time in 24-hour format.",
        validator=is_date_24h,
        hint="Use a format string.",
        explanation="date +%R prints time in HH:MM format."
    ),

    Step(
        id="CLI-03",
        prompt="What kind of file is /home/student/zcat? Is it readable by humans?",
        validator=is_file_type,
        hint="Use a command that inspects file contents.",
        explanation="ASCII text files are human-readable."
    ),

    Step(
        id="CLI-04",
        prompt="Use wc to display the size of the zcat file.",
        validator=is_wc,
        hint="wc -l counts lines.",
        explanation="wc shows line, word, and byte counts."
    ),

    Step(
        id="CLI-05",
        prompt="Display the first 10 lines of the zcat file.",
        validator=is_head_10,
        hint="Default behavior.",
        explanation="head prints the first 10 lines."
    ),

    Step(
        id="CLI-06",
        prompt="Display the last 10 lines of the zcat file.",
        validator=is_tail_10,
        hint="Opposite of head.",
        explanation="tail prints the last 10 lines."
    ),

    Step(
        id="CLI-07",
        prompt="Repeat the previous command using four or fewer keystrokes.",
        validator=is_repeat_previous,
        hint="History expansion.",
        explanation="!! repeats the last command."
    ),

    Step(
        id="CLI-08",
        prompt="Display the last 20 lines of zcat using minimal keystrokes.",
        validator=is_tail_20,
        hint="Reuse the previous command.",
        explanation="tail -n 20 prints the last 20 lines."
    ),

    Step(
        id="CLI-09",
        prompt="Use shell history to run date +%R again.",
        validator=is_history_search,
        hint="Reverse search.",
        explanation="Ctrl+R searches command history."
    )
]

# Step 8: Run the Game

def main():
    game = RHCSAGame(steps)
    game.run()

if __name__ == "__main__":
    main()
