#!/usr/bin/env bash

dask_file="$(which python)/../../lib/python3.8/site-packages/dask/dask.yaml:./dask"
spill_file='/Users/flynnb/local/anaconda3/envs/imc/lib/python3.8/site-packages/imcpp/data/spillover.csv:imcpp/data'

pyinstaller \
  --onefile \
  --add-data $dask_file \
  --add-data $spill_file \
  --hidden-import="skimage.feature._orb_descriptor_positions" \
  --hidden-import="imcpp.data" \
  imcpp_app.py
  #--add-data "imcpp/data/spillover.csv:./imcpp.data" \
