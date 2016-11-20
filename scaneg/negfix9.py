#!/usr/bin/env python3

# coding: utf-8

import sys
import gi
import math
gi.require_version('Vips', '8.0')
from gi.repository import Vips

# Negfix profiler
# LUT not implemented yet

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


# Negfix inverter
# B&W not implemented yet
# LUT not implemented yet

def invert(im, prof):

# When implementing B&W
#    if im.bands >= 3:
#        r = transform(im[0])
#        g = transform(im[1])
#        b = transform(im[2])
#        return r.bandjoin([g, b])
#    else:
#        return transform(im[0])

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

# drlim function

def shadows(band, lim):
    mask = (band <= lim).cast(band.BandFmt, shift = True)
    lut = (band & mask).identity(ushort = True)
    lut = (65535 * (lut / lim * 0.1))
    return band.maplut(lut) & mask

# drlim function

def highlights(band, lim):
    mask = (band >= lim).cast(band.BandFmt, shift = True)
    lut = (band & mask).identity(ushort = True)
    lut = (65535 * ((lut - lim) / (65536 - lim) * 0.1 + 0.9))
    return band.maplut(lut) & mask
    
# drlim function

def midtones(band, lims):
    mask = ((band > lims[0]) & (band < lims[1])).cast(band.BandFmt, shift = True)
    lut = (band & mask).identity(ushort = True)
    lut = (lut - lims[0]) / (lims[1] - lims[0])
    lut = (65535 * (lut * 0.8 + 0.1))
    return band.maplut(lut) & mask  

# drlim function

def drlim(band):
    lims = (band.percent(1), band.percent(99))
    lo = shadows(band, lims[0])
    hi = highlights(band, lims[1])
    mid = midtones(band, lims)
    return lo.add(mid).add(hi).cast(band.BandFmt) 

# Dynamic Range Limit function

def drlim(im):
    if im.bands >= 3:
        r = drlim(im[0])
        g = drlim(im[1])
        b = drlim(im[2])
        return r.bandjoin([g, b])
    else:
        band = im[0]
        lims = (band.percent(1), band.percent(99))
        lo = shadows(band, lims[0])
        hi = highlights(band, lims[1])
        mid = midtones(band, lims)
        return lo.add(mid).add(hi).cast(band.BandFmt) 

# Contrast Stretch

def cs(im):
    # Image histogram
    h = im.cast(Vips.BandFormat.UCHAR, shift=True).hist_find()
    w = h.width
    mp = im.width * im.height
    threshold = mp * 0.001
    lims = [[-1,-1],[-1,-1],[-1,-1]]
    for p in range(w - 2):
        for b in range(h.bands):
            if lims[b][0] == -1 and (h[b](p, 0)[0] > threshold) and (h[b](p + 1,0)[0] > threshold) and (h[b](p + 2,0)[0] > threshold):
                lims[b][0] = p 
            if lims[b][1] == -1 and (h[b](w - p - 1, 0)[0] > threshold) and (h[b](w - p - 2,0)[0] > threshold) and (h[b](w - p - 3,0)[0] > threshold):
                lims[b][1] = (w - p - 1)
            
    bands = im.bandsplit()
    for band in range(h.bands):
        a = 0
        b = pow(2,16) - 1
        c = lims[band][0] 
        d = lims[band][1]
        bands[band] = (im[band] - c * 256) * ((b - a)/(256 * (d - c))) + a

    im = bands[0].bandjoin([bands[1], bands[2]])
    return im.cast(bandfmt)

infile = sys.argv[1]
im = Vips.Image.new_from_file(infile)

bandfmt = im.BandFmt
gamma = 2.15
qrange = pow(2, im.Bbits) - 1
im = im / qrange

prof = profile(im)
im = invert(im, prof)

#TODO: create a cl option for drlim
im = drlim(im)       

#TODO: create a cl option for cs
im = cs(im)

im.write_to_file("p_"+infile)

