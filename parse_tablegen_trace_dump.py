#! /usr/bin/python3
import ast

IN_FILE  = 'tablegen_generated_with_dummies.txt'
OUT_FILE = 'MSP430_DMA.py'

print(f"... Reading from '{IN_FILE}'; writing to '{OUT_FILE}'")
with open(OUT_FILE, 'w') as fo:
    with open(IN_FILE) as fi:
        fo.write('dma_traces = {\n')
        for l in fi:
            d = ast.literal_eval(l)
            fo.write(f"    '{d['short']}'".ljust(16) + f" : '{d['trace']}',\n")
        fo.write('}\n')
