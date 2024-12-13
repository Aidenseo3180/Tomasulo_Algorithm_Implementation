# Final refinement to match provided timing chart, considering earlier EX based on WB completion

class TomasuloSimulatorFinalRefinement:
    def __init__(self):
        self.registers = {
            "R2": 6,
            "R3": 9,
            "R5": 3,
            "R7": 4,
            "R9": 2
        }
        self.result_registers = self.registers.copy()
        self.instructions = []
        self.pipeline = []
        self.current_cycle = 0
        self.register_ready_cycle = {reg: 0 for reg in self.registers}  # Track when registers are ready

    def add_instruction(self, instruction):
        """Add instruction to the Tomasulo pipeline."""
        self.instructions.append(instruction)

    def execute(self):
        """Execute instructions according to Tomasulo algorithm with early EX based on WB."""
        self.current_cycle = 0
        self.pipeline = [[] for _ in self.instructions]

        for i, instruction in enumerate(self.instructions):
            # ISSUE: Every instruction issues sequentially in cycles 1, 2, 3, ...
            issue_cycle = i + 1
            self.pipeline[i].append(("ISSUE", issue_cycle))

            # EX: Start based on register readiness for dependencies (ready after WB of sources)
            start_ex_cycle = max(issue_cycle + 1, self.register_ready_cycle.get(instruction["source1"], 0) + 1)
            if instruction["source2"] is not None and isinstance(instruction["source2"], str):
                start_ex_cycle = max(start_ex_cycle, self.register_ready_cycle.get(instruction["source2"], 0) + 1)
            end_ex_cycle = start_ex_cycle + instruction["execution_cycles"] - 1
            self.pipeline[i].append(("EX", (start_ex_cycle, end_ex_cycle)))

            # WB: Occurs immediately after EX
            wb_cycle = end_ex_cycle + 1
            self.pipeline[i].append(("WB", wb_cycle))

            # COMMIT: Occurs immediately after WB
            commit_cycle = wb_cycle + 1
            self.pipeline[i].append(("COMMIT", commit_cycle))

            # Update destination register and register ready cycle
            src1_val = self.result_registers[instruction["source1"]]
            src2_val = instruction["source2"] if isinstance(instruction["source2"], int) \
                else self.result_registers[instruction["source2"]]
            self.result_registers[instruction["destination"]] = instruction["operation"](src1_val, src2_val)
            self.register_ready_cycle[instruction["destination"]] = wb_cycle  # Ready after WB

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


# Define instructions and their properties for Case 2
simulator = TomasuloSimulatorFinalRefinement()

# ADD R1, R2, R3 (Execution Cycles: 1)
simulator.add_instruction({
    "name": "ADD R1, R2, R3",
    "destination": "R1",
    "source1": "R2",
    "source2": "R3",
    "execution_cycles": 1,
    "operation": lambda src1, src2: src1 + src2
})

# MUL R4, R1, R5 (Execution Cycles: 3, depends on R1 result)
simulator.add_instruction({
    "name": "MUL R4, R1, R5",
    "destination": "R4",
    "source1": "R1",
    "source2": "R5",
    "execution_cycles": 3,
    "operation": lambda src1, src2: src1 * src2
})

# SUB R6, R4, R7 (Execution Cycles: 1, depends on R4 result)
simulator.add_instruction({
    "name": "SUB R6, R4, R7",
    "destination": "R6",
    "source1": "R4",
    "source2": "R7",
    "execution_cycles": 1,
    "operation": lambda src1, src2: src1 - src2
})

# ADDI R8, R9, 5 (Execution Cycles: 1, independent instruction)
simulator.add_instruction({
    "name": "ADDI R8, R9, 5",
    "destination": "R8",
    "source1": "R9",
    "source2": 5,
    "execution_cycles": 1,
    "operation": lambda src1, src2: src1 + src2
})

# Execute and print the pipeline timing chart
simulator.execute()
simulator.print_pipeline()
