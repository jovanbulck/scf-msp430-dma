class NemesisOnHighConditionException(Exception):

    def __init__(self, instr_then, instr_else):
        self.instr_then  = instr_then
        self.instr_else = instr_else
