#!/usr/bin/env python3

# coding: utf-8

import sys
import gi
import math
gi.require_version('Vips', '8.0')
from gi.repository import Vips

#TODO: Test BW
#TODO: Negfix profiler not implemeted yet
#TODO: IR separation not implemented yet
#TODO: Resize not implemented yet
#TODO: Frame cut not implemented yet
#TODO: Dust removal not implemented yet


def profile(im):
    temp = im.extract_area(10, 10, im.width - 20, im.height - 20).gaussblur(3, min_ampl=0.5)

    mins = [None] * nobands
    maxs = [None] * nobands
    minvals = [1] * nobands
    maxvals = [0] * nobands
    result = [None] * nobands

    for b in range(0, nobands):
        mins[b] = temp[b].min()
        maxs[b] = temp[b].max()
        minvals[b] = min((mins[b] if mins[b] > 0 else minvals[b]), minvals[b])
        maxvals[b] = max((maxs[b] if maxs[b] < 1 else maxvals[b]), maxvals[b])
        result[b] = math.log10(maxvals[b] / minvals[b]) / math.log10(maxvals[0] / minvals[0])

    return minvals + result + [pow((minvals[0] / maxvals[0]), (1 / gamma)) * qrange * 0.95]


def invert(im):

#TODO: LUT not implemented yet

    bands = [None] * nobands
    for b in range(0, nobands):
        bands[b] = (prof[b] / im[b]).gamma(exponent=prof[b + nobands])

    im = bands[0]
    if nobands > 1:
        im = im.bandjoin(bands[1:nobands])

    im = im.gamma(exponent=gamma)
    im = im * (qrange + 1) - prof[nobands * 2]

    return im.cast(bandfmt)


# Shadow / Highlight Recovery
def shrecovery(im):

    def shadows(band, lim):
        mask = (band <= lim).cast(band.BandFmt, shift=True)
        lut = (band & mask).identity(ushort=True)
        lut = (65535 * (lut / lim * 0.1))
        return band.maplut(lut) & mask

    def highlights(band, lim):
        mask = (band >= lim).cast(band.BandFmt, shift=True)
        lut = (band & mask).identity(ushort=True)
        lut = (65535 * ((lut - lim) / (65536 - lim) * 0.1 + 0.9))
        return band.maplut(lut) & mask

    def midtones(band, lims):
        mask = ((band > lims[0]) & (band < lims[1])).cast(band.BandFmt, shift=True)
        lut = (band & mask).identity(ushort=True)
        lut = (lut - lims[0]) / (lims[1] - lims[0])
        lut = (65535 * (lut * 0.8 + 0.1))
        return band.maplut(lut) & mask

    bands = [None] * nobands
    for b in range(0, nobands):
        limits = (im[b].percent(1), im[b].percent(99))
        lo = shadows(im[b], limits[0])
        hi = highlights(im[b], limits[1])
        mid = midtones(im[b], limits)
        bands[b] = lo.add(mid).add(hi).cast(im[b].BandFmt)

    im = bands[0]
    if nobands > 1:
        im = im.bandjoin(bands[1:nobands])

    return im


# Contrast Stretch
def cstretch(im):
    # Image histogram
    h = im.cast(Vips.BandFormat.UCHAR, shift=True).hist_find()
    w = h.width
    mp = im.width * im.height
    threshold = mp * 0.001
    limits = [[-1, -1], [-1, -1], [-1, -1]]
    for p in range(w - 2):
        for b in range(h.bands):
            if limits[b][0] == -1 and (h[b](p, 0)[0] > threshold) and (h[b](p + 1, 0)[0] > threshold) and (h[b](p + 2, 0)[0] > threshold):
                limits[b][0] = p
            if limits[b][1] == -1 and (h[b](w - p - 1, 0)[0] > threshold) and (h[b](w - p - 2, 0)[0] > threshold) and (h[b](w - p - 3, 0)[0] > threshold):
                limits[b][1] = (w - p - 1)
            
    bands = im.bandsplit()
    for band in range(h.bands):
        a = 0
        b = pow(2, 16) - 1
        c = limits[band][0]
        d = limits[band][1]
        bands[band] = (im[band] - c * 256) * ((b - a)/(256 * (d - c))) + a

    im = bands[0]
    if nobands > 1:
        im = im.bandjoin(bands[1:nobands])

    return im.cast(bandfmt)

infile = sys.argv[1]
image = Vips.Image.new_from_file(infile)

resolution = int(image.xres * 25.4)

if resolution == 4800:
    image = image.shrink(3, 3)
elif resolution in [1200, 2400]:
    image = image.shrink(2, 2)

if image.bands >= 3:
    color = True
    nobands = 3
else:
    color = False
    nobands = 1

bandfmt = image.BandFmt
gamma = 2.15
qrange = pow(2, image.Bbits) - 1
image /= qrange
prof = profile(image)

image = invert(image)

#TODO: create a commandline option for shrecovery
#image = shrecovery(image)

#TODO: create a commandline option for cstretch
#image = cstretch(image)

image.write_to_file("p_"+infile)

