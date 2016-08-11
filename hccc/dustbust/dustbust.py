""" 
dustbust.py - Very simple dust/dirt removal program.
====================================================

Also needs: pilc.cpp (compiled/linked to ./pilc.so)

Nick Glazzard, 2014
"""

import Image
import ImageFilter
import ImageDraw
import os
import fnmatch, stat
import argparse
import time
from numpy import *
from ctypes import *

def all_files( root, patterns='*', single_level=False, yield_folders=False ):
    patterns = patterns.split( ';' )
    for path, subdirs, files in os.walk( root ):
        if yield_folders:
            files.extend( subdirs )
        files.sort()
        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch( name, pattern ):
                    yield os.path.join( path, name )
                    break
        if single_level:
            break

def create_folder_if_not_exists( path ):
    '''Create a folder if it does not exist.'''
    if not os.access( path, os.F_OK ):
        try:
            os.mkdir( path )
        except:
            print 'Cannot create folder %s' % path

class MyGaussianBlur(ImageFilter.Filter):
    """Hack to allow non-default gaussian blur radii with PIL."""
    name = "GaussianBlur"
    def __init__(self, radius=2):
        self.radius = radius
    def filter(self, image):
        return image.gaussian_blur(self.radius)

def thresh(p):
    """Threshold 1 channel pixel value p."""
    if p > 0: # Trying to dilate!
        return 255
    else:
        return 0

def mode_channels(mode):
    """Return the number of channels for an image with mode."""
    if mode == 'RGB':
        return 3
    elif mode == 'RGBA':
        return 4
    elif mode == 'L':
        return 1
    else:
        return 1
                        
