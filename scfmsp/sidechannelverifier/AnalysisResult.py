from enum import Enum


class AnalysisResult(Enum):
    SUCCESS = 0
    INFORMATION_LEAK = 1        # leak via return value(?)
    TIMING_LEAK = 2             # different start-to-end timing
    LOOP_ON_SECRET_DATA = 3     # secret-dependent loop condition
    NEMESIS_VULNERABILITY = 4   # different instruction counts or latencies
    DMA_VULNERABILITY = 5       # different instruction rom/ram/mmio access trace
