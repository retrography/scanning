#!/usr/bin/env ruby

require 'RMagick'
include Magick
require 'date'
require 'getopt/std'
require 'FileUtils'


$basename=DateTime.now.strftime('%Y-%m-%d_%H%M%S')
$format='tiff'
$monochrome=false
$infrared=false
$filmtype='135'
$resolution='4800'

# Look for -o with argument, and -I and -D boolean arguments

opt = Getopt::Std.getopts("r:f:o:t:mi")

$format = opt["f"] if opt["f"]
$filmtype = opt["t"] if opt["t"]
$resolution = opt["r"] if opt["r"]
$basename = opt["o"] if opt["o"]
$monochrome = true if opt["m"]
$infrared = true if opt["i"]

$resolution = $resolution.to_i
$crop_threshold=$resolution/120 #should vary based on dpi...
$crop_factor= case $resolution
                when 1200 then
                  2
                when 2400 then
                  2
                when 4800 then
                  2
                else
                  1
              end

class Scaneg

  def self.upper_limit(vertical_image, ymin)
    counter=ymin
    vertical_lower_bound = ymin
    lower_color_threshold = 16*256
    loop do
      lower_pixel=vertical_image.pixel_color(0, counter)

      if lower_pixel.intensity >= lower_color_threshold
        vertical_lower_bound=counter
        break
      end

      counter+=1
    end
    return vertical_lower_bound
  end

  def self.lower_limit(vertical_image, ymax)
    counter=ymax
    vertical_higher_bound = ymax
    lower_color_threshold = 16*256
    loop do
      higher_pixel=vertical_image.pixel_color(0, counter)

      if higher_pixel.intensity >= lower_color_threshold
        vertical_higher_bound=counter
        break
      end

      counter-=1
    end
    return vertical_higher_bound
  end

  def self.left_limit(horizontal_image, xmin)
    counter=xmin
    horizontal_lower_bound = xmin
    lower_color_threshold = 16*256
    #upper_color_threshold = 256**2-lower_color_threshold
    loop do
      leftmost_pixel=horizontal_image.pixel_color(counter, 0)

      if leftmost_pixel.intensity >= lower_color_threshold #and leftmost_pixel.intensity <= upper_color_threshold
        horizontal_lower_bound=counter
        break
      end

      counter+=1
    end
    return horizontal_lower_bound
  end

  def self.right_limit(horizontal_image, xmax)
    counter=xmax
    horizontal_higher_bound = xmax
    lower_color_threshold = 16*256
    #upper_color_threshold = 256**2-lower_color_threshold
    loop do
      rightmost_pixel=horizontal_image.pixel_color(counter, 0)

      if rightmost_pixel.intensity >= lower_color_threshold #and rightmost_pixel.intensity <= upper_color_threshold
        horizontal_higher_bound=counter
        break
      end

      counter-=1
    end
    return horizontal_higher_bound
  end

  def self.right_white_limit(image, xmax=image.columns)
    horizontal_image = image.resize(image.columns, 1)
    counter=xmax
    horizontal_higher_bound = xmax
    lower_color_threshold = 16*256
    upper_color_threshold = 256**2-lower_color_threshold
    loop do
      rightmost_pixel=horizontal_image.pixel_color(counter, 0)

      if rightmost_pixel.intensity >= lower_color_threshold and rightmost_pixel.intensity <= upper_color_threshold

        horizontal_higher_bound=counter
        break

      end
      counter-=1
    end

    if horizontal_higher_bound != xmax

      horizontal_higher_bound = right_white_limit(image, counter - 2*$crop_threshold)
    end

    return horizontal_higher_bound

  end

  def self.vertical_limits(image, ymin=0, ymax=image.rows)
    image_verticalized=image.resize(1, image.rows)
    return upper_limit(image_verticalized, ymin), lower_limit(image_verticalized, ymax)
  end

  def self.horizontal_limits(image, xmin=0, xmax=image.columns)
    image_horizontalized=image.resize(image.columns, 1)
    return left_limit(image_horizontalized, xmin), right_limit(image_horizontalized, xmax)
  end

  def self.scan(mode)

    filename="#{$basename}_#{mode}.#{$format}"

    scan_command = "scanimage --device-name pixma:04A9190D \
    --source 'Transparency Unit' \
    --resolution #{$resolution} \
    --format #{$format} \
    --mode #{mode} \
    -l 76 -x 66 \
    > #{filename} 2>/dev/null"

    system(scan_command)

    return filename

  end

  def self.crop135(image)

    case $resolution
      when 1200
        strip1 = image.crop(0, 925/2, 1250/2, 10850/2, true).rotate(270)
        strip2 = image.crop(1855/2, 925/2, 1250/2, 10850/2, true).rotate(270)
      when 2400
        strip1 = image.crop(0, 1850/2, 2500/2, 21700/2, true).rotate(270)
        strip2 = image.crop(3710/2, 1850/2, 2500/2, 21700/2, true).rotate(270)
      when 4800
        strip1 = image.crop(0, 37003/$crop_factor, 5000/$crop_factor, 43400/$crop_factor, true).rotate(270)
        strip2 = image.crop(7420/$crop_factor, 3700/$crop_factor, 5000/$crop_factor, 43400/$crop_factor, true).rotate(270)

    end
    return strip1, strip2

  end

  def self.trim(image)
    y1, y2 = Scaneg.vertical_limits(image)
    image.crop!(0, y1+$crop_threshold, image.columns, y2-y1-2*$crop_threshold, true)
    x1, x2 = Scaneg.horizontal_limits(image)
    image.crop!(x1+$crop_threshold, 0, x2-x1-2*$crop_threshold, image.rows, true)

    width = Scaneg.right_white_limit(image)

    image.crop!(0, 0, width+$crop_threshold, image.rows, true)
    return image, x1, width, y1, y2
  end

  def self.compose_ir(image, ir)
    image, x1, x2, y1, y2 = trim(image)

    # this should be fixed both for the b strip of 35mms and for 120s

    ir.resize!(ir.columns, ir.rows-($resolution/100/$crop_factor).to_i)
    ir.crop!(x1+$crop_threshold+($resolution/300/$crop_factor).to_i, y1+$crop_threshold, x2+$crop_threshold, y2-y1-2*$crop_threshold, true)

    ir.matte = false
    image.matte = true

    image.composite!(ir, Magick::CenterGravity, Magick::CopyOpacityCompositeOp)
    return image
  end

  def self.bin(filename)

    #image.resize!((image.columns/$crop_factor).to_int, (image.rows/$crop_factor).to_int, Magick::BoxFilter, 1)
    newfilename="bin_" + filename
    scale_factor=(100.0/$crop_factor).round(2).to_s+"%"
    resize_command="convert #{filename} -filter box -resize #{scale_factor}% -compress zip #{newfilename}"
    system(resize_command)
    FileUtils.rm(filename)
    return newfilename
  end

  def self.invert(filename1, filename2="")
    invert_command="negfix8p -ir -cs #{filename1} #{filename2}"
    system(invert_command)
    return "P_#{filename1}", "P_#{filename2}"
  end


  def self.do135
    if ($monochrome)
      imagefile=Scaneg.scan('grayscale')
    else
      #imagefile=Scaneg.scan('color')
      imagefile="/Volumes/Content/Temp/newscan/bin_2014-12-03_030205_color.tiff"
    end

    if ($infrared)
      #irfile=Scaneg.scan('infrared')
      #irfile = Scaneg.bin(irfile)
      irfile = "/Volumes/Content/Temp/newscan/bin_2014-12-03_030205_infrared.tiff"
    end

    #imagefile = Scaneg.bin(imagefile)

    images = Image.read(imagefile).first
    image1, image2 = Scaneg.crop135(images)
    images = nil;

    if ($infrared)
      irs = Image.read(irfile).first
      ir1, ir2 = Scaneg.crop135(irs)
      irs=nil

      image1 = Scaneg.compose_ir(image1, ir1)
      image2 = Scaneg.compose_ir(image2, ir2)
    else
      image1 = trim(image1)
      image2 = trim(image2)
    end

    image1.write("#{$basename}_a.#{$format}")
    image2.write("#{$basename}_b.#{$format}")
    invert("#{$basename}_a.#{$format}","#{$basename}_b.#{$format}")
  end

  def self.do120
    if ($monochrome)
      imagefile=Scaneg.scan('grayscale')
    else
      imagefile=Scaneg.scan('color')
    end

    if ($infrared)
      irfile=Scaneg.scan('infrared')
      irfile = Scaneg.bin(irfile)
    end

    imagefile = Scaneg.bin(imagefile)

    image = Image.read(imagefile).first

    if ($infrared)
      ir = Image.read(irfile).first
      image = Scaneg.compose_ir(image, ir)
    else
      image = trim(image)
    end

    image.write("#{$basename}.#{$format}")
  end

  def self.do
    do135 if ($filmtype == '135')
    do120 if ($filmtype == '120')
  end
end


Scaneg.do




