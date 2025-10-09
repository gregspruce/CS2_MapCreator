@"./../ImageMagick_7.0.5-7_portable_Q16_x64_stripped/convert.exe" heightmap.tif -set colorspace RGB -channel R -separate +channel -quality 90 %1
@rem "./../ImageMagick_7.0.5-7_portable_Q16_x64_stripped/convert.exe" heightmap.tif -verbose info:
@rem "./../ImageMagick_7.0.5-7_portable_Q16_x64_stripped/convert.exe" outfile.png -verbose info:
@rem @pause