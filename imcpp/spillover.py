#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
import pandas as pd

import importlib.resources as import_res


with import_res.path("imcpp.data","spillover.csv") as spillpath:
    SPILLMAT_CSV = Path(spillpath)


def load_spillmat(infile=None):
    if not infile:
        infile=SPILLMAT_CSV
    return pd.read_csv(infile, index_col=0)


def align_spillmat(spillmat, input_metals):

    unique_metals = set(spillmat.index.union(spillmat.columns))

    sm = spillmat.reindex(index=input_metals, columns=input_metals, fill_value=0)
    filled = sm.values
    np.fill_diagonal(filled, 1.0)
    return pd.DataFrame(filled, index=sm.index, columns=sm.columns)
