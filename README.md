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

## Installation
### Running from Python

Install the necessary packages:
```bash
git clone
cd imc-preprocessor
conda create -n imcpp -f package-list.txt
```

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
