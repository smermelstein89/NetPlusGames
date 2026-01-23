class RHCSAGame:
    def __init__(self, steps):
        self.steps = steps
        self.current_step = 0

    def run(self):
        print("\n🟥 RHCSA PRACTICE GAME 🟥\n")

        while self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.run_step(step)
            self.current_step += 1

        print("\n✅ All steps completed. Nice work.\n")

    def run_step(self, step):
        print(f"\nSTEP {self.current_step + 1}: {step.id}")
        print("-" * 50)
        print(step.prompt)

        while True:
            user_input = input("\nYour answer> ").strip()

            if user_input.lower() == "hint" and step.hint:
                print(f"💡 Hint: {step.hint}")
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
