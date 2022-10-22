from scfmsp.controlflowanalysis.ExecutionPoint import ExecutionPoint
from scfmsp.controlflowanalysis.MSP430 import MSP430AS, MSP430AD
from scfmsp.controlflowanalysis.MSP430_DMA import dma_traces

class AbstractInstruction:
    name = ''
    length = 2
    map1 = {}

    def __init__(self, function):
        self.file = ''
        self.program = function.program
        self.function = function

        self.address = 0
        self.length = 0
        self.clock = 0
        self.arguments = ()
        self.oplist = []
        
        self.register_mode = False
        self.indexed_mode =  False
        self.indirect_mode =  False
        self.immediate_mode =  False
        self.dst_register_mode =  False
        self.dst_indexed_mode = False

        self.immediate_dominator = None
        self.immediate_post_dominator = None
        self.predecessors = None

        self.__successors_checked_cache = None
        self.__execution_point = None

        # NOTE: we redefine our own variables here to not further clubber the
        # parsing below and to ensure that src/dst are assigned only a single
        # addressing mode at a time
        self.as_mode = ''
        self.ad_mode = ''

    def __unicode__(self):
        return '%s: %s %s' % (hex(self.address), self.name, self.arguments)

    def __repr__(self):
        return self.__unicode__()

    def determine_addressing_modes(self, arg1, arg2=None):
        if (arg1 == 3) or (arg1 == 2 and (self.indirect_mode or self.immediate_mode)):
            self.as_mode = MSP430AS.CONSTANT
        elif self.indexed_mode and arg1 == 2:
            self.as_mode = MSP430AS.ABSOLUTE
        elif self.immediate_mode and arg1 == 0:
            self.as_mode = MSP430AS.IMMEDIATE
        elif self.indexed_mode and arg1 == 0:
            self.as_mode = MSP430AS.SYMBOLIC
        elif self.immediate_mode:
            self.as_mode = MSP430AS.INDIRECT_INC
        elif self.indirect_mode:
            self.as_mode = MSP430AS.INDIRECT
        elif self.indexed_mode:
            self.as_mode = MSP430AS.INDEXED
        elif self.register_mode:
            self.as_mode = MSP430AS.DIRECT

        if arg2 is not None:
            if self.dst_indexed_mode and arg2 == 2:
                self.ad_mode = MSP430AD.ABSOLUTE
            elif self.dst_indexed_mode and arg2 == 0:
                self.ad_mode = MSP430AD.SYMBOLIC
            elif self.dst_indexed_mode:
                self.ad_mode = MSP430AD.INDEXED
            elif self.dst_register_mode:
                self.ad_mode = MSP430AD.DIRECT

    '''
        Parses the given asm instruction into its corresponding LLVM tablegen short format.
    '''
    def mk_short(self, inst):
        ops = inst.split('.')
        op = ops[0].upper()
        oplen = '8' if (len(ops) > 1) else '16'
        postfix = f'{self.ad_mode}{self.as_mode}'

        if 'J' in op:
            op = 'JMP' if op == 'JMP' else 'JCC'
            oplen = ''
            postfix = ''

        elif self.ad_mode == MSP430AD.DIRECT and self.arguments[1] == 'r0':
            if self.as_mode == MSP430AS.INDIRECT_INC and self.arguments[0] == 'r1':
                op =  'RET'
                oplen = ''
                postfix = ''
            else:
                op = 'BRCALL'
                oplen = ''
                postfix = f'{self.as_mode}'

        elif self.as_mode == MSP430AS.INDIRECT_INC and self.arguments[0] == 'r1':
                op = 'POP'
                postfix = f'{self.ad_mode}'

        elif inst == 'MOV.B':
            if self.as_mode == MSP430AS.DIRECT and self.ad_mode == MSP430AD.DIRECT:
                op = 'ZEXT'
                oplen = '16'
                postfix = 'r'
            else:
                op = 'MOVZX'
                oplen = '16'
                postfix += '8'

        elif op == 'SXT':
            op = 'SEXT'

        elif op == 'CALL':
            oplen = ''

        elif op == 'RETI':
            oplen = ''
            postfix = ''

        self.short =  op + oplen + postfix

    # https://en.wikipedia.org/wiki/TI_MSP430#MSP430_CPU
    def parse(self, op_list):
        instr = ''
        self.oplist = op_list.split()
        temp = '{0:04b}'.format(int(self.oplist[0][0],16))
        temp1 =  '{0:04b}'.format(int(self.oplist[0][3],16))
        temp2 =  '{0:04b}'.format(int(self.oplist[0][2],16))
        # source addressing mode-----------------------------
        if (temp[2] == '0' and temp[3] == '0'):
            self.register_mode =  True
        if (temp[2] == '0' and temp[3] == '1'):
            self.indexed_mode =  True
        if (temp[2] == '1' and temp[3] == '0'):
            self.indirect_mode = True
        if(temp[2] == '1' and temp[3] == '1'):
            self.immediate_mode = True
        # destination addressing mode------------------
        if(temp[0] == '0'):
            self.dst_register_mode = True
        else:
            self.dst_indexed_mode = True

        # Instruction II (1 operand)-----------------------
        if (self.oplist[0][2] == '1'):
            arg1 = int(self.oplist[0][1],16)
            self.determine_addressing_modes(arg1)

            # Length of instructions and arguments ---------------
            if(self.register_mode):
                length = 1
                self.arguments = ('r'+str(arg1),)

            if(self.indirect_mode):
                length = 1
                self.arguments = ('r'+str(arg1),)  

            if(self.indexed_mode):
                length = 2
                if(arg1 == 3):
                    length = 1
                self.arguments = ('r'+str(arg1),)   

            if(self.immediate_mode):
                if (self.oplist[0][1] == '0'):
                    length = 2
                    self.arguments = ('#'+self.oplist[0][6]+self.oplist[0][7]+self.oplist[0][4]+self.oplist[0][5],) 
                else:
                    length = 1
                    self.arguments = ('r'+str(arg1),)
            # Instruction types II------------------------------------------
            if (temp1[2]=='0' and temp1[3]=='0' and temp[0]=='0'):
                if (temp[1] == '1'):
                    instr = 'rrc.b'
                else:
                    instr = 'rrc'
            if (temp1[2]=='0' and temp1[3]=='0' and temp[0]=='1'):
                instr = 'swpb'
            if (temp1[2]=='0' and temp1[3]=='1' and temp[0]=='0'):
                instr = 'rra'
            if (temp1[2]=='0' and temp1[3]=='1' and temp[0]=='1'):
                instr = 'sxt'
            if (temp1[2]=='1' and temp1[3]=='0' and temp[0]=='0'):
                instr = 'push'
            if (temp1[2]=='1' and temp1[3]=='0' and temp[0]=='1'):
                instr = 'call'
            if (temp1[2]=='1' and temp1[3]=='1' and temp[0]=='0'):
                instr = 'reti'   


        # Instruction III-----------------------------------
        elif (self.oplist[0][2] == '2' or self.oplist[0][2] == '3'):
            # Length of instruction
            length = 1
            self.clock = 2
            # Instruction III
            if (temp2[3]=='0' and temp1[0]=='0' and temp1[1]=='0'):
                instr = 'jnz'
            if (temp2[3]=='0' and temp1[0]=='0' and temp1[1]=='1'):
                instr = 'jz'
            if (temp2[3]=='0' and temp1[0]=='1' and temp1[1]=='0'):
                instr = 'jnc'
            if (temp2[3]=='0' and temp1[0]=='1' and temp1[1]=='1'):
                instr = 'jc'
            if (temp2[3]=='1' and temp1[0]=='0' and temp1[1]=='0'):
                instr = 'jn'
            if (temp2[3]=='1' and temp1[0]=='0' and temp1[1]=='1'):
                instr = 'jge'
            if (temp2[3]=='1' and temp1[0]=='1' and temp1[1]=='0'):
                instr = 'jl'
            if (temp2[3]=='1' and temp1[0]=='1' and temp1[1]=='1'):
                instr = 'jmp'


          # Instruction I ------------------------------------
        else:
            arg1 = int(self.oplist[0][3],16)
            arg2 = int(self.oplist[0][1],16)
            self.determine_addressing_modes(arg1, arg2)

            # Length of instruction & arguments
            if(self.register_mode and self.dst_register_mode):
                length = 1
                self.clock = 1
                if (arg2 == 0):
                    self.clock = 2
                self.arguments = ('r'+str(arg1),'r'+str(arg2),)

            if(self.register_mode and self.dst_indexed_mode):
                length = 2
                self.clock = 4
                if(arg2 == 2):
                    self.arguments = ('r'+str(arg1),'&'+self.oplist[0][6]+self.oplist[0][7]+self.oplist[0][4]+self.oplist[0][5],)
                else:
                    self.arguments = ('r'+str(arg1),'r'+str(arg2),)

            if(self.indexed_mode and self.dst_register_mode):
                length = 2
                if (self.oplist[0][3] == '3'): # constant generator -------------
                    length = 1
                    self.clock = 1
                else:
                    # Note: Documented openMSP430 ISA deviation: always 3 cycles even for R0
                    self.clock = 3
                if(arg1 == 2):
                    self.arguments = ('&'+self.oplist[0][6]+self.oplist[0][7]+self.oplist[0][4]+self.oplist[0][5],'r'+str(arg2),)
                else:
                    self.arguments = ('r'+str(arg1),'r'+str(arg2),)   
            if(self.indexed_mode and self.dst_indexed_mode):
                length = 3
                self.clock = 6
                if (self.oplist[0][3] == '3'): # constant generator -------------
                    length = 2
                    self.clock = 4 
                if(arg1 == 2): 
                    self.arguments = ('&'+self.oplist[0][6]+self.oplist[0][7]+self.oplist[0][4]+self.oplist[0][5],'&'+self.oplist[0][10]+self.oplist[0][11]+self.oplist[0][8]+self.oplist[0][9],)
                else:
                    self.arguments = ('r'+str(arg1),'r'+str(arg2),)
            
            if(self.indirect_mode and self.dst_register_mode):
                length = 1
                if (self.oplist[0][3] == '2' or self.oplist[0][3] == '3'): # constant generator -------------
                    self.clock = 1
                else:
                    self.clock = 2
                    # Note: Documented openMSP430 ISA deviation: 2->3 for R0
                    if (arg2 == 0):
                        self.clock = 3
                self.arguments = ('r'+str(arg1),'r'+str(arg2),)

            if(self.indirect_mode and self.dst_indexed_mode):
                length = 2
                if (self.oplist[0][3] == '2' or self.oplist[0][3] == '3'): # constant generator -------------
                    self.clock = 4
                else:
                    self.clock = 5
                if(arg2 == 2):
                    self.arguments = ('r'+str(arg1),'&'+self.oplist[0][6]+self.oplist[0][7]+self.oplist[0][4]+self.oplist[0][5],)
                else:
                    self.arguments = ('r'+str(arg1),'r'+str(arg2),)

            if(self.immediate_mode and self.dst_register_mode):
                if (self.oplist[0][3] == '0'): #-----##------
                    length = 2
                    self.clock = 2
                    if (arg2 == 0):
                        self.clock = 3
                    self.arguments = ('#'+self.oplist[0][6]+self.oplist[0][7]+self.oplist[0][4]+self.oplist[0][5],'r'+str(arg2),)
                else:# indirect autoincrement -------------------
                    length = 1
                    if (self.oplist[0][3] == '2' or self.oplist[0][3] == '3'): # constant generator -------------
                        self.clock = 1
                    else:
                        self.clock = 2
                        if (arg2 == 0):
                            self.clock = 3
                    self.arguments = ('r'+str(arg1),'r'+str(arg2),)

            if(self.immediate_mode and self.dst_indexed_mode):
                if (self.oplist[0][3] == '0'):#-----#------
                    length = 3
                    self.clock = 5
                    self.arguments = ('#'+self.oplist[0][6]+self.oplist[0][7]+self.oplist[0][4]+self.oplist[0][5],'r'+str(arg2),)
                else:# indirect autoincrement -----------------------------
                    length = 2
                    if (self.oplist[0][3] == '2' or self.oplist[0][3] == '3'): # constant generator -------------
                        self.clock = 4
                    else:
                        self.clock = 5
                    self.arguments = ('r'+str(arg1),'r'+str(arg1),)

            # Instruction type I --------------------------------------------------------------------------------------------------------------------
            if (self.oplist[0][2] == '4'):
                if (temp[1] == '1'):
                    instr =  'mov.b'
                else:
                    instr =  'mov'
            if (self.oplist[0][2] == '5'):
                if (temp[1] == '1'):
                    instr =  'add.b'
                else:
                    instr =  'add'
            if (self.oplist[0][2] == '6'):
                if (temp[1] == '1'):
                    instr =  'addc.b'
                else:
                    instr =  'addc'
            if (self.oplist[0][2] == '7'):
                if (temp[1] == '1'):
                    instr =  'subc.b'
                else:
                    instr =  'subc'
            if (self.oplist[0][2] == '8'):
                if (temp[1] == '1'):
                    instr =  'sub.b'
                else:
                    instr =  'sub'
            if (self.oplist[0][2] == '9'):
                if (temp[1] == '1'):
                    instr =  'cmp.b'
                else:
                    instr =  'cmp'        
            if (self.oplist[0][2] == 'a'):
                if (temp[1] == '1'):
                    instr =  'dadd.b'
                else:
                    instr =  'dadd'
            if (self.oplist[0][2] == 'b'):
                if (temp[1] == '1'):
                    instr =  'bit.b'
                else:
                    instr =  'bit'
            if (self.oplist[0][2] == 'c'):
                if (temp[1] == '1'):
                    instr =  'bic.b'
                else:
                    instr =  'bic'
            if (self.oplist[0][2] == 'd'):
                if (temp[1] == '1'):
                    instr =  'bis.b'
                else:
                    instr =  'bis'
            if (self.oplist[0][2] == 'e'):
                if (temp[1] == '1'):
                    instr =  'xor.b'
                else:
                    instr =  'xor'
            if (self.oplist[0][2] == 'f'):
                if (temp[1] == '1'):
                    instr =  'and.b'
                else:
                    instr =  'and'


        return instr, length, self.arguments, self.clock, self.register_mode, self.indexed_mode, self.immediate_mode, self.indirect_mode, self.dst_register_mode, self.dst_indexed_mode, self.as_mode, self.ad_mode
    
    def set_info(self, instr_str, length, address, arguments, clock, oplist, register, index, immediate, indirect, dst_register, dst_index, file, as_mode, ad_mode):
        self.length = length
        self.address = address
        self.arguments = arguments
        self.clock = clock
        self.oplist = oplist
        self.register_mode =  register
        self.indexed_mode = index
        self.immediate_mode =  immediate
        self.indirect_mode =  indirect
        self.dst_indexed_mode = dst_index
        self.dst_register_mode = dst_register
        self.file =  file

        self.latency = self.get_execution_time()
        self.as_mode = as_mode
        self.ad_mode = ad_mode
        self.trace = None
        self.mk_short(instr_str)

        try:
            self.trace = dma_traces[self.short]
        except KeyError:
            print(f'KeyError: Unknown MSP430TableGen instruction: {self.short}')

        print(f'{self.short:12} {instr_str:5} ' \
              f'with latency={self.latency}; trace={str(self.trace):26} ' \
              f'{str(self.arguments):20} (@{self.address:#x} in {self.file})')

        assert('UNKNOWN' not in self.short)
        #assert(self.trace)
        if (self.trace is not None):
            if (self.latency*3 + 2) != len(self.trace) :
                print(f'WARNING: Incorrect instruction latency {self.latency} vs. DMA trace length')

    def get_execution_point(self):
        if self.__execution_point is None:
            self.__execution_point = ExecutionPoint(self.function.name, self.address, self.function.caller)
        return self.__execution_point

    def get_successors(self):        
        return [self.get_execution_point().forward(self.length*2)]

    def get_successors_checked(self):
        if self.__successors_checked_cache is not None:
            return self.__successors_checked_cache
        successors = self.get_successors()
        ret = []
        for succ in successors:
            try:
                self.program.get_instruction_at_execution_point(succ)
                ret.append(succ)
            except:
                pass
        self.__successors_checked_cache = ret
        return ret

    def get_execution_time(self):
        pass

    def get_branching_time(self):
        return 2

    def get_region_then(self):
        return []

    def get_region_else(self):
        return []

    def _get_branchtime(self, region):
        ret = 0
        for ep in region:
            instr = self.program.get_instruction_at_execution_point(ep)
            ret += instr.get_execution_time()
            
            if not (ep == self.get_execution_point()):
                ret -= instr.get_branchtime_then()     
        return ret

    def get_branchtime_then(self):
        return self._get_branchtime(self.get_region_then())

    def get_branchtime_else(self):
        return self._get_branchtime(self.get_region_else())

    def get_junction(self):
        return None

    def execute_judgment(self, ac):
        raise NotImplementedError('Instruction "%s" is lacking an execute_judgment implementation! At %s' %
                                  (self.name, self.get_execution_point()))

