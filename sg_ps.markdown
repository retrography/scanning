# Scanning Using ScanGear & Photoshop

This guide explains how to make a basic negative scan, with minimum color manipulation and correction using ScanGear and Photoshop. We first use ScanGear to make a scan of an entore film strip with film base color canceled. Then we use photoshop to invert the colors in a way that cross-channel color relations are preserved.

First we have to make sure the configuration is correct.

1) Before launching ScanGear from CanoScan launcher, make sure "Enable large images scans" is checked in ScanGear settings.

![01genset](assets/01genset.png)

2) After running ScanGear, launch the Preferences window and move to "Scan" tab. Make sure "Enable 48/16 bit output" is selected.

![02prefs](assets/02prefs.png)

3) Move to "Color Settings" tab. Check "None" as your color management methods of choice. Press "OK" and go back to the scan window. 

![03prefs](assets/03prefs.png)

4) Switch to advanced mode and select "Color Positive Mode" as your source. We choose the positive mode because we do not want ScanGear to do the color inversion for us. Set color mode to "Color (48 bit)". Make sure "Unsharp Mask" and "Grain Correction" are off. It is fine if you want to leave Dust and Scratch Removal on. Also make sure "Manual Exposure" is not selected.  

![04scnmd](assets/04scnmd.png)

5) Now select the whole strip of film you intend to scan. Do your best not to exclude the negative holder. Now press the histogram button.

![05slcpre](assets/05slcpre.png)

In histogram window select the color channels one by one (green, blue, read) and set the white point and the black point for each. Do not do this on all channels combined or on the luminosity channel, because the channels need to be calibrated separately. In order to set the white point and the black point of the image 

![06histog](assets/06histog.png)

![07slcpst](assets/07slcpst.png)

![08asnpfl](assets/08asnpfl.png)

![09asnpfl](assets/09asnpfl.png)

![10slcpre](assets/10slcpre.png)

![11levels](assets/11levels.png)

![12levels](assets/12levels.png)

![13levels](assets/13levels.png)

![14slcpst](assets/14slcpst.png)

![15invert](assets/15invert.png)

![16final](assets/16final.png)

