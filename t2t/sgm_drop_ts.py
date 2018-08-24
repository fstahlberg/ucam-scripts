# coding=utf-8
r"""Removes testsuites from SGM files
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Converts an nbest list to plain text files.')
parser.add_argument('-is','--input_src_sgm', help='Input source sgm ("src" sgm).', required=True)
parser.add_argument('-it','--input_trg_sgm', help='Input target sgm ("src" sgm).', required=True)
parser.add_argument('-os','--output_src_sgm', help='Output source sgm ("src" sgm).', required=True)
parser.add_argument('-ot','--output_trg_sgm', help='Output target sgm ("ref" sgm).', required=True)
parser.add_argument('-oi','--output_indices', help='Output line numbers.', required=True)
args = parser.parse_args()


with open(args.input_src_sgm, "r") as src_reader:
  with open(args.input_trg_sgm, "r") as trg_reader:
    with open(args.output_src_sgm, "w") as src_writer:
      with open(args.output_trg_sgm, "w") as trg_writer:
        with open(args.output_indices, "w") as indices_writer:
          line_nr = -1
          src_active = True
          trg_active = True
          for src_input_line in src_reader:
            parts = src_input_line.split()
            if parts[0] == "<srcset":
              parts[0] = "<refset"
              src_writer.write(src_input_line)
              trg_writer.write(" ".join(parts) + "\n")
            elif parts[0] == "<doc":
              src_active = not "testsuite" in src_input_line
              if src_active:
                src_writer.write(src_input_line)
                trg_writer.write(src_input_line)
            elif parts[0] == "<seg":
              line_nr += 1
              if not src_active:
                continue
              # Find trg sentence
              while True:
                trg_input_line = next(trg_reader)
                trg_parts = trg_input_line.split()
                if trg_parts[0] == "<doc":
                  trg_active = not "testsuite" in trg_input_line
                elif trg_parts[0] == "<seg" and trg_active:
                  trg_writer.write(trg_input_line)
                  break
              src_writer.write(src_input_line)
              indices_writer.write("%d\n" % line_nr)
            elif parts[0] == "</srcset>":
              src_writer.write(src_input_line)
              trg_writer.write("</refset>\n")
            else:
              if src_active:
                src_writer.write(src_input_line)
                trg_writer.write(src_input_line)
