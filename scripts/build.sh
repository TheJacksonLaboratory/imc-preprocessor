#!/usr/bin/env bash

dask_file="$(which python)/../../lib/python3.8/site-packages/dask/dask.yaml:./dask"

pyinstaller \
  --onefile \
  --add-data $dask_file \
  imc-preprocessor/app.py
