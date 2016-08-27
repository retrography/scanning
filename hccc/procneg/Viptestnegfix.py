#!/usr/bin/env python3

# coding: utf-8

import sys
import gi
import math
gi.require_version('Vips', '8.0')
from gi.repository import Vips



def profile(im):
    temp = im.extract_area(10, 10, im.width - 20, im.height - 20).gaussblur(3, min_ampl=0.5)

    minimar = temp[0].min()
    minimag = temp[1].min()
    minimab = temp[2].min()
    maximar = temp[0].max()
    maximag = temp[1].max()
    maximab = temp[2].max()

    values = [1, 1, 1, 0, 0, 0]

    values = [min((minimar if minimar > 0 else values[0]), values[0]),
              min((minimag if minimag > 0 else values[1]), values[1]),
              min((minimab if minimab > 0 else values[2]), values[2]),
              max((maximar if maximar < 1 else values[3]), values[3]),
              max((maximag if maximag < 1 else values[4]), values[4]),
              max((maximab if maximab < 1 else values[5]), values[5])]

    return [values[0], values[1], values[2],
            pow((values[0] / values[3]), (1 / gamma)) * qrange * 0.95,
            math.log10(values[4] / values[1]) / math.log10(values[3] / values[0]),
            math.log10(values[5] / values[2]) / math.log10(values[3] / values[0])]


def invert(im, prof):
    r = im[0]
    g = im[1]
    b = im[2]
    
    r = (prof[0] / r)
    g = (prof[1] / g).gamma(exponent = prof[4])
    b = (prof[2] / b).gamma(exponent = prof[5])
    
    im = (r.bandjoin([g, b]))
    
    im = im.gamma(exponent = gamma)
    im = im * (qrange + 1) - prof[3]

    return im.cast(bandfmt)


infile = sys.argv[1]
im = Vips.Image.new_from_file(infile)

bandfmt = im.BandFmt
gamma = 2.15
qrange = pow(2, im.Bbits) - 1
im = im / qrange

prof = profile(im)
im = invert(im, prof)       
im.write_to_file("p_"+infile)

