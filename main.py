#! /usr/bin/python3

import json
import sys
from rich import print_json

from scfmsp.sidechannelverifier.Analysis import Analysis
from scfmsp.dataextraction.ContainerInitializer import ContainerInitializer
from scfmsp.dataextraction.SyntaxConverter import SyntaxConverter

import argparse
import logging

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('json_file')
    parser.add_argument('--debug', dest='log_level', action='store_const', const=logging.DEBUG, default=logging.WARNING)
    parser.add_argument('--info', dest='log_level', action='store_const', const=logging.INFO)
    parser.add_argument('--warning', dest='log_level', action='store_const', const=logging.WARNING)
    parser.add_argument('--error', dest='log_level', action='store_const', const=logging.ERROR)
    parser.add_argument('--minimal', action='store_true')
    args = parser.parse_args()

    if args.minimal:
        args.log_level = logging.ERROR

    logging.basicConfig(format='%(levelname)s: %(message)s', level=args.log_level)

    initializer = ContainerInitializer()
    initializer.parse_file(args.json_file)
    program = SyntaxConverter.parse_file(initializer.get_file_path(), initializer.get_starting_function())

    analysis = Analysis(program)
    starting_ep = program.functions[initializer.get_starting_function()].first_instruction.get_execution_point()
    starting_ac = initializer.get_starting_ac()
    finishing_ac = initializer.get_finishing_ac()
    timing_sensitive = initializer.get_timing_sensitive()
    print(args.json_file.rjust(40), end='\t')

    try:
        result = analysis.analyze(starting_ep, starting_ac, finishing_ac, timing_sensitive)
    except:
        print("Recursion exception!")
        exit()

    output = {
        'result': result.result.name,
        'result_code': result.result.value,
        'execution_point': None if result.ep is None else {
            'function': result.ep.function,
            'address': hex(result.ep.address),
            'then_branch': str(result.instr_then),
            'else_branch': str(result.instr_else),
        },
        'unique_ret': str(result.unique_ret)
    }
    json_res = json.dumps(output)
    if args.minimal:
        print(result.result)
    else:
        print_json(json_res)

    return result.result.value

if __name__ == '__main__':
    sys.exit(main())
