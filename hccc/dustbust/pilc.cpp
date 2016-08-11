// pilc.cpp - Sundry image processing functions for PIL callable from Python.
// ==========================================================================
//
// Nick Glazzard 2014
// ------------------

#include <stdio.h>
#include <string.h>

typedef unsigned char u8;

// Give everything C linkage so the can be accessed via ctypes from Python.
// Note this means polymorphic functions cannot be declared (in this section).
extern "C" {

  // Test passing images to and from Python in PIL format.
  void testproc(u8* result, u8* data, int w, int h, int c)
  {
    printf("w=%d, h=%d, c=%d, result=%p, data=%p\n",w,h,c,result,data);
    memcpy(result,data,w*h*c);

    // Draw a filled green-ish rectangle.
    for( int y=(int)(0.1*h); y<(int)(0.3*h); y++ ){
      u8* lp = result + y * c * w;
      for( int x=(int)(0.4*w); x<(int)(0.5*w); x++ ){
	u8* pp = lp + x * c;
	pp[0] = 100;
	pp[1] = 200;
	pp[2] = 50;
      }
    }
  }

  // Zero the pixel value in *op.
  static inline void zeropixel(u8* op, int c )
  {
    for( int o=0; o<c; o++ )
      op[o] = 0;
  }

  // Copy the pixel value in *ip to *op.
  static inline void setpixel(u8* op, u8* ip, int c )
  {
    for( int o=0; o<c; o++ )
      op[o] = ip[o];
  }

  // Set the pixel value at image(x,y) to *ip.
  static inline void isetpixel(u8* image, u8* ip, int x, int y, int w, int h, int c )
  {
    u8* pixp = image + c * ( x + y * w );
    setpixel( pixp, ip, c );
  }

  // Get the pixel value at image(x,y).
  static inline void igetpixel(u8* op, u8* image, int x, int y, int w, int h, int c )
  {
    u8* pixp = image + c * ( x + y * w );
    setpixel( op, pixp, c );
  }

  // Min of i and lo.
  static inline int imin( int i, int lo )
  {
    return (lo < i) ? lo : i ;
  }

  // Max of i and hi.
  static inline int imax( int i, int hi )
  {
    return (hi > i) ? hi : i ;
  }

  // Clamp i to [lo:hi].
  static inline int iclamp( int i, int lo, int hi )
  {
    return imax(lo,imin(i,hi));
  }

  // Fill inside the mask along lines only. use simple linear interpolation of end pixels.
  // Unfortunately, line like artefacts are too visible with this method.
  void patchlines(u8* result, u8* data, u8* mask, int w, int h, int c)
  {
    printf("w=%d, h=%d, c=%d, result=%p, data=%p\n",w,h,c,result,data);
    u8 b[4], e[4], d[4];

    // Over all the lines.
    for( int y=0; y<h; y++ ){
      u8* op = result + y * c * w;
      u8* ip = data + y * c * w;
      u8* mp = mask + y * w;

      // Along current line.
      for( int x=0; x<w; x++ ){

	// Mask is zero. Copy pixel.
	if( mp[x] == 0 ){
	  setpixel(&op[x*c],&ip[x*c],c);
	}

	// Mask has transitioned to non-zero. Record the colour of the preceeding input pixel.
	else{
	  int xb = x;
	  int xbp = xb - 1;
	  if( xbp < 0 )xbp = 0; // Should never happen as mask should have zero at edges.
	  setpixel(b,&ip[xbp*c],c);

	  // Look for the mask transitioning back to 0. Record the colour of that input pixel.
	  for( ; x<w; x++){
	    if( mp[x] == 0 ){
	      int xe = x;
	      int n = x - xbp;
	      setpixel(e,&ip[xe*c],c);

	      // Fill the output run between xb and xe, ignoring the input.
	      for( int o=0; o<c; o++ )
		d[o] = ( e[o] - b[o] ) / n;
	      for( int xf=xb; xf<xe; xf++ ){
		setpixel(&op[xf*c],b,c);
		for( int o=0; o<c; o++ )
		  b[o] += d[o];
	      }

	      // Remember to set the pixel at which mask went back to zero.
	      setpixel(&op[xe*c],&ip[xe*c],c);
	      // Stop skipping input.
	      break;
	    } // Non-zero mask transition.
	  } // Skipping input run. 
	} // Mask transitioned to non-zero.

      } // Over x
    } // Over y
  } // patchlines()

  // Find the average pixel value in a box x-r:x+r x y-r:y+r using pixels where mask(x,y) == 0.
  // If no pixel in the box has a zero mask, return false and leave tmask and op unchanged.
  // Otherwise, return true, set tmask(x,y) = 0, and set op
  static inline bool condblurbox(u8* result, u8* image, u8* mask, u8* tmask, int x, int y, int w, int h, int c, int r)
  {
    u8 v[4];
    int sum[4];

    // Check bounds.
    int ymin = imax(0,y-r);
    int ymax = imin(h-1,y+r);
    int xmin = imax(0,x-r);
    int xmax = imin(w-1,x+r);

    // Zero sum.
    int npix = 0;
    for( int p=0; p<c; p++ )
      sum[p] = 0;

    // Over the box area.
    for( int yc=ymin; yc<=ymax; yc++ ){
      for( int xc=xmin; xc<=xmax; xc++ ){

	// (mask==0) so add in this box pixel.
	if( mask[xc+yc*w] == 0 ){
	  igetpixel(v, image, xc, yc, w, h, c);
	  for(int p=0; p<c; p++)
	    sum[p] += v[p];
	  ++npix;
	}
      }
    }

    // Form the average if possible.
    if( npix > 0 ){
      for(int p=0; p<c; p++)
	v[p] = (u8)( sum[p] / npix );
      isetpixel(result, v, x, y, w, h, c);
      tmask[x+y*w] = 0;
      return true;
    }

    // No pixels in the box had (mask==0).
    else
      return false;
  } // condblurbox()

  // Conditional blur pass. Return the number of pixels in result that were not filled.
  int condblurpass(u8* result, u8* data, u8* mask, u8* tmask, int w, int h, int c, int r)
  {
    // Save mask in tmask. tmask is modified here.
    memcpy(tmask,mask,w*h);

    // Count the number of fill failures.
    int nfail = 0;

    // Over all the lines.
    for( int y=0; y<h; y++ ){

      // Along current line.
      for( int x=0; x<w; x++ ){

	// If mask(x,y) != 0:
	// Fill in result(x,y) with the conditional (mask==0) blur of data(x-r:x+r,y-r:y+r).
	// This modifies tmask. If result(x,y) was not filled (because there
	// were no pixels in the blur box where (mask==0) at (x,y)), bump nfail.
	if( mask[x+y*w] != 0 ){
	  if( ! condblurbox( result, data, mask, tmask, x, y, w, h, c, r) )
	    ++nfail;
	}
      } // over x
    } // over y

    return nfail;
  } // condblurpass()
  
  // Conditional blur. Blur data to result using only pixels where (mask==0). Do this in
  // repeated passes (modifying data and mask as well as result) until (mask==0) everywhere,
  // or more than maxpass passes have been attempted. Return 1 if OK. If maxpass passes were
  // not enough, return 0.
  int condblur( u8* result, u8* data, u8* mask, u8* tmask, int w, int h, int c, int r, int maxpass )
  {
    int nfail = 0;

    // Iterate over passes.
    for( int ipass=0; ipass<=maxpass; ipass++ ){
      nfail = condblurpass( result, data, mask, tmask, w, h, c, r );
      if( nfail == 0 || ipass == maxpass )
	break;

      // Set up for next pass. Set data=result and mask=tmask.
      memcpy(data,result,w*h*c);
      memcpy(mask,tmask,w*h);
    }

    // See if all pixels were filled OK.
    if( nfail == 0)
      return 1;
    else
      return 0;
  } // condblur()
}
