class Instruction:
    """
    Class dedicated for the instruction
    """
    def __init__(self, instruction):

        self._opcode = instruction[0]
        self._operand_1 = instruction[1]
        self._operand_2 = instruction[2]

        self._stage = 'ISSUE'   # initial stage of instruction in pipeline
        self._is_stall = False  # indicator flag to indicate whether the instruction is in stall

    def get_opcode(self):
        return self._opcode
    
    def get_operand_1(self):
        return self._operand_1
    
    def get_operand_2(self):
        return self._operand_2

    def get_stage(self):
        return self._stage
    
    def update_stage(self, stage_name):
        self._stage = stage_name

class Register:
    """
    Register
    """
    def __init__(self, val):
        """
        Args:
            val(int): value the register holds
        """
        self._val = val

    def get_val(self):
        return self._val

    def set_val(self, val):
        self_val = val

class ReservationStation:
    """
    Reservation station that temporary holds the instruction
    """
    def __init__(self, capacity: int):
        self._capacity = capacity
        self._reserv_statation = [None] * self.capacity
        self._is_full = False

    def store_inst(self, inst: Instruction):
        # Find free space in reservation station
        for idx, content in self._reserv_statation:
            if content is None:
                self._reserv_statation[idx] = inst
                return

        # if there's no free space, set is_full as True
        self._is_full = True

    def check_is_full(self):
        return self._is_full

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
    def __init__(self, inst_buffer: list, rc: int = 4, frc: int = 4, rg: int = 10, lrc: int = 4, strc: int = 4):
        """
        Args:
            inst_buffer (Instruction): list of instructions in Instruction type
            rc (int): adder reservation station capacity
            frc (int): floating-point adder reservation capacity
            rg (int): number of registers
            lrc (int): load reservation station capacity
            strc (int): store reservation station capacity
        """
        self._inst_buffer = inst_buffer     # store all the given instructions
        self._inst_in_pipeline = []         # list that keeps a track of "running instructions"

        self._RAT = []      # RAT (source mapping)
        self._ARF = []      # Architecture Reg File

        # Register
        self._register = [Register(0)] * rg

        # Reservation stations
        self._adder_reserv_st = ReservationStation(rc)
        self._fp_adder_reserv_st = ReservationStation(frc)
        self._load_reserv_st = ReservationStation(lrc)
        self._store_reserv_st = ReservationStation(strc)

        self._cycle = 0          # keep a track of cycles

        if inst_buffer.empty():
            print("----- No instruction given to run, terminated -----")
            return

        self.run()

    def find_free_reservation(self, inst):
        """
        Find if the corresponding instruction can be placed inside the reservation station
        """

        inst_type = inst.get_opcode()
        is_full = False

        if inst_type is "ADD" or inst_type is "ADDI" or inst_type is "SUB":     # For adder reservation station
            self._adder_reserv_st.store_inst(inst)
            is_full = self._adder_reserv_st.check_is_full()
        
        if inst_type is "MULT" or inst_type is "DIVD":                          # For floating-point reservation station
            self._fp_adder_reserv_st.store_inst(inst)
            is_full = self._fp_adder_reserv_st.check_is_full()

        if inst_type is "LDR":
            self._load_reserv_st.store_inst(inst)
            is_full = self._load_reserv_st.check_is_full

        if inst_type is "STR":
            self._store_reserv_st.store_inst(inst)
            is_full = self._store_reserv_st.check_is_full

        return is_full

    def perform_operation(self, inst):
        # Depends on the opcode, run different stages
        op = inst.get_opcode()
        match(op):
            case 'ADD':
                pass
            case 'ADDI':
                pass
            case 'SUB':
                pass
            case 'MULT':
                pass
            case 'DIVD':
                pass
            case 'LDR':
                pass
            case 'STR':
                pass
            case _:
                print("Not supported")

    def pipeline(self, inst_list):
        """
        Runs each instruction in inst_in_pieline, progress their stages.
        Keep a track of cycle
        """
        def update_inst_stage(inst):
            curr_stage = inst.get_stage()
            match(curr_stage):
                case "ISSUE":
                    inst.update_stage("EX")
                case "EX":
                    inst.update_stage("MEM")
                case "MEM":
                    inst.update_stage("WB")
                case "WB":
                    inst.update_stage("COMMIT")
                case "COMMIT":
                    inst.update_stage("DONE")

        # Go through each instruction inside the list
        for inst in inst_list:
           update_inst_stage(inst)


        pass

    def run(self):
        """
        Run Tomasulo's Algorithm
        """

        self._cycle += 1

        # 1. Get next instruction from instruction buffer
        # Repeatedly run until the instruction buffer is empty
        if not self._inst_buffer.empty():
            inst = self._inst_buffer.pop(0)
            self._inst_in_pipeline.append(inst)
        
        # 2. Find a free reservation for it
        # if not free, stall until one is
        # NOTE: instruction CANNOT be issued when the corresponding reservation station is full
        is_full = self.find_free_reservation(inst)
            
        if is_full is True:
            pass    # TODO: stall

        # 3. Read operands that are in registers
        # If not in register, find which reservation station will product it

        if not self._inst_in_pipeline.empty():
            self.pipeline(self._inst_in_pipeline)



        # 4. Rename registers


        # 5. Reservation stations are now physical registers



        pass
        
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



def main():

    instruction_buffer = []
    with open('your_file.txt', 'r') as file:
        for line in file:
            words = line.split()  # Split the line by whitespace & save in list
            instruction_buffer.append(Instruction(words))

    # Initialization
    tm = OperatingSystem(
        inst_buffer=instruction_buffer, 
        rc=4,
        frc=4,
    )

    # Testing each instruction


    pass

if __name__ == '__main__':
    main()
