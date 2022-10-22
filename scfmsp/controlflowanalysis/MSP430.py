from enum import Enum

'''
From <https://en.wikipedia.org/wiki/TI_MSP430#MSP430_CPU>

MSP430 addressing modes
--------------------------------------------------------------------------------
As 	Ad 	Register 	Syntax 	Description
--------------------------------------------------------------------------------
00 	0 	n 	        Rn 	Register direct. The operand is the
                                        contents of Rn.
01 	1 	n 	        x(Rn) 	Indexed. The operand is in memory at
                                        address Rn+x.
10 	— 	n 	        @Rn 	Register indirect. The operand is in
                                        memory at the address held in Rn.
11 	— 	n 	        @Rn+ 	Indirect autoincrement. As above, then
                                        the register is incremented by 1 or 2.
--------------------------------------------------------------------------------

Addressing modes using R0 (PC)
--------------------------------------------------------------------------------
As 	Ad 	Register 	Syntax 	Description
--------------------------------------------------------------------------------
01 	1 	0 (PC) 	        ADDR 	Symbolic. Equivalent to x(PC). The
                                        operand is in memory at address PC+x.
11 	— 	0 (PC) 	        #x 	Immediate. Equivalent to @PC+. The
                                        operand is the next word in the
                                        instruction stream.
--------------------------------------------------------------------------------

Addressing modes using R2 (SR) and R3 (CG), special-case decoding
--------------------------------------------------------------------------------
As 	Ad 	Register 	Syntax 	Description
--------------------------------------------------------------------------------
01 	1 	2 (SR) 	        &ADDR 	Absolute. The operand is in memory at
                                        address x.
10 	— 	2 (SR) 	        #4 	Constant. The operand is the constant 4.
11 	— 	2 (SR) 	        #8 	Constant. The operand is the constant 8.
00 	— 	3 (CG) 	        #0 	Constant. The operand is the constant 0.
01 	— 	3 (CG) 	        #1 	Constant. The operand is the constant 1.
                                        There is no index word.
10 	— 	3 (CG) 	        #2 	Constant. The operand is the constant 2.
11 	— 	3 (CG) 	        #−1 	Constant. The operand is the constant −1.
--------------------------------------------------------------------------------
'''

'''
    https://github.com/llvm-mirror/llvm/blob/master/lib/Target/MSP430/MSP430InstrFormats.td#L17
'''
class MSP430AS(Enum):
    DIRECT       = 'r'
    INDEXED      = 'n'
    INDIRECT     = 'p'          #TODO not in parse_tablegen script?
    INDIRECT_INC = 'p'    
    SYMBOLIC     = 'UNKNOWN'    #TODO not in parse_tablegen script?
    IMMEDIATE    = 'i'
    ABSOLUTE     = 'm'
    CONSTANT     = 'c'

    def __str__(self):
        return self.value
 
class MSP430AD(Enum):
    DIRECT       = 'r'
    INDEXED      = 'n'
    SYMBOLIC     = 'UNKNOWN'
    ABSOLUTE     = 'm'

    def __str__(self):
        return self.value
