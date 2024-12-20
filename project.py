import re
import os
import pprint


class ProcessControlBlock:
    """
    Tracks the progress of the individual instruction
    """
    def __init__(self, instruction):
        self._opcode = instruction[0]
        self._operand_1 = instruction[1]
        self._operand_2 = instruction[2]
        if len(instruction) == 4:
            self._operand_3 = instruction[3]
        else:
            self._operand_3 = []

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

        self._SD_helper = 0     # For SD inst, saves the corresponding ROB entry index

        # Flag to determine whether it uses F registers
        self._is_fp = False

        # Determine if it's FP during initialization
        if "F" in self._operand_1 or "F" in self._operand_2 or "F" in self._operand_3:
            self._is_fp = True

    def set_SD_helper(self, idx):
        self._SD_helper = idx

    def get_SD_helpr(self):
        return self._SD_helper

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
    
    def get_is_fp(self):
        return self._is_fp
    
class ReservationStation:
    """
    Reservation station that temporary holds the instruction
    """
    def __init__(self, f, capacity: int):
        self.f = f
        self._capacity = capacity
        self._is_full = False

        self._reserv_station = [None] * capacity

    def store_inst(self, inst: ProcessControlBlock):
        """
        Save the instruction to the reservation station entry
        """

        # First, find the empty entry
        for idx, entry in enumerate(self._reserv_station):
            if entry is None:
                self.store_result(idx, "Reserved")
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
        print(self._reserv_station, file=self.f)


class Memory:
    """
    Class designed to mimick memory aspect (Addresses and Values)
    """
    def __init__(self):

        # 256B (64W)
        self._values = [0] * 64 # 256 / 4 = 64 Word. Ex. _values[0] will correspond to value of memory address 0-4.

    def load_value(self, addr):
        return self._values[addr]

    def store_value(self, addr, value):
        self._values[addr] = value
    
class ReorderBuffer:
    """
    Class for ROB
    """
    def __init__(self):
        self._inst = ""
        self._finish_bit = False
        self._val = None

    def set_entry(self, inst):
        self._inst = inst

    def set_finish_bit(self):
        self._finish_bit = True

    def get_entry(self):
        return self._inst

    def get_finish_bit(self):
        return self._finish_bit
    
    def set_rob_entry_val(self, val):
        self._val = val

    def get_rob_entry_val(self, val):
        return self._val

class BranchPredictor:
    """
    One-bit branch predictor
    """
    def __init__(self):
        # Start with True
        self._prediction = True

    def get_prediction(self):
        return self._prediction
    
    def incorrect_prediction(self):
        self._prediction = not(self._prediction)

