#!/usr/bin/env python3

# coding: utf-8

import sys
import gi
gi.require_version('Vips', '8.0')
from gi.repository import Vips

def gamma(band, gamma):
    return band.gamma(exponent = (1/gamma))

def shadows(band, lim):
    mask = (band <= lim).cast(band.BandFmt, shift = True)
    return (65535 * (band / lim * 0.1)) & mask

def highlights(band, lim):
    mask = (band >= lim).cast(band.BandFmt, shift = True)
    return (65535 * ((band - lim) / (65536 - lim) * 0.1 + 0.9)) & mask

def midtones(band, lims):
    mask = ((band > lims[0]) & (band < lims[1])).cast(band.BandFmt, shift = True)
    band = (band - lims[0]) / (lims[1] - lims[0])
    band = gamma(band, 2.2)
    return (65535 * (band * 0.8 + 0.1)) & mask    

def invert(band):
    band = band.invert()
    lims = (band.percent(5), band.percent(95))
    lo = shadows(band, lims[0])
    hi = highlights(band, lims[1])
    mid = midtones(band, lims)
    return (lo.add(mid).add(hi)).cast(band.BandFmt)

infile = sys.argv[1]
im = Vips.Image.new_from_file(infile)
if im.bands >= 3:
    r = invert(im[0])
    g = invert(im[1])
    b = invert(im[2])
    im = r.bandjoin([g, b])
else:
    im = invert(im[0])        
im.write_to_file("p_"+infile)
