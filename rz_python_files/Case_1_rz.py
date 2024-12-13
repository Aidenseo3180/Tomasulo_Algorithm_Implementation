# Adjusting the simulator to match the specific timing chart

class TomasuloSimulatorCase1Adjusted:
    def __init__(self):
        self.registers = {
            "R2": 5,
            "R3": 10,
            "R5": 8,
            "R6": 3,
            "R8": 2,
            "R10": 4
        }
        self.result_registers = self.registers.copy()
        self.instructions = []
        self.pipeline = []
        self.current_cycle = 0

    def add_instruction(self, instruction):
        """Add instruction to be executed."""
        self.instructions.append(instruction)

    def execute(self):
        """Execute the instructions to match the provided timing chart."""
        self.current_cycle = 0
        self.pipeline = [[] for _ in self.instructions]

        for i, instruction in enumerate(self.instructions):
            # ISSUE: Align ISSUE cycles based on sequence
            issue_cycle = i + 1
            self.pipeline[i].append(("ISSUE", issue_cycle))
            self.current_cycle = issue_cycle

            # EX: Start immediately after ISSUE, handle specific EX duration
            start_ex_cycle = self.current_cycle + 1
            end_ex_cycle = start_ex_cycle + instruction["execution_cycles"] - 1
            self.pipeline[i].append(("EX", (start_ex_cycle, end_ex_cycle)))
            self.current_cycle = end_ex_cycle

            # WB: Occurs right after EX
            wb_cycle = self.current_cycle + 1
            self.pipeline[i].append(("WB", wb_cycle))
            self.current_cycle = wb_cycle

            # COMMIT: Occurs right after WB
            commit_cycle = self.current_cycle + 1
            self.pipeline[i].append(("COMMIT", commit_cycle))
            self.current_cycle = commit_cycle

            # Update register values at COMMIT
            operands = instruction["operands"]
            src1 = self.result_registers[operands[0]]
            src2 = operands[1] if isinstance(operands[1], int) else self.result_registers[operands[1]]
            self.result_registers[instruction["destination"]] = instruction["operation"](src1, src2)

    def print_pipeline(self):
        """Display the pipeline timing chart."""
        print("Instruction | ISSUE | EX       | WB  | COMMIT")
        for i, stages in enumerate(self.pipeline):
            ex_stage = f"{stages[1][1][0]}-{stages[1][1][1]}"
            print(
                f"{self.instructions[i]['name']} | {stages[0][1]}    | {ex_stage} | {stages[2][1]}  | {stages[3][1]}"
            )
        print("\nFinal Register Values:")
        for reg, value in self.result_registers.items():
            print(f"{reg} = {value}")


# Define instruction set and execution cycles for Case 1 based on the provided chart
simulator = TomasuloSimulatorCase1Adjusted()

# ADD R1, R2, R3 (Execution Cycles: 1)
simulator.add_instruction({
    "name": "ADD R1, R2, R3",
    "destination": "R1",
    "execution_cycles": 1,
    "operation": lambda src1, src2: src1 + src2,
    "operands": ["R2", "R3"]
})

# SUB R4, R5, R6 (Execution Cycles: 1)
simulator.add_instruction({
    "name": "SUB R4, R5, R6",
    "destination": "R4",
    "execution_cycles": 1,
    "operation": lambda src1, src2: src1 - src2,
    "operands": ["R5", "R6"]
})

# ADDI R7, R8, 10 (Execution Cycles: 1)
simulator.add_instruction({
    "name": "ADDI R7, R8, 10",
    "destination": "R7",
    "execution_cycles": 1,
    "operation": lambda src1, src2: src1 + src2,
    "operands": ["R8", 10]
})

# MUL R9, R1, R10 (Execution Cycles: 3)
simulator.add_instruction({
    "name": "MUL R9, R1, R10",
    "destination": "R9",
    "execution_cycles": 3,
    "operation": lambda src1, src2: src1 * src2,
    "operands": ["R1", "R10"]
})

# Execute and display results
simulator.execute()
simulator.print_pipeline()
