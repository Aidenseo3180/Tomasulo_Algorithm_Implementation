import pprint

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

        # flag to note whether the instruction has been already executed (since we do not want to execute same instruction more than once)
        self._is_executed = False

        # flag to notify when to move to the next stage
        self._move_to_next_stage = False
        self._cycle_counter = 0     # this tracks the # of cycles instruction spent from each cycle -> if certain #, then move to next stage

        self._reserv_idx = None


    def set_reserv_idx(self, idx):
        self._reserv_idx = idx

    def get_reserv_idx(self):
        return self._reserv_idx

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
        self.update_stage(stage_name)
        self._stage_cycle_counter[stage_name] = (from_cycle, to_cycle)

    def get_stage_cycle_counter(self):
        return self._stage_cycle_counter

class ReservationStation:
    """
    Reservation station that temporary holds the instruction
    """
    def __init__(self, capacity: int):
        self._capacity = capacity
        self._is_full = False

        self._reserv_station = [None] * capacity

    def store_inst(self, inst: ProcessControlBlock):
        """
        Save the instruction to the reservation station entry
        """

        # First, find the empty entry
        for idx, entry in enumerate(self._reserv_station):
            if entry == None:
                inst.set_reserv_idx(idx)
                return True # successful store
        
        return False
    
    def store_result(self, idx, res):
        self._reserv_station[idx] = res

    def get_reserv_content(self, idx):
        return self._reserv_station[idx]

    def clear_reserv_content(self, idx):
        """
        Empty the corresponding idx(instruction)'s reservation station content, and increment the capacity
        """
        self._reserv_station[idx] = None

    def print_reserv_station_content(self):
        print(self._reserv_station)


