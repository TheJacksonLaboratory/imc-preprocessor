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

Use the `--verbose` flag to have substantially more informative output/logging.

### Usage - Configurable
```{bash}
# generate a configuration file for your MCD file
python app.py config path/to/prefix.mcd [-c optional/alternative/name.yaml]
# edit prefix.yaml [or optional/alternative.name.yaml]
python app.py process prefix.yaml
```

### Configuration format
Note that depending on the number of acquisitions in your MCD file, the
configuration file may be quite large; and unfortunately options are sorted
alphabetically, so we will start with describing options at the bottom.

#### Global options
-   `mcdpath`: **Required**. The full file path of the MCD file to be processed.
-   `output_prefix`: **Required**. The way all subsequent saved outputs will start.
-   `spillover_matrix_file`: *Optional* This is a full file path to an alternative
    spillover matrix CSV file.  If left as `null`, a default spillover matrix will
    be utilized.

Example:
```{yaml}
mcdpath: /path/to/testing/prefix.mcd  # this must be the full file path
output_prefix: prefix-new  # change the filename "prefix" for all output files
spillover_matrix_file: null
```

#### Processing control options
These options control what transformations are actually performed on your data.
While each operation is not required, it is required that you specify
`true`/`false` for each step.

- `do_compensation` **Required**: `true`/`false`.  Run the compensation algorithm.
- `pixel_removal_method`: **Required**: `conway`/`tophat`.  Which algorithm to
  use to removal pixels/small features on a per-channel basis.
- `do_pixel_removal` **Required**: `true`/`false`. Run the pixel removal alogrithm specified above.
- `do_equalization` **Required**: `true`/`false`. Run the equalization algorithm.

The pixel removal algorithms are detailed below.
-   `conway` computes a binary mask and computes the number of nonzero neighbors
    within a selem around each pixel.  If this number of nonzero neighbors is
    less than a threshold, the pixel's value in this channel is set to zero.
-   `tophat` creates a mask from `binary_image - white_tophat(binary_image,
    selem)`.  Pixels masked this way will be set to zero.

#### Output control options

Saving the output of each processing option is optional.  Currently you can
choose from the following output types:
-   `tiff`: A folder is made for each acqusition and individual tiffs for each
    channel are saved within that folder.
-   `tiffstack`: A single stacked tiff is made for each acqusition.
-   `text`: A single text file is made per acqusition where each column is a
    single channel and each row represents a pixel.  Note that these text files
    are not compressed and can be quite large for large scans.
-   `imc`: Save an `imctools` `IMCfolder` format.
-   `null`: Use this if you don't want output for a certain step.

Additionally, you can choose the way the output from each step is named.  The
final names will be: `<output_prefix><*_output_suffix>.aX.label.metal.ext`

-   `compensate_output_type`. `null`/`tiff`/`tiffstack`/`text`/`imc`
-   `pixel_removal_output_type`. `null`/`tiff`/`tiffstack`/`text`/`imc`
-   `equalization_output_type`. `null`/`tiff`/`tiffstack`/`text`/`imc`
-   `equalization_output_suffix`. `-equalized`
-   `compensate_output_suffix`. `-compensated`
-   `pixel_removal_output_suffix`. `-cleaned`

#### Acqusition and channel options

Additionally, each Acquisition lists its channels and the details for each
channel.  This format allows you to change pixel removal thresholds on a
per-channel, per-acquisition basis if you need that control.  You can also
change the selem shape (default is a 3x3 square).

Most importantly, **if you want to exclude an acquisition or specific channels
from processing, delete it.  In the case of acqusitions, you must delete it and
all its associated channels.**


## Installation

Install the necessary packages:
```bash
git clone
cd imc-preprocessor
conda create -n imcpp -f package-list.txt
```
This package requires Python 3.8+ due to usage of `typing.Literal`.

## Running from Python
Then run:
```bash
> python app.py -h
usage: app.py [-h] {process,config} ...

optional arguments:
  -h, --help        show this help message and exit

command:
  {process,config}

> python app.py config -h
usage: imcpp_app.py config [-h] [-v] [-c CONFIG_OUTPUT] mcd

positional arguments:
  mcd                   Path to .MCD file

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Show verbose output/logging
  -c CONFIG_OUTPUT, --config-output CONFIG_OUTPUT
                        Optional custom filename/location to save .YAML config file

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
bash scripts/build.sh
```

[imctools]: https://github.com/BodenmillerGroup/imctools
