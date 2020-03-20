# IMC-preprocessor

This is a quick and dirty extension to [imctools][imctools] that, given an input
MCD file:
-   Exports raw per-channel tiffs
-   Exports percentile clipped and/or smoothed tiff stacks and per-channel tiffs
-   Exports heavily smoothed tiff stacks for segmentation

Help make this better!

## Running from Python

Install the necessary packages:
```bash
git clone
cd imc-preprocessor
conda create -n imcpp -f package-list.txt
```

Then run:
```bash
> python mcdconverter.py -h
usage: mcdconverter.py [-h] [-o OUTDIR] [-b CLIP_BLUR_RADIUS]
                       [-s SEGMENTATION_BLUR_RADIUS] [--clip-min CLIP_MIN]
                       [--clip-max CLIP_MAX]
                       mcdfile
mcdconverter.py: error: the following arguments are required: mcdfile
```

## Running via the GUI
```bash
> python imcpp.py
```

## Building a standalone app

Create via `pyinstaller`.  Currently only tested on MacOS
```
pyinstaller --onefile --windowed imcpp.py
```

[imctools]: https://github.com/BodenmillerGroup/imctools
