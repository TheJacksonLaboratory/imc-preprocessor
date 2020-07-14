#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
import pandas as pd

#from pkg_resources import resource_filename, Requirement


SPILLMAT_CSV = Path("./spillover.csv")
#SPILLMAT_CSV = Path(resource_filename(
#    Requirement.parse("imc-preprocessor"),
#    "data/spillmat.csv"
#))


def load_spillmat():
    return pd.read_csv(SPILLMAT_CSV, index_col=0)


def align_spillmat(input_metals):
    spillmat = load_spillmat()

    unique_metals = set(spillmat.index.union(spillmat.columns))

    sm = spillmat.reindex(index=input_metals, columns=input_metals, fill_value=0)
    filled = sm.values
    np.fill_diagonal(filled, 1.0)
    return pd.DataFrame(filled, index=sm.index, columns=sm.columns)