if __name__ == '__main__':
    print '==========================================================================='
    print 'dustbust.py - Very simple dust removal program for scanned positive images.'
    print '==========================================================================='
    parser = argparse.ArgumentParser()
    parser.add_argument("start_name", help="Name of first image to process.")
    parser.add_argument("end_name", help="Name of last image to process.")
    parser.add_argument("mask_name", help="Name of mask image to create or use.")
    parser.add_argument("-m", "--makemask", help="Estimate the dust mask.", action="store_true")
    args = parser.parse_args()
    start_time = time.time()
    start_image = args.start_name #'posscans/positive-2014-04-27-181041.jpg'
    end_image = args.end_name #'posscans/positive-2014-04-27-191411.jpg'
    mask_image = args.mask_name #'group1.jpg'
    inputspath, junkname = os.path.split(start_image)

    # Estimate the dust mask case.
    if args.makemask:
        print 'Estimating a dust mask.'
        print '-----------------------'
        first = True
        imnum = 0 
        running = False
        # Average a chunk of frames chosen to have similar dust patterns.
        for n in all_files( inputspath, '*.jpg' ):
            if n == start_image:
                running = True
            if n == end_image:
                break
            if running:
                imnum += 1
                print 'INFO: Adding in:',n
                a = Image.open( n )
                f = array(a) # convert PIL image to Numpy array.
                if first:
                    s = zeros(f.shape,dtype=float) # float sum array.
                    first = False
                s += f # Add this 8 bit image to float sum.
        print 'INFO: Added in:',imnum,'images.'
        print 'INFO: Max value before scaling is:',amax(s)
        ss = s * (255.0/amax(s)) # Scaled sum.
        # Find a heavily blurred version of the average to get a background estimate.
        # N.B. The blur itself is rather slow ...
        print 'INFO: Estimating background (slow).'
        oi = Image.fromarray(ss.astype(uint8)) # back to 8 bit
        boi = oi.filter(MyGaussianBlur(radius=50)) # blur
        # Find the absolute value of the average - background.
        # This largely removes the "slow" background variations (with luck).
        print 'INFO: Removing background.'
        fboi = array(boi,dtype=float) # back to float
        soi = absolute(ss - fboi) # Abs(scaled sum - background)
        ssoi = soi * (255.0/amax(soi)) # Scale that back to full 8 bit range.
        issoi = Image.fromarray(ssoi.astype(uint8)) # Convert 8 bit Numpy array back to PIL image.
        # Set regions near the edges to zero to avoid edge problems.
        # Say top and bottom 4%
        print 'INFO: Trimming edges.'
        draw = ImageDraw.Draw(issoi)
        w,h = issoi.size
        ytrim = int(0.04*h)
        draw.polygon([(0,0),(w-1,0),(w-1,ytrim),(0,ytrim)],fill='black')
        draw.polygon([(0,h-ytrim),(w-1,h-ytrim),(w-1,h-1),(0,h-1)],fill='black')
        issoi.save(mask_image)
        print 'INFO: Wrote mask:',mask_image
        print 'Please threshold this manually using GIMP etc.'

    # Apply the dust mask case.
    else:
        print 'Applying a dust mask.'
        print '---------------------'
        print 'INFO: Create cleanedphotos folder.'
        create_folder_if_not_exists( 'cleanedphotos' )
        mask = Image.open(mask_image)
        lmask = mask.convert('L') # Make sure it is a 1 channel luma image.
        # Dilate it a bit.
        print 'INFO: Dilating mask.'
        dlmask = lmask.filter(MyGaussianBlur(radius=5)) # blur
        dlmask.point(thresh) # threshold
        print 'INFO: Softening mask.'
        bdlmask = lmask.filter(MyGaussianBlur(radius=2)) # blur again to give soft edges
        # Ensure all the edges has a black border.
        print 'INFO: Trimming mask edges.'
        draw = ImageDraw.Draw(bdlmask)
        w,h = bdlmask.size
        ytrim = int(0.04*h)
        draw.polygon([(0,0),(w-1,0),(w-1,ytrim),(0,ytrim)],fill='black')
        draw.polygon([(0,h-ytrim),(w-1,h-ytrim),(w-1,h-1),(0,h-1)],fill='black')
        xtrim = int(0.02*w)
        draw.polygon([(0,0),(xtrim,0),(xtrim,h-1),(0,h-1)],fill='black')
        draw.polygon([(w-xtrim,0),(w-1,0),(w-1,h-1),(w-xtrim,h-1)],fill='black')
        # bdlmask.save('bdlmask.jpg')
        # Open a shared object containing C functions we will need to call.
        lib = cdll.LoadLibrary( './pilc.so' )
        # Process the frames
        running = False
        imnum = 0
        for n in all_files( inputspath, '*.jpg' ):
            if n == start_image:
                running = True
            if n == end_image:
                break
            if running:
                imnum += 1
                print 'INFO: Processing:',n
                # Read the input (dirty) image and make a copy of it.
                dirty = Image.open( n )
                w,h = dirty.size
                c = mode_channels(dirty.mode)
                dirtycopy = dirty.copy()
                # Where the (dilated) mask is not 0 (i.e. in the dirt),
                # find a colour to fill the dirty bit with by averaging nearby pixels
                # that are not in the dirt (i.e. have mask==0). Do this repeatedly
                # until all dirty pixels have been filled. For performance reasons,
                # this low level pixel munging must be done by calling a C function
                # that does the hard work.
                dirtypixels = dirty.tostring()
                rawdirty = cast(dirtypixels, POINTER(c_ubyte*c*w*h)) # Input image data.
                maskpixels = bdlmask.tostring()
                rawmask = cast(maskpixels, POINTER(c_ubyte*w*h)) # Dilated mask data.
                resultpixels = (c_ubyte*w*h*c)() # Buffer to hold result of conditional blur.
                tmaskpixels = (c_ubyte*w*h)() # Buffer to hold temporary mask (which is modified).
                radius = 3 # Blur radius at each pass.
                maxpasses = 8 # Maximum number of passes.
                lib.condblur(byref(resultpixels), rawdirty, rawmask, byref(tmaskpixels), \
                                 c_int(w), c_int(h), c_int(c), c_int(radius), c_int(maxpasses) )
                # Make an image with the filled dirty bits (only).
                dirtyfilled = Image.fromstring('RGB',(w,h),resultpixels)
                # dirtyfilled.save('resultsave.jpg')
                # Composite dirty and dirtyfilled using the softened, dilated mask.
                result = Image.composite(dirtyfilled,dirty,bdlmask)
                # Save the result.
                inpath, imname = os.path.split(n)
                outimage = os.path.join('cleanedphotos',imname)
                result.save(outimage)                
                
        print 'INFO: Processed',imnum,'image(s).'
    # Finished.
    elapsed_time = time.time() - start_time
    elapsed_mins = int(elapsed_time) / 60
    elapsed_secs = elapsed_time - ( 60 * elapsed_mins )
    print 'INFO: Processing took:',elapsed_mins,'minutes',int(10.0*elapsed_secs)/10.0,'seconds.'
    print 'Done.'
