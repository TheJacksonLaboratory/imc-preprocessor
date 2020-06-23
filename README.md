# IMC-preprocessor

**NOTE**: this code was recently updated and will likely update again once `imctools` v2.x is released.

This package is a simple app that handles
* Compensation of IMC images
* Simple noise filtering
* Histogram equalization for easy viewing/compositing

## Usage

This app runs in one or two stages depending on the level of control you want:
1. Feed it an MCD file and it will attempt to process it with reasonable defaults
2. Generate a configuration file from your MCD, edit the configuration file, and feed the app your config file.

### Usage - Use defaults
```{bash}
python app.py process path/to/prefix.mcd
```

### Usage - Configurable
```{bash}
python app.py config path/to/prefix.mcd
# edit prefix.yaml
python app.py process prefix.yaml
```

### Configuration format
The global processing options are as follows:
Path to the MCD file you're processing:
```{yaml}
mcdpath: /path/to/testing/prefix.mcd
```

Turn on/off the various processing steps:
```{yaml}
# true or false
do_compensate: true
do_equalization: true
do_pixel_removal: true
```

Change the output formats of each step:
```{yaml}
# tiff, tiffstack, or imc
compensate_output_type: imc 
equalization_output_type: tiff
pixel_removal_output_type: tiffstack
```
`tiff` will output individual tiffs (under their own folder), `tiffstack` will
output a single stacked tiff, and `imc` will create an `IMCFolder` from
`imctools`.

Other options:
```{yaml}
# conway or tophat
pixel_removal_method: conway
```
-   `conway` computes a binary mask and computes the number of nonzero neighbors
    within a selem around each pixel.  If this number of nonzero neighbors is
    less than a threshold, the pixel's value in this channel is set to zero.
-   `tophat` creates a mask from `binary_image - white_tophat(binary_image,
    selem)`.  Pixels masked this way will be set to zero.

Additionally, each Acquisition lists its channels and the details for each
channel.  This format allows you to change pixel removal thresholds on a
per-channel, per-acquisition basis if you need that control.  Additionally, you
can change the selem shape (default is a 3x3 square). **If you want to exclude an
acquisition from processing, delete it and all its associated channels.**


## Installation
### Running from Python

Install the necessary packages:
```bash
git clone
cd imc-preprocessor
conda create -n imcpp -f package-list.txt
```
This package requires Python 3.8+ due to usage of `typing.Literal`.

Then run:
```bash
> python app.py -h
usage: app.py [-h] {process,config} ...

optional arguments:
  -h, --help        show this help message and exit

command:
  {process,config}

> python app.py config -h
usage: app.py config [-h] mcd

positional arguments:
  mcd

optional arguments:
  -h, --help  show this help message and exit

> python app.py process -h
usage: app.py process [-h] mcd_or_yaml

positional arguments:
  mcd_or_yaml

optional arguments:
  -h, --help   show this help message and exit
```

## Building a standalone app

Create via `pyinstaller`.  Currently only tested on MacOS
```
pyinstaller --onefile --windowed app.py
```

[imctools]: https://github.com/BodenmillerGroup/imctools
