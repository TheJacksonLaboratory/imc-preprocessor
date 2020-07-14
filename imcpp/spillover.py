#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
import pandas as pd

import importlib.resources as import_res


with import_res.path("imcpp.data","spillover.csv") as spillpath:
    SPILLMAT_CSV = Path(spillpath)


def load_spillmat():
    return pd.read_csv(SPILLMAT_CSV, index_col=0)


def align_spillmat(input_metals):
    spillmat = load_spillmat()

    unique_metals = set(spillmat.index.union(spillmat.columns))

    sm = spillmat.reindex(index=input_metals, columns=input_metals, fill_value=0)
    filled = sm.values
    np.fill_diagonal(filled, 1.0)
    return pd.DataFrame(filled, index=sm.index, columns=sm.columns)
