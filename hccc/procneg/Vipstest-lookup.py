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
    lut = (band & mask).identity(ushort = True)
    lut = (65535 * (lut / lim * 0.1))
    return band.maplut(lut) & mask

def highlights(band, lim):
    mask = (band >= lim).cast(band.BandFmt, shift = True)
    lut = (band & mask).identity(ushort = True)
    lut = (65535 * ((lut - lim) / (65536 - lim) * 0.1 + 0.9))
    return band.maplut(lut) & mask
    
def midtones(band, lims):
    mask = ((band > lims[0]) & (band < lims[1])).cast(band.BandFmt, shift = True)
    lut = (band & mask).identity(ushort = True)
    lut = (lut - lims[0]) / (lims[1] - lims[0])
    lut = gamma(lut, 2.15)
    lut = (65535 * (lut * 0.8 + 0.1))
    return band.maplut(lut) & mask  

def transform(band):
    band = band.invert()
    lims = (band.percent(5), band.percent(95))
    lo = shadows(band, lims[0])
    hi = highlights(band, lims[1])
    mid = midtones(band, lims)
    return lo.add(mid).add(hi).cast(band.BandFmt) 

def invert(im):
    if im.bands >= 3:
        r = transform(im[0])
        g = transform(im[1])
        b = transform(im[2])
        return r.bandjoin([g, b])
    else:
        return transform(im[0])

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
