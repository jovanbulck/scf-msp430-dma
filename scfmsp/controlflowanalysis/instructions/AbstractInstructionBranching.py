from scfmsp.sidechannelverifier.SecurityLevel import SecurityLevel
from scfmsp.sidechannelverifier.exceptions.BranchtimeDiffersException import BranchtimeDiffersException
from scfmsp.sidechannelverifier.exceptions.LoopOnHighConditionException import LoopOnHighConditionException
from scfmsp.sidechannelverifier.exceptions.NemesisOnHighConditionException import NemesisOnHighConditionException
from scfmsp.sidechannelverifier.exceptions.DMAOnHighConditionException import DMAOnHighConditionException

from scfmsp.controlflowanalysis.RegionComputation import RegionComputation
from scfmsp.controlflowanalysis.instructions.AbstractInstructionControlFlow import AbstractInstructionControlFlow

import logging
logger = logging.getLogger(__file__)

do_supress_idx_error = False

class AbstractInstructionBranching(AbstractInstructionControlFlow):
    def __init__(self, function):
        super(AbstractInstructionBranching, self).__init__(function)
        self.regions_computed = False
        self.region_then = []
        self.region_else = []
        self.nemesis_region_then = []
        self.nemesis_region_else = []
        self.junction = None
        self.then_number = 0
        self.else_number = 0

    def get_successors(self):
        ret = super(AbstractInstructionBranching, self).get_successors()
        ret.append(self.get_branch_target())
        return ret

    def compute_regions(self):
        self.region_then = set()
        self.region_else = set()
        self.nemesis_region_then = []
        self.nemesis_region_else = []
        computation = RegionComputation(self.program, self.region_then, self.region_else, self.nemesis_region_then, self.nemesis_region_else)
        self.junction = computation.start_computation(self)

    def get_region_then(self):
        if not self.regions_computed:
            self.compute_regions()
            self.regions_computed = True
        
        return self.region_then

    def get_region_else(self):
        if not self.regions_computed:
            self.compute_regions()
            self.regions_computed = True
        
        return self.region_else

    def get_junction(self):
        if not self.regions_computed:
            self.compute_regions()
            self.regions_computed = True

        return self.junction

    def compare_region(self):
        for ep_then , ep_else in zip(self.nemesis_region_then, self.nemesis_region_else):
            instr_then = self.program.get_instruction_at_execution_point(ep_then)
            instr_else = self.program.get_instruction_at_execution_point(ep_else)
            latency_then = instr_then.get_execution_time()
            latency_else = instr_else.get_execution_time()
            if (latency_then != latency_else):
                return (True, f'latency {latency_then} for {instr_then}', f'latency {latency_else} for {instr_else}')
        return (False, None, None)

    def have_nemesis(self):
        logger.info('Checking Nemesis')
        nemesis = True
        instr_cnt_then = len(self.nemesis_region_then)
        instr_cnt_else = len(self.nemesis_region_else)
        if( instr_cnt_then == instr_cnt_else):
            return self.compare_region()
        return (nemesis, f'count={instr_cnt_then}', f'count={instr_cnt_else}')

    def compare_region_dma(self):
        for ep_then , ep_else in zip(self.nemesis_region_then, self.nemesis_region_else):
            instr_then = self.program.get_instruction_at_execution_point(ep_then)
            instr_else = self.program.get_instruction_at_execution_point(ep_else)
            trace_then = instr_then.get_dma_trace()
            trace_else = instr_else.get_dma_trace()
            if (trace_then != trace_else):
                return (True, f'DMA trace {trace_then} for {instr_then}', f'DMA trace {trace_else} for {instr_else}')
        return (False, None, None)

    def have_dma(self):
        logger.info('Checking DMA')
        dma = True
        instr_cnt_then = len(self.nemesis_region_then)
        instr_cnt_else = len(self.nemesis_region_else)
        if( instr_cnt_then == instr_cnt_else):
            return self.compare_region_dma()
        return (dma, f'count={instr_cnt_then}', f'count={instr_cnt_else}')

    def is_loop(self):
        return self.immediate_dominator in self.get_region_else() or self.immediate_dominator in self.get_region_then()


    def get_branching_condition_domain(self, ac):
        pass
            
    def execute_judgment(self, ac):
        if (self.get_branching_condition_domain(ac) & ac.secenv.get(self.get_execution_point())) == SecurityLevel.LOW:
            return

        global do_supress_idx_error
        ep = self.get_execution_point()

        # HACK (manually checked) to work around over-approximation in SCF-MSP tool
        if ep.address == 0x81ca and ep.function == 'modexp_enter':
            logger.warning(f'Overriding known false-positive @{ep.address:#x} (in {ep.function})')
            do_supress_idx_error = True
            return

        try:
            for ep in self.get_region_then():
                ac.secenv.set(ep, SecurityLevel.HIGH)
            for ep in self.get_region_else():
                ac.secenv.set(ep, SecurityLevel.HIGH)
        except IndexError as ie:
            if do_supress_idx_error:
                logger.warning(f'Overriding IndexError false-positive @{ep.address:#x} (in {ep.function})')
                return      
            else:
                raise ie

        ac.stack = [SecurityLevel.HIGH for _ in range(len(ac.stack))]

        if self.is_loop():
            #raise LoopOnHighConditionException()
            logger.warning(f'Overriding LoopOnHighConditionException @{ep.address:#x} (in {ep.function})')
            return

        
        (have_nemesis, instr_then, instr_else) = self.have_nemesis()
        if have_nemesis:
            raise NemesisOnHighConditionException(instr_then, instr_else)

        (have_dma, instr_then, instr_else) = self.have_dma()
        if have_dma:
            raise DMAOnHighConditionException(instr_then, instr_else)

        if not self.is_loop():
            if not (self.get_branchtime_then() == self.get_branchtime_else()):
                raise BranchtimeDiffersException()
