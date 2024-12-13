class TomasuloSimulator:
    def __init__(self):
        # Initialize components: registers, memory, and instruction queue
        self.registers = {"R0": 8, "R2": 20, "R3": 0, "R4": 0, "R6": 5, "R7": 2, "R8": 3}
        self.memory = {8: 20, 12: 0}
        self.timing_chart = []  # To store instruction timings
        self.current_cycle = 0
        self.last_wb_cycle = {}  # Track when registers are written back

    def run(self, instructions):
        overlapping_issue_cycle = 1  # Start with the first cycle for issuing instructions
        for instr in instructions:
            # Calculate ISSUE cycle
            issue_cycle = overlapping_issue_cycle

            # Calculate EX start cycle based on dependencies
            if instr["type"] == "ALU":
                dep1_ready = self.last_wb_cycle.get(instr["src1"], 0)
                dep2_ready = self.last_wb_cycle.get(instr["src2"], 0)
                ex_start = max(issue_cycle + 1, dep1_ready + 1, dep2_ready + 1)
            elif instr["type"] == "LD":
                ex_start = issue_cycle + 1
            elif instr["type"] == "ST":
                # ST depends on its source operand and waits for the producer to finish WB
                dep_ready = self.last_wb_cycle.get(instr["src"], 0)
                ex_start = max(issue_cycle + 1, dep_ready + 1)

            # Calculate other stages
            ex_end = ex_start + (instr["duration"] - 1)
            mem_cycle = ex_end + 1 if instr["type"] == "LD" else "-"
            wb_cycle = mem_cycle + 1 if mem_cycle != "-" else ex_end + 1 if instr["type"] != "ST" else "-"
            commit_cycle = wb_cycle + 1 if wb_cycle != "-" else ex_end + 1

            # Update last WB cycle for registers written by this instruction
            if "dest" in instr:
                self.last_wb_cycle[instr["dest"]] = wb_cycle

            # Record the instruction's timing
            self.timing_chart.append({
                "Instruction": instr["name"],
                "ISSUE": issue_cycle,
                "EX": f"{ex_start}-{ex_end}" if ex_start != ex_end else ex_start,
                "MEM": mem_cycle,
                "WB": wb_cycle,
                "COMMIT": commit_cycle
            })

            # Update the current cycle for dependency
            self.current_cycle = max(commit_cycle, self.current_cycle)
            overlapping_issue_cycle += 1  # Overlap issue cycles

            # Simulate instruction execution (optional, for correctness check)
            if instr["type"] == "ST":
                self.memory[instr["address"]] = self.registers[instr["src"]]
            elif instr["type"] == "LD":
                self.registers[instr["dest"]] = self.memory[instr["address"]]
            elif instr["type"] == "ALU":
                src1 = self.registers[instr["src1"]]
                src2 = self.registers[instr["src2"]]
                self.registers[instr["dest"]] = instr["op"](src1, src2)

    def print_results(self):
        print("\nInstruction Timing Chart:")
        print(f"{'Instruction':<15} {'ISSUE':<5} {'EX':<10} {'MEM':<5} {'WB':<5} {'COMMIT':<5}")
        for entry in self.timing_chart:
            print(f"{entry['Instruction']:<15} {entry['ISSUE']:<5} {entry['EX']:<10} {entry['MEM']:<5} {entry['WB']:<5} {entry['COMMIT']:<5}")

        print("\nFinal Register Values:")
        for reg, value in self.registers.items():
            print(f"{reg}: {value}")

        print("\nFinal Memory Values:")
        for addr, value in self.memory.items():
            print(f"MEM[{addr}]: {value}")


# Define the test case instructions
instructions = [
    {"name": "ST R2, 0(R0)", "type": "ST", "src": "R2", "address": 8, "duration": 1},
    {"name": "LD R3, 0(R0)", "type": "LD", "dest": "R3", "address": 8, "duration": 1},
    {"name": "MUL R4, R3, R7", "type": "ALU", "op": lambda x, y: x * y, "src1": "R3", "src2": "R7", "dest": "R4", "duration": 20},
    {"name": "ADD R8, R4, R6", "type": "ALU", "op": lambda x, y: x + y, "src1": "R4", "src2": "R6", "dest": "R8", "duration": 2},
    {"name": "SUB R3, R8, R7", "type": "ALU", "op": lambda x, y: x - y, "src1": "R8", "src2": "R7", "dest": "R3", "duration": 3},
    {"name": "ST R8, 4(R0)", "type": "ST", "src": "R8", "address": 12, "duration": 1},
]

# Create simulator and run the instructions
simulator = TomasuloSimulator()
simulator.run(instructions)
simulator.print_results()
