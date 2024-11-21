
class ProcessControlBlock:
    """
    Tracks the progress of the individual instruction
    """
    def __init__(self, instruction):

        self._opcode = instruction[0]
        self._operand_1 = instruction[1]
        self._operand_2 = instruction[2]
        self._operand_3 = instruction[3]

        self._current_stage = 'None'   # initial stage of instruction in pipeline
        self._is_stall = False         # indicator flag to indicate whether the instruction is in stall

        # Keeps a track of how many cycles instruction spent on each stage
        # Each stage stores (from, to) # of cycles
        self._stage_cycle_counter = {
            "ISSUE": (),
            "EX": (),
            "MEM": (),
            "WB": (),
            "COMMIT": () 
        }

        # Dependency checker
        self._is_dependent = False

        # flag to note whether the instruction has been already executed (since we do not want to execute same instruction more than once)
        self._is_executed = False

        # flag to notify when to move to the next stage
        self._move_to_next_stage = False
        self._cycle_counter = 0     # this tracks the # of cycles instruction spent from each cycle -> if certain #, then move to next stage

    def get_cycle_counter(self):
        return self._cycle_counter
    
    def increment_cycle_counter(self):
        self._cycle_counter += 1

    def reset_cycle_counter(self):
        self._cycle_counter = 0

    def get_opcode(self):
        return self._opcode
    
    def get_operand_1(self):
        return self._operand_1
    
    def get_operand_2(self):
        return self._operand_2
    
    def get_operand_3(self):
        return self._operand_3

    def get_stage(self):
        return self._current_stage
    
    def get_is_executed(self):
        return self._is_executed
    
    def set_is_executed(self):
        self._is_executed = True

    def get_move_to_next_stage(self):
        return self._move_to_next_stage
    
    def set_move_to_next_stage(self):
        self._move_to_next_stage = True

    def reset_move_to_next_stage(self):
        self._move_to_next_stage = False
    
    def update_stage(self, stage_name):
        self._current_stage = stage_name

    def update_stage_cycle_counter(self, stage_name, from_cycle, to_cycle):
        self._stage_cycle_counter[stage_name] = (from_cycle, to_cycle)

class ReservationStation:
    """
    Reservation station that temporary holds the instruction
    """
    def __init__(self, capacity: int):
        self._capacity = capacity
        self._is_full = False

    def store_inst(self):
        if self._capacity != 0:
            self._capacity -= 1
            return True  # successful store
        
        return False

# TODO: I'll do this later
class Memory:
    """
    Class designed to mimick memory aspect (Addresses and Values)
    """
    def __init__(self):

        self._addresses = []
        self._values = []
        pass