# OS
class OperatingSystem:
    """
    Class dedicated to conduct Tomasulo's Algorithm.
    Assume there's only 1 adder, 1 floating-point adder
    """
    def __init__(self, config_data, file_to_run, folder_path):
        """
        Args:
            config_data: contains the configuration
        """

        self._config_data = config_data
        self._file_to_run = file_to_run

        output_file_name = f"output_{file_to_run}"
        current_directory = os.getcwd() + folder_path
        self._output_file_path = os.path.join(current_directory, output_file_name)

        if os.path.exists(self._output_file_path):
            with open(self._output_file_path, "w") as f:
                f.truncate()  # This clears the content

        # open the file & start writing to it
        self.f = open(self._output_file_path, "w")

        print("\n**********************************", file=self.f)
        print("*         Initial Setup          *", file=self.f)
        print("**********************************\n", file=self.f)

        print(f"\nRunning test case: {self._file_to_run}\n", file=self.f)

        # Access parsed data
        print("Functional Units: ", file=self.f)
        pprint.pprint(config_data["fu_details"], stream=self.f)
        print("ROB Entries: ", end='', file=self.f)
        print(config_data["rob_entries"], file=self.f)
        print("CDB Buffer Entries: ", end='', file=self.f)
        print(config_data["cdb_buffer_entries"], file=self.f)
        print("Misprediction Penalty: ", end='', file=self.f)
        print(config_data["misprediction_penalty"], file=self.f)
        print("Registers: ", config_data["registers"], file=self.f)
        print("Memory: ", config_data["memory"], file=self.f)
        print("Label: ", config_data["label"], file=self.f)
        print("Instructions: ", config_data["instructions"], file=self.f)


        # --------------- Read config data -----------------
        # read in instructions
        self._inst_buffer = self.parse_instructions(self._config_data['instructions'])
        if len(self._inst_buffer) == 0:
            print("----- No instruction given to run, terminated -----", file=self.f)
            return

        # *****************************
        # *  Architectural Registers  *
        # ******************************
        # 32 Integer Registers
        self._register = {}
        for i in range(0, 32):
            self._register[f"R{i}"] = 0

        # 32 FP Registers
        self._fp_register = {}
        for i in range(0, 32):
            self._fp_register[f"F{i}"] = 0
        
        for reg, val in self._config_data['registers'].items():
             # Read initial integer register config
            if reg in self._register:
                self._register[reg] = val
            
            # Read initial fp register config
            if reg in self._fp_register:
                self._fp_register[reg] = val


        # ****************
        # *    Memory    *
        # ****************
        self.memory = Memory()
        for mem_idx, val in self._config_data['memory'].items():
            self.memory.store_value(int(mem_idx) // 4, val)

        # ************************
        # *  ROB instiantiation  *
        # ************************
        self._ROB_entries = []
        rob_size = self._config_data["rob_entries"]
        for i in range(rob_size):
            self._ROB_entries.append(ReorderBuffer())
        self._ROB_entries_avail_idx = 0
        self._ROB_head_pointer = 0  # This is what we use to traverse ROB as its finished bit becomes True

        # Use RAT to map each instruction with each entry of ROB
        self._RAT = {}                  # RAT (source mapping) {"R1": ["# index of ROB entry", "# index of ROB entry", etc.]}
        for i in range(0, 31):
            self._RAT[f"R{i}"] = []
        for i in range(0, 31):
            self._RAT[f"F{i}"] = []
        
        self._CDB_buffer_entries = self._config_data["cdb_buffer_entries"]

        self._active_instructions = []  # Keeps the ACTIVE inst

        # Reservation stations
        self._adder_reserv_st = ReservationStation(self.f, config_data["fu_details"]['integer_adder']['rs'])
        self._fp_adder_reserv_st = ReservationStation(self.f, config_data["fu_details"]['fp_adder']['rs'])
        self._fp_mult_reserv_st = ReservationStation(self.f, config_data["fu_details"]['fp_multiplier']['rs'])
        self._load_store_reserv_st = ReservationStation(self.f, config_data["fu_details"]['load_store_unit']['rs'])

        self._cycle = 0          # keep a track of cycles

        # List that keeps a track of dependent register
        # self._dependency_list = []

        # Load Store Queue to keep load/store inst in order (use list like a queue)
        # Reservation station for memory unit
        # NOTE: load & Store has dedicated adder for effective address calculation
        # Each entry of queue contains 2 fields: address & value (address to find location, value for store - not useful for loads)
        # "Store" writes into memory only in commmit stage (dequeued only when they commit)
        self.load_store_queue = []

        # Flag that I use to determine whether the commit has occurred
        # If True, do not run commit other instructions that are about to commit (bc commit should take 1 cycle each)
        self._is_commited = False

        # One-bit Predictor for branching
        self._one_bit_predictor = BranchPredictor()

        # Flag that checks if pipeline flush has been triggered
        self._pipeline_flush_flag = False
        # And when pipeline flush happens, restore index is used to restore the branch inst
        self._restore_branch_starting_idx = 0

        self._is_prev_inst_branch = False

        self._is_correctly_predicted = 0
        
        self._running_inst = 0

        self._parsed_instructions = None
        self._parsed_instructions_is_dependent = []

        self.run_pipeline()

    def check_dependency(self, current_inst):

        self._parsed_instructions = []

        for idx, inst in enumerate(self._active_instructions):

            stage = inst.get_stage()
            if stage == "Terminated" or stage == "COMMIT":
                continue

            op = inst.get_opcode()

            if inst == current_inst:
                break

            if op in ["LD", "SD"]:
                # Load and Store instructions
                if op == "LD":
                    if stage == "WB":
                        continue

                    des = inst.get_operand_1()  # Destination register
                    src1 = inst.get_operand_2()  # Base register as source 1
                    src2 = None
                elif op == "SD":

                    des = None  # Store doesn't have a destination
                    src1 = inst.get_operand_1()  # Source register to store
                    # src2 = base  # Base register as source 2
                    src2 = None
            elif op[0] == 'B':
                # if branch, only check 1 and 2
                des = None
                src1 = inst.get_operand_1()
                src2 = inst.get_operand_2()
            else:
                # if stage == "WB":
                #     continue
                des = inst.get_operand_1()
                src1 = inst.get_operand_2()
                src2 = inst.get_operand_3()

            self._parsed_instructions.append((stage, op, des, src1, src2))

        # print(self._parsed_instructions)
        # Check dependencies with earlier instructions

        op = current_inst.get_opcode()

        if op in ["LD", "SD"]:
            # Load and Store instructions
            if op == "LD":
                des = current_inst.get_operand_1()  # Destination register
                src1 = current_inst.get_operand_2()  # Base register as source 1
                src2 = None
        elif op == "SD":
                des = None  # Store doesn't have a destination
                src1 = current_inst.get_operand_1()  # Source register to store
                # src2 = base  # Base register as source 2
                src2 = None
        elif op[0] == 'B':
            # if branch, only check 1 and 2
            des = None
            src1 = current_inst.get_operand_1()
            src2 = current_inst.get_operand_2()
        else:
            des = current_inst.get_operand_1()
            src1 = current_inst.get_operand_2()
            src2 = current_inst.get_operand_3()

        for prev_idx, (prev_stage, prev_op, prev_dest, prev_src1, prev_src2) in enumerate(self._parsed_instructions):
            # print("prev: ", prev_dest, prev_src1, prev_src2)
            # print("=>", des, src1, src2)
            if des == prev_dest:
                return True  # WAW
            if des == prev_src1 or des == prev_src2:
                return True  # WAR
            if (src1 == prev_dest or src2 == prev_dest):
                return True  # RAW
                
        return False

    def find_free_reservation(self, inst: ProcessControlBlock):
        """
        Find if the corresponding instruction can be placed inside the reservation station
        """

        inst_type = inst.get_opcode()
        is_successful = False
        
        if inst_type == "ADD" or inst_type == "ADDI" or inst_type == "SUB" or inst_type == "SUBI":     # For adder reservation station
            is_successful = self._adder_reserv_st.store_inst(inst)

        if inst_type == "ADD.D" or inst_type == "SUB.D":     # For adder reservation station
            is_successful = self._fp_adder_reserv_st.store_inst(inst)

        if inst_type == "MULT.D":                          # For floating-point reservation station
            is_successful = self._fp_mult_reserv_st.store_inst(inst)

        if inst_type == "LD":
            is_successful = self._load_store_reserv_st.store_inst(inst)
            self._load_store_reserv_st.print_reserv_station_content()

        if inst_type == "SD":
            is_successful = self._load_store_reserv_st.store_inst(inst)

        if inst_type == "BEQ" or inst_type == "BNE":     # branch inst added to integer ALU
            is_successful = self._adder_reserv_st.store_inst(inst)  

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
        # NOTE: Find the idx of instruction's reservation station
        inst_reserv_idx = inst.get_reserv_idx()
        is_fp = inst.get_is_fp()
        
        match(op):
            # ***************
            # *    Adder    *
            # ***************
            case 'ADD':
                if current_stage == "EX":
                    if is_executed == False:
                        # ---- First save the executed result to reservation station -> during WB, write to register -----
                        # if is_fp == True:
                        #     res = self._fp_register[operand_2] + self._fp_register[operand_3]
                        #     self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        # else:
                        res = self._register[operand_2] + self._register[operand_3]
                        self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()          # set the executed flag to True
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    # if is_fp == True:
                    #     self._fp_register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx)   # write the result to register now
                    #     self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx)   # write the result to register now
                    # Clear the reservation station entry
                    self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # remove register from dependency list -> allow other instructions w/ dependencies to run
                    # self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            case 'ADDI':
                if current_stage == "EX":
                    if is_executed == False:
                        # if is_fp == True:
                        #     res = self._fp_register[operand_2] + int(operand_3)
                        #     self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        # else:
                        res = self._register[operand_2] + int(operand_3)
                        self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    # if is_fp == True:
                    #     self._fp_register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    #     self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            case 'ADD.D':
                if current_stage == "EX":
                    if is_executed == False:
                        # ---- First save the executed result to reservation station -> during WB, write to register -----
                        # if is_fp == True:
                        res = self._fp_register[operand_2] + self._fp_register[operand_3]
                        self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        # else:
                        # res = self._register[operand_2] + self._register[operand_3]
                        # self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()          # set the executed flag to True
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    # if is_fp == True:
                    self._fp_register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx)   # write the result to register now
                    self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    # self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx)   # write the result to register now
                    # Clear the reservation station entry
                    # self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # remove register from dependency list -> allow other instructions w/ dependencies to run
                    # if operand_1 not in self._dependency_list:
                    #     self._dependency_list.append(operand_1)
                    # else:
                    # #    self.remove_from_dependency_list(operand_1)
                    #     pass

                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            case 'SUB':
                if current_stage == "EX":
                    if is_executed == False:
                        # if is_fp == True:
                        #     res = self._fp_register[operand_2] - self._fp_register[operand_3]
                        #     self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        # else:
                        res = self._register[operand_2] - self._register[operand_3]
                        self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    # if is_fp == True:
                    #     self._fp_register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    #     self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            case 'SUBI':
                if current_stage == "EX":
                    if is_executed == False:
                        # if is_fp == True:
                        #     res = self._fp_register[operand_2] - int(operand_3)
                        #     self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        # else:
                        res = self._register[operand_2] - int(operand_3)
                        self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    # if is_fp == True:
                    #     self._fp_register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    #     self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            case 'SUB.D':
                if current_stage == "ISSUE":
                    inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "EX":
                    if is_executed == False:
                        # if is_fp == True:
                        res = self._fp_register[operand_2] - self._fp_register[operand_3]
                        self._fp_adder_reserv_st.store_result(inst_reserv_idx, res)
                        # else:
                        # res = self._register[operand_2] - self._register[operand_3]
                        # self._adder_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    # if is_fp == True:
                    self._fp_register[operand_1] = self._fp_adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    # self._register[operand_1] = self._adder_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now
                    # self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            # ***********************
            # *    FP Multiplier    *
            # ***********************
            case 'MULT.D':
                if current_stage == "EX":
                    if is_executed == False:
                        res = self._fp_register[operand_2] * self._fp_register[operand_3]
                        self._fp_mult_reserv_st.store_result(inst_reserv_idx, res)
                        inst.set_is_executed()
                        inst.increment_cycle_counter() # +1 to its own counter (spent 1 cycle)
                    else:
                        if inst.get_cycle_counter() < self._config_data["fu_details"]["fp_multiplier"]["cycles_in_ex"]-1:    # FP multiplier EX count
                            inst.increment_cycle_counter()
                        else:
                            inst.set_move_to_next_stage()  # takes 2 cycles in EX
                elif current_stage == "WB":
                    inst.set_move_to_next_stage()      # takes 1 cycle in WB
                    self._fp_register[operand_1] = self._fp_mult_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now

                    self._fp_mult_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # self.remove_from_dependency_list(operand_1)
                else:
                    inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            # case 'DIVD':
            #     if current_stage == "EX":
            #         if is_executed == False:
            #             res = self._fp_register[operand_2] / self._fp_register[operand_3]
            #             self._fp_mult_reserv_st.store_result(inst_reserv_idx, res)
            #             inst.set_is_executed()
            #         else:
            #             if inst.get_cycle_counter() < self._config_data["fu_details"]["fp_multiplier"]["cycles_in_ex"]-1:
            #                 inst.increment_cycle_counter()
            #             else:
            #                 inst.set_move_to_next_stage()  # takes 2 cycles in EX
            #     elif current_stage == "WB":
            #         inst.set_move_to_next_stage()      # takes 1 cycle in WB
            #         self._fp_register[operand_1] = self._fp_mult_reserv_st.get_reserv_content(inst_reserv_idx) # write the result to register now

            #         self._fp_mult_reserv_st.clear_reserv_content(inst_reserv_idx)
            #         self.remove_from_dependency_list(operand_1)
            #     else:
            #         inst.set_move_to_next_stage()      # takes 1 cycle in COMMIT
            # ***********************
            # *   Load Store Unit   *
            # ***********************
            case 'LD':
                # If there's a (), then check the address instead
                if current_stage == "EX":
                    if is_executed == False:
                        if "(" in operand_2:
                            # NOTE: use register as base address, add offset on top of it to find data
                            # 4 offset (in byte) = 1 (in word)
                            offset, reg = self.split_number_and_parentheses(operand_2)
                            if reg[0] == "R":
                                base_addr = self._register[reg]
                            elif reg[0] == "F":
                                base_addr = self._fp_register[reg]

                            self.load_store_queue.append(inst)  # add to load/store queue

                            # LOAD goes into memory whenever the address is calculated:
                            calculated_addr = (base_addr + offset) / 4
                            # grab the data from the memory
                            value = self.memory.load_value(int(calculated_addr))  # convert to word
                            self._load_store_reserv_st.store_result(inst_reserv_idx, value) # save in reservation station first
                            
                            inst.set_is_executed()
                            inst.set_move_to_next_stage()
                elif current_stage == "MEM":        
                    if inst.get_cycle_counter() < self._config_data["fu_details"]["load_store_unit"]["cycles_in_mem"]-1:    # FP multiplier EX count
                        inst.increment_cycle_counter()
                    else:
                        
                        val = self._load_store_reserv_st.get_reserv_content(inst_reserv_idx)
                        self._register[operand_1] = val # TODO: find whether it's reg or FP reg. Also, save to reservation station first
                        self.load_store_queue.pop(0)
                        inst.set_move_to_next_stage()  # takes 2 cycles in EX

                        # remove from dependency list
                        # self.remove_from_dependency_list(operand_1)
                        self._load_store_reserv_st.clear_reserv_content(inst_reserv_idx)
                else:
                    inst.set_move_to_next_stage()

            case 'SD':
                if current_stage == "EX":
                    if "(" in operand_2:
                        self.load_store_queue.append(inst)  # add to load/store queue
                        # self._load_store_reserv_st.store_result(inst_reserv_idx, )
                        inst.set_move_to_next_stage()

                        inst_reserv_idx = inst.get_reserv_idx()
                        self._load_store_reserv_st.clear_reserv_content(inst_reserv_idx)
                else:
                    inst.set_move_to_next_stage()

            # ***************************
            # *   Branch instructions   *
            # ***************************
            case 'BEQ':
                # NOTE: During EX stage, it verifies the prediction (done by one-bit predictor)
                if current_stage == "EX":
                    # NOTE: for branches, check if predicted right
                    is_predicted_correct = True
                    if is_executed == False:
                        # In case of fp-registers
                        if is_fp == True:
                            is_predicted_correct = True if self._fp_register[operand_1] == self._fp_register[operand_2] else False
                            #self._fp_adder_reserv_st.store_result(inst_reserv_idx, is_predicted_correct)
                        else:
                            is_predicted_correct = True if self._register[operand_1] == self._register[operand_2] else False
                            #self._adder_reserv_st.store_result(inst_reserv_idx, is_predicted_correct)

                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX

                        # Now compare with one-bit predictor
                        predicted_earlier = self._one_bit_predictor.get_prediction()
                        # If ISSUE prediction is wrong,
                        if predicted_earlier != is_predicted_correct:
                            self._one_bit_predictor.incorrect_prediction()  # switch the predictor to its opposite value (T->F, F->T)
                            # NOTE: Pipeline flush happens
                            self._pipeline_flush_flag = True    # trigger flush flag

                            self._is_correctly_predicted = 2    # indicating incorrect prediction (used for prints)

                        # If predicted correctly, then nothing happens
                        else:
                            self._is_correctly_predicted = 1

                        self._adder_reserv_st.clear_reserv_content(inst.get_reserv_idx())
                
                elif current_stage == "COMMIT":
                    # if is_fp == True:
                    #     self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    #     self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    inst.set_move_to_next_stage()
                        
                else:
                    inst.set_move_to_next_stage()

            case 'BNE':
                # NOTE: During EX stage, it verifies the prediction (done by one-bit predictor)
                if current_stage == "EX":
                    # NOTE: for branches, check if predicted right
                    is_predicted_correct = True
                    if is_executed == False:
                        # In case of fp-registers
                        if is_fp == True:
                            is_predicted_correct = True if self._fp_register[operand_1] != self._fp_register[operand_2] else False
                            #self._fp_adder_reserv_st.store_result(inst_reserv_idx, is_predicted_correct)
                        else:
                            is_predicted_correct = True if self._register[operand_1] != self._register[operand_2] else False
                            #self._adder_reserv_st.store_result(inst_reserv_idx, is_predicted_correct)

                        inst.set_is_executed()
                        inst.set_move_to_next_stage()  # takes 1 cycle in EX

                        # Now compare with one-bit predictor
                        predicted_earlier = self._one_bit_predictor.get_prediction()
                        # If ISSUE prediction is wrong,
                        if predicted_earlier != is_predicted_correct:
                            self._one_bit_predictor.incorrect_prediction()  # switch the predictor to its opposite value (T->F, F->T)
                            # NOTE: Pipeline flush happens
                            self._pipeline_flush_flag = True    # trigger flush flag

                            self._is_correctly_predicted = 2    # indicating incorrect prediction (used for prints)

                        # If predicted correctly, then nothing happens
                        else:
                            self._is_correctly_predicted = 1

                        self._adder_reserv_st.clear_reserv_content(inst.get_reserv_idx())
                
                elif current_stage == "COMMIT":
                    # if is_fp == True:
                    #     self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    # else:
                    #     self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                    inst.set_move_to_next_stage()
                        
                else:
                    inst.set_move_to_next_stage()

            case _:
                print("--- WARNING: Opcode Not supported, thus ignored ---", file=self.f)
                raise Exception("Given Opcode Not Supported")


    def split_number_and_parentheses(self, input_string):
        """
        Splits a string into a number and the content within parentheses.

        Args:
            input_string (str): The input string in the format 'number(content)'.

        Returns:
            tuple: A tuple containing the number (as an integer) and the string inside parentheses.
        """
        match = re.match(r"(\d+)\((.+?)\)", input_string)
        if match:
            number = int(match.group(1))
            content = match.group(2)
            return number, content
        else:
            raise ValueError("Input string is not in the expected format 'number(content)'")

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
            
            # --------- Check for dependency before entering EX stage --------------
            # NOTE: STORE dependency works differently than other instructions
            is_dependent = False
            opcode = inst.get_opcode()
            if curr_stage == "ISSUE":
                is_dependent = self.check_dependency(inst)

            if is_dependent == True:
                return
            
            # keep a track of how many cycles spent in each stage before move to the next stage
            if curr_stage != "ISSUE" and curr_stage != "COMMIT":
                cycle_spent = inst.get_cycle_counter()
                inst.update_stage_cycle_counter(curr_stage, self._cycle - cycle_spent, self._cycle)

            # ----- Check current stage, update the corresponding stage accordingly -----
            match(curr_stage):
                case "ISSUE":
                    inst.update_stage("EX")

                case "EX":
                    # Only LOAD use MEM
                    if opcode == "LD":
                        inst.update_stage("MEM")
                    elif opcode == "SD" or opcode[0] == 'B':
                        inst.update_stage("COMMIT") # if SD or branches, skip MEM & WB and jump to COMMIT
                    else:
                        inst.update_stage("WB")

                case "MEM":
                    inst.update_stage("WB")

                case "WB":
                    inst.update_stage("COMMIT")

                    ROB_idx = self._RAT[inst.get_operand_1()][0]
                    if inst == self._ROB_entries[ROB_idx].get_entry():
                        self._ROB_entries[ROB_idx].set_finish_bit()

                case "COMMIT":
                    # When COMMIT is reached, update the flag in ROB entries

                    if opcode == "SD" or opcode[0] == 'B':
                        
                        ROB_idx = inst.get_SD_helpr()
                        if inst == self._ROB_entries[ROB_idx].get_entry():
                            self._ROB_entries[ROB_idx].set_finish_bit()     # For SD & B_, stay in Commit until it's their time to commit
                    else:
                        ROB_idx = self._RAT[inst.get_operand_1()][0]
                    
                    if self._ROB_head_pointer == ROB_idx and self._is_commited == False:
                        self._ROB_head_pointer += 1
                        inst.update_stage_cycle_counter(curr_stage, self._cycle, self._cycle)
                        inst.update_stage("Terminated")   # NOTE: When instruction reaches 'Terminated', that's when it leaves the active instruction list
                        self._is_commited = True
                        if opcode == "SD" or opcode[0] == 'B':          # since nothing saved RAT for SD and B_, pass
                            # del self._RAT[inst.get_SD_helpr()][0] 
                            pass
                        else:
                            del self._RAT[inst.get_operand_1()][0]

                        # For SD (Since run operation happens first & update pipeline happens next):
                        # check if top-most inst in queue is current inst SD -> if it is, perform operation
                        if opcode == "SD":
                            if inst == self.load_store_queue[0]:
                                offset, reg = self.split_number_and_parentheses(inst.get_operand_2())
                                if reg[0] == "R":
                                    base_addr = self._register[reg]
                                elif reg[0] == "F":
                                    base_addr = self._fp_register[reg]
                                # convert to word & find address, then store the content of register
                                calculated_addr = (base_addr + offset) / 4
                                self.memory.store_value(int(calculated_addr), self._register[inst.get_operand_1()])
                                self.load_store_queue.pop(0)    # remove from queue
                                # inst.set_move_to_next_stage()
                                # self.remove_from_dependency_list(inst.get_operand_2()) # remove offset(addr) from dependency list

                        self._running_inst -= 1

                    # Otherwise, stay in COMMIT stage

            # reset the flag and counter (bc we just used the counter to track # of cycles spent in each stage)
            inst.reset_move_to_next_stage()
            inst.reset_cycle_counter()

        # NOTE: Before actually running the code, save all instructions
        saved_instruction_list = self._inst_buffer.copy()
        self._is_prev_inst_branch = False # Check if previous inst was branch -> if it was, then immediate put the current inst to EX 

        # ---------- 1. Get next instruction from instruction buffer ------------
        # Repeatedly run until the instruction buffer is empty
        counter_for_restoring_branch = 0
        cycle_penalty = 0   # misprediction penalty. Decrement by 1 when it exists -> affects what WILL be added to active inst (not what's already running)
        while(len(self._inst_buffer) != 0 or self._running_inst > 0):
            self._cycle += 1

            self._is_commited = False

            # NOTE: This is grabbing instruction from _inst_buffer -> putting them in active inst
            # First, check buffer to see if there's any instructions that need to be fetched
            if len(self._inst_buffer) != 0:

                if cycle_penalty <= 0:
                    inst = ProcessControlBlock(self._inst_buffer[0])

                    # --------- 2. Find a free reservation for it ----------
                    # if not free, stall until one is
                    # NOTE: instruction CANNOT be issued when the corresponding reservation station is full
                    is_successful = self.find_free_reservation(inst)

                    # if there's a space in reservation -> remove inst from buffer & add to queue
                    # otherwise, stall (keep it in _inst_buffer)
                    if is_successful is True:
                        
                        # Save instruction to available ROB entry
                        self._ROB_entries[self._ROB_entries_avail_idx].set_entry(inst)
                        if inst.get_opcode() == "SD" or inst.get_opcode()[0] == 'B':   # For SD(Store), RAT doesn't save anything
                            inst.set_SD_helper(self._ROB_entries_avail_idx)
                            
                            if inst.get_opcode() == "SD":
                                counter_for_restoring_branch += 1
                        else:
                            self._RAT[inst.get_operand_1()].append(self._ROB_entries_avail_idx)
                            counter_for_restoring_branch += 1

                        self._ROB_entries_avail_idx += 1

                        # Add ISSUE record to inst to keep a track of things
                        #if self._is_prev_inst_branch == False:
                        inst.update_stage_cycle_counter("ISSUE", self._cycle, self._cycle)
                        
                        # else:   # if prev inst is branch -> set next inst to EX stage
                        #     inst.update_stage_cycle_counter("EX", self._cycle, self._cycle)
                        #     self._is_prev_inst_branch = False

                        self._active_instructions.append(inst)  # Add to the active instruction queue (with instruction tracker)
                        del self._inst_buffer[0]    # remove instruction from inst buffer (since it's active now)
                        self._running_inst += 1

                        # Add to Dependency List
                        if inst.get_opcode() == "SD":
                            # self._dependency_list.append(inst.get_operand_1()) # use offset(addr) as dependency check instead
                            pass
                        elif inst.get_opcode()[0] == 'B':
                            # For branches, don't add to dependency list
                            # Don't add dependencies for branches

                            # NOTE: as soon as branch instruction comes in -> decide whether to take branch
                            # & Execute the next instruction in EX stage

                            self._is_prev_inst_branch = True

                            if self._one_bit_predictor.get_prediction() == True:
                                # 1. Read the label first
                                label_name = inst.get_operand_3()
                                predicted_inst_idx = self._config_data["label"][label_name]

                                # 2. Put instructions after predicted_inst_idx to inst_buffer
                                # First, clear self._inst_buffer & add from where the label starts
                                self._inst_buffer.clear()
                                self._inst_buffer = saved_instruction_list[predicted_inst_idx:]

                            else:
                                # If false, then proceed with what we have
                                pass

                            pass
                        # else:
                        #     if inst.get_operand_1() not in self._dependency_list:
                        #         if inst.get_operand_1() != inst.get_operand_2() and inst.get_operand_1() != inst.get_operand_3():
                        #             self._dependency_list.append(inst.get_operand_1())

                else:
                    cycle_penalty -= 1

            # ----- iterate through the ACTIVE instructions to progress -----
            for idx, inst in enumerate(self._active_instructions):
                
                if inst.get_stage() != "Terminated":
                    # ----- Run each operation in pipeline -----
                    self.perform_operation(inst)
                    # ----- Check if we can move to next stage (if move_next_stage flag is True) -----
                    update_inst_stage(inst)


                    # NOTE:
                    # If pipeline flush has occurred -> then the latest, most recent 2 instructions (branch + 1 more inst it ran after) in pipeline are the ones we want to remove
                    # So we can do this in for-loop (Since it will be called AT THE VERY END of the for-loop)
                    if self._pipeline_flush_flag == True:
                        # Reduce ROB entry idx by 2
                        for delete_inst in self._active_instructions[idx+1:]:
                            self._ROB_entries_avail_idx = self._ROB_entries_avail_idx - 1   #-2
                            self._running_inst -= 1 #2

                            # Clear reservation station for BEQ
                            # self._adder_reserv_st.clear_reserv_content(self._active_instructions[-2].get_reserv_idx())

                            # Remove all instructions after the branch from active inst.
                            # self._active_instructions.pop()
                            #self._active_instructions.pop()

                            # Check what type of inst is the one we want to flush from pipeline
                            opcode_to_remove = delete_inst.get_opcode()
                            inst_reserv_idx = delete_inst.get_reserv_idx()
                                
                            if opcode_to_remove == 'SD':    # Assume there's no BRNACH AFTER BRANCH
                                # Delete dependency from the list
                                # self._dependency_list.pop()
                                pass
                            elif opcode_to_remove[0] == 'B':
                                pass
                            else:   # for ADD, SUB, etc. bc you also need to delete entry from RAT
                                # Delete entry from RAT (remove from end)
                                if len(self._RAT[delete_inst.get_operand_1()]) != 0:
                                    self._RAT[delete_inst.get_operand_1()].pop()

                                # NOTE: We do not have to remove from dependency list & reservation station bc
                                # by the time we call pipeline flush, these commands will be in WB -> so reservation & dependency list removed
                                # So only have to worry about LD (Since it will be in MEM stage)
                                if delete_inst.get_opcode() == "LD":
                                    # Delete dependency from the list
                                    # if len(self._dependency_list) != 0:
                                    #     self._dependency_list.pop()

                                    # Also have to remove it from reservation station
                                    self._load_store_reserv_st.clear_reserv_content(inst_reserv_idx)

                            if opcode_to_remove == "ADD" or opcode_to_remove == "SUB" or opcode_to_remove == "ADDI":
                                self._adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                            elif opcode_to_remove == "ADD.D" or opcode_to_remove == "SUB.D":
                                self._fp_adder_reserv_st.clear_reserv_content(inst_reserv_idx)
                            elif opcode_to_remove == "MULT.D":
                                self._fp_mult_reserv_st.clear_reserv_content(inst_reserv_idx)

                            # No need to remove dependencies for branch inst (bc it wasn't added)

                            # Also need to clear the inst buffer & refill it with CORRECT path
                            self._inst_buffer.clear()
                            # restored_branch_inst = saved_instruction_list[counter_for_restoring_branch]
                            # self._inst_buffer.append(restored_branch_inst)  # restore branch inst

                            # label_name = restored_branch_inst[3]
                            # restore CORRECT path (counter_for_restoring_branch = correct idx) in this case

                        # NOTE: Find the corect Path
                        for curr_idx, each_inst in enumerate(saved_instruction_list):
                            if each_inst[0] == inst.get_opcode() and each_inst[1] == inst.get_operand_1() and each_inst[2] == inst.get_operand_2() and each_inst[3] == inst.get_operand_3():
                                for each_inst in saved_instruction_list[curr_idx+1:]:
                                    self._inst_buffer.append(each_inst)
                        
                        del self._active_instructions[idx+1:]

                        # And give misprediction penalty
                        cycle_penalty = self._config_data["misprediction_penalty"]

                        break   # break out from active_inst, rerun

                else:
                    # Set stage to TERMINATED
                    inst.update_stage("Terminated")

            if self._is_correctly_predicted == 1: # correct branch prediction
                print("!!!!!!!!! Branch Prediction: Correctly Predicted !!!!!!!!!!!!", file=self.f)
                self._is_correctly_predicted = 0

            elif self._is_correctly_predicted == 2: # incorrect branch prediction
                print("!!!!!!!!! Branch Prediction: Incorrectly Predicted !!!!!!!!!", file=self.f)
                self._is_correctly_predicted = 0

            if self._pipeline_flush_flag == True:
                mp_val = self._config_data["misprediction_penalty"]
                print(f"========> Pipeline Flush Has Occurred. Misprediction Penalty of {mp_val} Applied <=========", file=self.f)
                self._pipeline_flush_flag = False

            # Print the pipeline            
            self.print_pipeline()

            # Reservation Stations
            print("Reservation Stations in Current Cycle: ", file=self.f)
            print("Integer Adder: ", end='', file=self.f)
            self._adder_reserv_st.print_reserv_station_content()
            print("FP Adder: ", end='', file=self.f)
            self._fp_adder_reserv_st.print_reserv_station_content()
            print("FP Multplier: ", end='', file=self.f)
            self._fp_mult_reserv_st.print_reserv_station_content()
            print("Load Store: ", end='', file=self.f)
            self._load_store_reserv_st.print_reserv_station_content()
            # print(self._register, file=self.f)

        # Print Final Stat
        self.print_final_stat()
                
    def print_pipeline(self):
        """
        Print the current pipeline
        """
        print("\n--------------------------------------", file=self.f)
        print(f"\nCurrent cycle: {self._cycle}\n", file=self.f)

        for inst in self._active_instructions:
            if inst.get_opcode() == "LD" or inst.get_opcode() == "SD":
                print(f"{inst.get_opcode()} {inst.get_operand_1()} {inst.get_operand_2()} | ", end='', file=self.f)
            else:
                print(f"{inst.get_opcode()} {inst.get_operand_1()} {inst.get_operand_2()} {inst.get_operand_3()} | ", end='', file=self.f)
            for key, value in inst.get_stage_cycle_counter().items():
                if key != "Terminated":
                    print(f"{key}:{value} ", end='', file=self.f)
            print("\n", file=self.f)

    def print_final_stat(self):
        """
        Print the status of the internals
        """

        print("\n\n\nPipeline Finished, Start Printing the Final Overall Result...\n\n", file=self.f)

        print("\n***********************************", file=self.f)
        print("*                                 *", file=self.f)
        print("*  Internal Structure At the End  *", file=self.f)
        print("*                                 *", file=self.f)
        print("***********************************\n", file=self.f)

        # Reservation Status
        print("********************************", file=self.f)
        print("* Reservation Statation Status *", file=self.f)
        print("********************************\n", file=self.f)

        print("        Adder Reservation Station: ", file=self.f)
        print("-----------------------------------------", file=self.f)
        self._adder_reserv_st.print_reserv_station_content()
        print("\nFloating-Point Adder Reservation Station:", file=self.f)
        print("-----------------------------------------", file=self.f)
        self._fp_adder_reserv_st.print_reserv_station_content()
        print("\nFloating-Point Mult Reservation Station:", file=self.f)
        print("-----------------------------------------", file=self.f)
        self._fp_mult_reserv_st.print_reserv_station_content()
        print("\n    Load Store Reservation Station: ", file=self.f)
        print("-----------------------------------------", file=self.f)
        self._load_store_reserv_st.print_reserv_station_content()

        # Instruction Status (in pipeline form)
        print("\n*******************************", file=self.f)
        print("* Instruction Pipeline Status *", file=self.f)
        print("*******************************\n", file=self.f)

        for inst in self._active_instructions:
            if inst.get_opcode() == "LD" or inst.get_opcode() == "SD":
                print(f"{inst.get_opcode()} {inst.get_operand_1()} {inst.get_operand_2()} | ", end='', file=self.f)
            else:
                print(f"{inst.get_opcode()} {inst.get_operand_1()} {inst.get_operand_2()} {inst.get_operand_3()} | ", end='', file=self.f)
            for key, value in inst.get_stage_cycle_counter().items():
                if key != "Terminated":
                    print(f"{key}:{value} ", end='', file=self.f)
            print("\n", file=self.f)

        # Register result status
        print("\n***************************", file=self.f)
        print("* Register Content Status *", file=self.f)
        print("***************************\n", file=self.f)
        print("Integer Register\n", file=self.f)
        counter = 0
        for key, value in self._register.items():                
            if counter < 10:
                counter += 1
                print(f"{key}:{value}  ", end='', file=self.f)
            else:
                if key == "R15":
                    print(f"{key}:{value}  ", file=self.f)
                else:
                    print(f"{key}:{value}  ", end='', file=self.f)


        print("\n\nFloating-Point Register\n", file=self.f)
        counter = 0
        for key, value in self._fp_register.items():
            if counter < 10:
                counter += 1
                print(f"{key}:{value}  ", end='', file=self.f)
            else: 
                if key == "F15":
                    print(f"{key}:{value}  ", file=self.f)
                else:
                    print(f"{key}:{value}  ", end='', file=self.f)

        # Memory
        print("\n\n*************************", file=self.f)
        print("* Memory Content Status *", file=self.f)
        print("*************************\n", file=self.f)
        for i in range(0, 64):
            memory_val = self.memory.load_value(i)
            if i % 7 == 0 and i != 0:
                print(f"Memory[{i*4}]:{memory_val}  ", file=self.f)
            else:
                print(f"Memory[{i*4}]:{memory_val}  ", end='', file=self.f)


        print(f"\n\nTotal number of cycles: {self._cycle}\n", file=self.f)
 
        print("\n**********************************\n", file=self.f)

        self.f.close()

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
            "rs": int(lines[1].split()[2].strip()),
            "cycles_in_ex": int(lines[1].split()[3].strip()),
            "cycles_in_mem": None,
            "f_units": int(lines[1].split()[4].strip()),
        },
        "fp_adder": {
            "rs": int(lines[2].split()[2].strip()),
            "cycles_in_ex": int(lines[2].split()[3].strip()),
            "cycles_in_mem": None,
            "f_units": int(lines[2].split()[4].strip()),
        },
        "fp_multiplier": {
            "rs": int(lines[3].split()[2].strip()),
            "cycles_in_ex": int(lines[3].split()[3].strip()),
            "cycles_in_mem": None,
            "f_units": int(lines[3].split()[4].strip()),
        },
        "load_store_unit": {
            "rs": int(lines[4].split()[2].strip()),
            "cycles_in_ex": int(lines[4].split()[3].strip()),
            "cycles_in_mem": int(lines[4].split()[4].strip()),
            "f_units": int(lines[4].split()[5].strip()),
        },
    }

    # Parse ROB and CDB buffer entries
    config["rob_entries"] = int(lines[6].split()[1].strip())
    config["cdb_buffer_entries"] = int(lines[7].split()[1].strip())
    config["misprediction_penalty"] = int(lines[8].split()[1].strip())

    # Memory
    config["memory"] = {}
    # branch labels
    config["label"] = {}
    # Dynamically parse register values
    config["registers"] = {}
    register_section_started = False
    instruction_section_started = False
    instruction_idx_cnt = 0
    for line in lines[9:]:
        stripped_line = line.strip()

        if not stripped_line:  # Skip empty lines
            continue

        if any(op in stripped_line for op in ["ADD","ADD.D","ADDI","SUB","SUB.D","MULT.D", "SD", "LD", "BEQ", "BNE"]):
            config.setdefault("instructions", []).append(stripped_line)
            instruction_idx_cnt += 1
        else:
            # Parse registers
            register_section_started = True
            if stripped_line.startswith("R") and len(stripped_line.split()) == 2:
                register, value = stripped_line.split()
                config["registers"][register] = int(value)

            if stripped_line.startswith("F") and len(stripped_line.split()) == 2:
                register, value = stripped_line.split()
                config["registers"][register] = float(value)

            if stripped_line.startswith("MEM") and len(stripped_line.split()) == 2:
                memory, value = stripped_line.split()
                config["memory"][memory[4:-1]] = float(value)

            # If reads in branch label, save it!
            if stripped_line.endswith(":"):
                label_name = stripped_line[:-1]
                config["label"][label_name] = instruction_idx_cnt

    return config