# TODO: do this later
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
    def __init__(self, config_data):
        """
        Args:
            config_data: contains the configuration
        """

        self._config_data = config_data

        # --------------- Read config data -----------------
        # read in instructions
        self._inst_buffer = self.parse_instructions(self._config_data['instructions'])
        if len(self._inst_buffer) == 0:
            print("----- No instruction given to run, terminated -----")
            return

        # Read initial register config
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
        for reg, val in self._config_data['registers'].items():
            if reg in self._register:
                self._register[reg] = val

        # TODO: Also make floating point registers (F1, F2, etc.). Above are R1, R2, etc.


        # TODO: do this later
        self._RAT = []      # RAT (source mapping)
        self._ARF = []      # Architecture Reg File

        self._active_instructions = []  # Keeps the ACTIVE inst

        # Reservation stations
        self._adder_reserv_st = ReservationStation(config_data["fu_details"]['integer_adder']['rs'])
        self._fp_adder_reserv_st = ReservationStation(config_data["fu_details"]['fp_adder']['rs'])
        self._fp_mult_reserv_st = ReservationStation(config_data["fu_details"]['fp_multiplier']['rs'])
        self._load_store_reserv_st = ReservationStation(config_data["fu_details"]['load_store_unit']['rs'])

        self._cycle = 0          # keep a track of cycles

        # List that keeps a track of dependent register
        self._dependency_list = []
        self._is_dependent = False  # dependency flag
        
        self.run_pipeline()


    def find_free_reservation(self, inst):
        """
        Find if the corresponding instruction can be placed inside the reservation station
        """

        inst_type = inst.get_opcode()
        is_successful = False
        
        if inst_type == "ADD" or inst_type == "ADDI" or inst_type == "SUB":     # For adder reservation station
            is_successful = self._adder_reserv_st.store_inst(inst)
        
        if inst_type == "MUL" or inst_type == "DIVD":                          # For floating-point reservation station
            is_successful = self._fp_adder_reserv_st.store_inst(inst)

        if inst_type == "LDR":
            is_successful = self._load_store_reserv_st.store_inst(inst)

        if inst_type == "STR":
            is_successful = self._load_store_reserv_st.store_inst(inst)

        return is_successful
    

    def check_dependency(self, operand_2="", operand_3=""):
        # ----- If there's a dependency -> return True ------
        if operand_2 in self._dependency_list or operand_3 in self._dependency_list:
            return True # indicate dependency exist
        
        return False    # no dependency


    def remove_from_dependency_list(self, register_name):
        if register_name in self._dependency_list:
            self._dependency_list.remove(register_name)


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
        # Currently, we have to wait until WB stage to write to the register -> make it so that we check reservation station first!

        # NOTE: Find the idx of instruction's reservation station
        inst_reserv_idx = inst.get_reserv_idx()
        match(op):
            case 'ADD':
                if current_stage == "EX":
                    if is_executed == False:
                        # ---- First save the executed result to reservation station -> during WB, write to register -----
                        res = self._register[operand_2] + self._register[operand_3]
                        self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()          # set the executed flag to True
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx)   # write the result to register now

                    # Clear the reservation station entry
                    self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # remove register from dependency list -> allow other instructions w/ dependencies to run
                    self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            case 'ADDI':
                if current_stage == "EX":
                    if is_executed == False:
                        res = self._register[operand_2] + int(operand_3)
                        self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now

                    self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            case 'SUB':
                if current_stage == "EX":
                    if is_executed == False:
                        res = self._register[operand_2] - self._register[operand_3]
                        self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now

                    self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT

            case 'MUL':
                if current_stage == "EX":
                    if is_executed == False:
                        res = self._register[operand_2] * self._register[operand_3]
                        self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.increment_cycle_counter() # +1 to its own counter (spent 1 cycle)
                    else:
                        if inst.get_cycle_counter() < 2:
                            inst.increment_cycle_counter()
                        else:
                            inst.set_move_to_next_stage()  # takes 2 cycles in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    self._register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now

                    self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT

            case 'DIVD':
                if current_stage == "EX":
                    if is_executed == False:
                        res = self._register[operand_2] / self._register[operand_3]
                        self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                    else:
                        if inst.get_cycle_counter() < 2:
                            inst.increment_cycle_counter()
                        else:
                            inst.set_move_to_next_stage()  # takes 2 cycles in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    self._register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now

                    self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT

            case 'LDR':
                # TODO: implement LDR (LOAD)
                pass
            case 'STR':
                # TODO: implement STR (STORE)
                pass
            case _:
                print("--- WARNING: Opcode Not supported, thus ignored ---")
                raise Exception("Given Opcode Not Supported")


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
            
            # --------- Check for dependency before entering EX stage --------------
            is_dependent = self.check_dependency(inst.get_operand_2(), inst.get_operand_2())
            if is_dependent == True:
                return

            curr_stage = inst.get_stage()
            opcode = inst.get_opcode()

            # keep a track of how many cycles spent in each stage before move to the next stage
            cycle_spent = inst.get_cycle_counter()
            inst.update_stage_cycle_counter(curr_stage, self._cycle - cycle_spent, self._cycle)

            # ----- Check current stage, update the corresponding stage accordingly -----
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
        running_inst = 0
        while(len(self._inst_buffer) != 0 or running_inst > 0):

            self._cycle += 1

            # print(f"current cycle: {self._cycle}")

            # First, check buffer to see if there's any instructions that need to be fetched
            if len(self._inst_buffer) != 0:
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
                    running_inst += 1

                    # Add to Dependency List
                    if inst.get_operand_1() not in self._dependency_list:
                        self._dependency_list.append(inst.get_operand_1())

            # ----- iterate through the ACTIVE instructions to progress -----
            for inst in self._active_instructions:
                if inst.get_stage() != "DONE":
                    if inst.get_stage() != "Terminated":
                        # ----- Run each operation in pipeline -----
                        self.perform_operation(inst)
                        # ----- Check if we can move to next stage (if move_next_stage flag is True) -----
                        update_inst_stage(inst)
                else:
                    running_inst -= 1
                    # Set stage to TERMINATED b/c if stay in DONE, this else statement gets called for instructions in DONE stage iteratively
                    inst.update_stage("Terminated")


            # TODO: ------ 4. Rename registers ( do this later) ------


            # TODO: ------ 5. Reservation stations are now physical registers ------

        self.print_stat()
                

    def print_stat(self):
        """
        Print the status of the internals
        """

        print("\n**********************************")
        print("*                                *")
        print("* Overview of Internal Structure *")
        print("*                                *")
        print("**********************************\n")

        # Reservation Status
        print("********************************")
        print("* Reservation Statation Status *")
        print("********************************\n")

        print("        Adder Reservation Station: ")
        print("-----------------------------------------")
        self._adder_reserv_st.print_reserv_station_content()
        print("\nFloating-Point Adder Reservation Station:")
        print("-----------------------------------------")
        self._fp_adder_reserv_st.print_reserv_station_content()
        print("\nFloating-Point Mult Reservation Station:")
        print("-----------------------------------------")
        self._fp_mult_reserv_st.print_reserv_station_content()
        print("\n    Load Store Reservation Station: ")
        print("-----------------------------------------")
        self._load_store_reserv_st.print_reserv_station_content()

        # Instruction Status (in pipeline form)
        print("\n*******************************")
        print("* Instruction Pipeline Status *")
        print("*******************************\n")

        for inst in self._active_instructions:
            print(f"{inst.get_opcode()} {inst.get_operand_1()} {inst.get_operand_2()} {inst.get_operand_3()} | ", end='')
            for key, value in inst.get_stage_cycle_counter().items():
                if key != "Terminated":
                    print(f"{key}:{value} ", end='')
            print("\n")

        # Register result status
        print("\n***************************")
        print("* Register Content Status *")
        print("***************************\n")
        for key, value in self._register.items():
            print(f"{key}: {value}")

        # TODO: Memory Status (of every cycle)
        # Print memory addresses

        print(f"\n\nTotal number of cycles: {self._cycle}\n")
 
        print("\n**********************************\n")

    def parse_instructions(self, instructions_list):
        instructions = []

        for line in instructions_list:
            if line == "":
                continue 

            parts = line.split()
            operation = parts[0]  # First part is the operation
            operands = parts[1].split(',')  # Split operands by ','

            # Extract individual components
            if len(operands) == 3:  # For instructions like ADD, SUB, MUL
                op1, op2, op3 = operands
                instructions.append((operation, op1.strip(), op2.strip(), op3.strip()))
            elif len(operands) == 2:  # For instructions like LOAD, STORE
                op1, op2 = operands
                instructions.append((operation, op1.strip(), op2.strip()))
        
        return instructions