# OS
class OperatingSystem:
    """
    Class dedicated to conduct Tomasulo's Algorithm.
    Assume there's only 1 adder, 1 floating-point adder
    """
    def __init__(self, inst_buffer: list, rc: int = 4, frc: int = 4, lrc: int = 4, strc: int = 4):
        """
        Args:
            inst_buffer (list): list of instructions
            rc (int): adder reservation station capacity
            frc (int): floating-point adder reservation capacity
            lrc (int): load reservation station capacity
            strc (int): store reservation station capacity
        """
        self._inst_buffer = inst_buffer     # store all the given instructions

        # TODO: do this later
        self._RAT = []      # RAT (source mapping)
        self._ARF = []      # Architecture Reg File

        self._active_instructions = []  # Keeps the ACTIVE inst

        # Register (w/ initial values)
        self._register = {
            "R1": 0,
            "R2": 0,
            "R3": 0,
            "R4": 0,
            "R5": 0,
            "R6": 0,
            "R7": 0,
            "R8": 0,
            "R9": 0,
            "R10": 0
        }

        # Reservation stations
        self._adder_reserv_st = ReservationStation(rc)
        self._fp_adder_reserv_st = ReservationStation(frc)
        self._load_reserv_st = ReservationStation(lrc)
        self._store_reserv_st = ReservationStation(strc)

        self._cycle = 0          # keep a track of cycles

        if self._inst_buffer.empty():
            print("----- No instruction given to run, terminated -----")
            return

        self.run_pipeline()

    def find_free_reservation(self, inst):
        """
        Find if the corresponding instruction can be placed inside the reservation station
        """

        inst_type = inst.get_opcode()
        is_successful = False

        if inst_type is "ADD" or inst_type is "ADDI" or inst_type is "SUB":     # For adder reservation station
            is_successful = self._adder_reserv_st.store_inst(inst)
        
        if inst_type is "MULT" or inst_type is "DIVD":                          # For floating-point reservation station
            is_successful = self._fp_adder_reserv_st.store_inst(inst)

        if inst_type is "LDR":
            is_successful = self._load_reserv_st.store_inst(inst)

        if inst_type is "STR":
            is_successful = self._store_reserv_st.store_inst(inst)

        return is_successful

    def perform_operation(self, inst: ProcessControlBlock):
        # Depends on the opcode, run different stages
        op = inst.get_opcode()
        operand_1 = inst.get_operand_1()
        operand_2 = inst.get_operand_2()
        operand_3 = inst.get_operand_3()

        current_stage = inst.get_stage()

        is_executed = inst.get_is_executed()

        # ---------- 3. Read operands that are in registers ----------------
        # TODO: If not in register, find which reservation station will product it
        match(op):
            case 'ADD':
                if current_stage == "EX":
                    if is_executed == False:
                        # TODO: Update so that the result gets written in reservation station -> and during WB stage, write to Register
                        self._register[operand_1] = self._register[operand_2] + self._register[operand_3]
                        inst.set_is_executed()          # set the executed flag to True
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB, COMMIT
            case 'ADDI':
                if current_stage == "EX":
                    if is_executed == False:
                        self._register[operand_1] = self._register[operand_2] + operand_3
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB, COMMIT each
            case 'SUB':
                if current_stage == "EX":
                    if is_executed == False:
                        self._register[operand_1] = self._register[operand_2] - self._register[operand_3]
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB, COMMIT each
            case 'MULT':
                if current_stage == "EX":
                    if is_executed == False:
                        self._register[operand_1] = self._register[operand_2] * self._register[operand_3]
                        inst.set_is_executed()
                    else:
                        if inst.get_cycle_counter < 2:
                            inst.increment_cycle_counter()
                        else:
                            inst.set_move_to_next_stage()  # takes 2 cycles in EX
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB, COMMIT each
                    
            case 'DIVD':
                if current_stage == "EX":
                    if is_executed == False:
                        self._register[operand_1] = self._register[operand_2] / self._register[operand_3]
                        inst.set_is_executed()
                    else:
                        if inst.get_cycle_counter < 2:
                            inst.increment_cycle_counter()
                        else:
                            inst.set_move_to_next_stage()  # takes 2 cycles in EX
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB, COMMIT each

            case 'LDR':
                # TODO: implement LDR (LOAD)
                pass
            case 'STR':
                # TODO: implement STR (STORE)
                pass
            case _:
                print("--- WARNING: Opcode Not supported, thus ignored ---")

    def run_pipeline(self):
        """
        Run Tomasulo's Algorithm
        Run each instruction in inst_in_pipeline, progress their stages.
        Keep a track of cycle
        """              

        def update_inst_stage(inst: ProcessControlBlock):
            
            move_to_next = inst.get_move_to_next_stage()
            if move_to_next == False:   # if can't move to next stage, don't
                return

            curr_stage = inst.get_stage()
            opcode = inst.get_opcode()

            # keep a track of how many cycles spent in each stage before move to the next stage
            cycle_spent = inst.get_cycle_counter()
            inst.update_stage_cycle_counter(curr_stage, self._cycle, self._cycle + cycle_spent)

            match(curr_stage):
                case "ISSUE":
                    inst.update_stage("EX")
                case "EX":
                    # Only LOAD and STORE use MEM
                    if opcode == "LDR" or opcode == "STR":
                        inst.update_stage("MEM")
                    else:
                        inst.update_stage("WB")
                case "MEM":
                    inst.update_stage("WB")
                case "WB":
                    inst.update_stage("COMMIT")
                case "COMMIT":
                    inst.update_stage("DONE")   # NOTE: When instruction reaches 'DONE', that's when it leaves the active instruction list

            # reset the flag and counter (bc we just used the counter to track # of cycles spent in each stage)
            inst.reset_move_to_next_stage()
            inst.reset_cycle_counter()

        # ---------- 1. Get next instruction from instruction buffer ------------
        # Repeatedly run until the instruction buffer is empty
        while(not self._inst_buffer.empty()):

            self._cycle += 1
            inst = ProcessControlBlock(self._inst_buffer[0])

            # --------- 2. Find a free reservation for it ----------
            # if not free, stall until one is
            # NOTE: instruction CANNOT be issued when the corresponding reservation station is full
            is_successful = self.find_free_reservation(inst)

            # if there's a space in reservation -> remove inst from buffer & add to queue
            # otherwise, stall (keep it in _inst_buffer)
            if is_successful is True:
                inst.update_stage_cycle_counter("ISSUE", self._cycle, self._cycle)
                self._active_instructions.append(inst)  # Add to the active instruction queue (with instruction tracker)
                del self._inst_buffer[0]

            # iterate through the ACTIVE instructions to progress
            for inst in self._active_instructions:
                self.perform_operation(inst)
                update_inst_stage(inst)                

            # TODO: ------ 4. Rename registers ( do this later) ------


            # TODO: ------ 5. Reservation stations are now physical registers ------

    def print_stat(self):
        """
        Print the status of the internals
        """


        print("---------- Overview of Internal Structure ---------")

        # Reservation Status


        # Instruction Status (in pipeline form)


        # Register result status


        # Memory Status (of every cycle)

 

        print("-------------------")

def parse_instructions(file_path):
    instructions = []

    with open(file_path, 'r') as file:
        for line in file:
            # Remove leading/trailing whitespaces and skip empty lines
            line = line.strip()
            if not line:
                continue

            # Split the instruction into operation and operands
            parts = line.split()
            operation = parts[0]  # First part is the operation
            operands = parts[1].split(',')  # Split operands by ','

            # Extract individual components
            if len(operands) == 3:  # For instructions like ADD, SUB, MUL
                op1, op2, op3 = operands
                instructions.append((operation, op1.strip(), op2.strip(), op3.strip()))
            elif len(operands) == 2:  # For instructions like ADDI
                op1, op2 = operands
                instructions.append((operation, op1.strip(), op2.strip()))
    
    return instructions

def main():

    # This is the test case we want to run
    file_path = 'test_case_1.txt'
    parsed_instructions = parse_instructions(file_path=file_path)

    # Initialization
    tm = OperatingSystem(
        inst_buffer=parsed_instructions, 
        rc=4,
        frc=4,
    )

if __name__ == '__main__':
    main()
