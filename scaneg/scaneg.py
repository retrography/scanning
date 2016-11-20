#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(description='ScaNeg negative scanning tool')

parser.add_argument('-i', '--infra', action="store_true", default=False, help="scan the infrared channel for dust and scratch removal")
parser.add_argument('-g', '--grey', action="store_true", default=False, help="greyscale scan for b&w negatives (default: colour)")
parser.add_argument('-r', '--resolution', action="store", type=int, default=1200, choices=set((1200,2400,4800)), help="scan resolution in dpi")
parser.add_argument('-f', '--format', action="store", default="135", choices=set(("135", "120")), help="film holder format (slide holder not supported yet)")

args = parser.parse_args()

def fmt_to_dims(argument):
    switcher = {
        '120': {'l': 80.6, 'x': 56.2, 't': 25.8, 'y': 219.2},
        '135': {'l': 77, 'x': 63.06, 't': 21.75, 'y': 226}
    }
    return switcher.get(argument)

dims = fmt_to_dims(args.format)

