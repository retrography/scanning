'''Map a scanned photographic negative to a correctly
coloured and exposed (hopefully) positive image. This
sort of follows the process described in:

 Digital Processing of Scanned Negatives
 Qian Kin, Daniel Tretter
 Imaging Systems Laboratory
 HP Laboratories Palo Alto
 HPL-97-16(R.1)
 July 6th 2004

 This implementation is:
 Copyright (C) 2012 Nick Glazzard
 Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
 '''
import Image
import filebits
import os

def invert(p):
    '''Convert negative to positive.'''
    return( 255 - p )

def mapmid(v,gamma):
    '''Map midtones (range 0:1) using a sigmoid (S shaped) function.'''
    if( v <= 0.5 ):
        return 0.5 * pow( 2*v, gamma )
    else:
        return 1.0 - 0.5 * pow( ( 2 - 2*v ), gamma )

def mapfull(v,h5,h95,gamma):
    '''Map shadows (<5 percentile), highlights (>95 percentile) and
       midtone regions independently. Shadows -> bottom tenth output,
       Highlights -> top tenth output, Midtone -> 0.1 to 0.9 of output.'''
    if( v < h5 ):
        vd = float(v) / h5 * 0.1
    elif( v > h95 ):
        vd = float(v-h95) / (256-h95) * 0.1 + 0.9
    else:
        vd = mapmid( float(v-h5)/(h95-h5), gamma ) * 0.8 + 0.1
    return 255*vd

def percentile(h,perc):
    '''Find the value corresponding to the perc percentile of
    histogram h.'''
    summ = 0
    for i in range(0,len(h)):
        summ += h[i]
    t = 0.01 * perc * summ
    summ = 0
    for i in range(0,len(h)):
        summ += h[i]
        if( summ >= t ):
            return i
    return len(h)-1

def colourneg( inname, gamma, outname ):
    '''Process image file inname to image file outname.
       Allow the gamma of the S shaped part of the colour mapping
       (used for midtones) to be specified.'''

    try:
        # Open the input image.
        a = Image.open( inname )
        print 'Input image mode: ', a.mode

        # Invert raw data including the orange cast.
        b = a.point( invert )

        # Histogram each colour channel.
        h = b.histogram()
        hr = h[:256]
        hg = h[256:512]
        hb = h[512:768]

        # Find the 5th and 95th percentile values for
        # each channel. These are used as "black" and "white"
        # points. Below "black" is shadow, above "white" is
        # highlight.
        hr5 = percentile(hr,5)
        hr95 = percentile(hr,95)
        hg5 = percentile(hg,5)
        hg95 = percentile(hg,95)
        hb5 = percentile(hb,5)
        hb95 = percentile(hb,95)
        print 'Percentiles: R:', hr5, ':', hr95, 'G:', hg5, ':', hg95, 'B:', hb5, ':', hb95

        # Generate red, green and blue look up tables.
        table = [ mapfull(0, hr5, hr95, gamma) ]
        for i in range(1,256):
            table.append( mapfull(i, hr5, hr95, gamma) )
        for i in range(0,256):
            table.append( mapfull(i, hg5, hg95, gamma) )
        for i in range(0,256):
            table.append( mapfull(i, hb5, hb95, gamma) )

        # Map the image through the look up table.
        c = b.point( table )

        # Save the result.
        c.save( outname )
        print 'Processed OK', inname, ' -> ', outname

    except:
        print 'Failed to open/process/write', inname, ' -> ', outname

def procnegs( negscans, posscans ):
    '''Process all scanned negatives in directory negscans creating positives in
       directory posscans. Create posscans if it does not exist.
       Only create a positive if it does not already exist.'''
    if not os.access( posscans, os.F_OK ):
        try:
            os.mkdir( posscans )
        except:
            print 'Cannot create ', posscans, '.'
            return
        
    if not os.access( negscans, os.F_OK ):
        print negscans, ' does not exist.'
        return

    for n in filebits.all_files( negscans, '*.jpg' ):
        (path,name) = os.path.split( n )
        resname = os.path.join( posscans, 'positive-'+name )
        if not os.access( resname, os.F_OK ):
            colourneg( n, 1.3, resname )

    print 'Done.'

# Process ...
if __name__ == '__main__':
    procnegs( 'negscans', 'posscans' )