def parse_configuration(file_path):
    """
    Reads a configuration file in a fixed format and parses the data into variables.
    
    Args:
        file_path (str): Path to the configuration file.
    
    Returns:
        dict: A dictionary containing the parsed configuration details.
    """
    config = {}
    
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Parse the Functional Unit (FU) details
    config["fu_details"] = {
        "integer_adder": {
            "rs": int(lines[1].split()[2].strip()), # reservation station
            "cycles_in_ex": int(lines[1].split()[3].strip()),
            "cycles_in_mem": None,
            "f_units": int(lines[1].split()[4].strip())
        },
        "fp_adder": {
            "rs": int(lines[2].split()[2].strip()),
            "cycles_in_ex": int(lines[2].split()[3].strip()),
            "cycles_in_mem": None,
            "f_units": int(lines[2].split()[4].strip())
        },
        "fp_multiplier": {
            "rs": int(lines[3].split()[2].strip()),
            "cycles_in_ex": int(lines[3].split()[3].strip()),
            "cycles_in_mem": None,
            "f_units": int(lines[3].split()[4].strip())
        },
        "load_store_unit": {
            "rs": int(lines[4].split()[2].strip()),
            "cycles_in_ex": int(lines[4].split()[3].strip()),
            "cycles_in_mem": int(lines[4].split()[4].strip()),
            "f_units": int(lines[4].split()[5].strip())
        }
    }

    # Parse ROB and CDB buffer entries
    config["rob_entries"] = int(lines[6].split()[1].strip())
    config["cdb_buffer_entries"] = int(lines[7].split()[1].strip())

    # Parse register values
    config["registers"] = {
        "R2": int(lines[9].split()[1].strip()),
        "R3": int(lines[10].split()[1].strip()),
        "R5": int(lines[11].split()[1].strip()),
        "R7": int(lines[12].split()[1].strip()),
        "R9": int(lines[13].split()[1].strip())
    }

    # Parse instructions
    config["instructions"] = []
    for i in range(15, len(lines)):  # Starting from line 15 where instructions begin
        config["instructions"].append(lines[i].strip())
    
    return config


def main():

    # ********************************************
    # * Choose the testcase we would like to run *
    # ********************************************

    file_to_run = "test_case_1.txt"

    print("\n**********************************")
    print("*         Initial Setup          *")
    print("**********************************\n")
    config_data = parse_configuration(file_to_run)
    # Access parsed data
    print("Functional Units: ")
    pprint.pprint(config_data["fu_details"])
    print("ROB Entries: ", end='')
    pprint.pprint(config_data["rob_entries"])
    print("CDB Buffer Entries: ", end='')
    pprint.pprint(config_data["cdb_buffer_entries"])
    print("Registers: ", config_data["registers"])
    print("Instructions: ", config_data["instructions"])

    # # -------------- Actual Run ---------------

    OperatingSystem(
        config_data=config_data
    )

if __name__ == '__main__':
    main()
