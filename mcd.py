#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
from skimage.filters import gaussian
from skimage.restoration import denoise_tv_chambolle
from skimage.exposure import equalize_adapthist
from imctools.io.mcdparser import McdParser
from imctools.io.abstractparserbase import AcquisitionError
from imctools.io.imcfolderwriter import ImcFolderWriter


class MCD:
    def __init__(self, mcdpath: Path):
        self.mcdpath = mcdpath
        self.imc_name = mcdpath.stem
        self.acquisitions = {}

    @staticmethod
    def _get_acquisition(mcd, ac_id):
        try:
            imc_ac = mcd.get_imc_acquisition(ac_id)
        except AcquisitionError as e:
            imc_ac = None
        return imc_ac

    def load_acquisitions(self):
        print("Loading acquisitions.  Make take some time...")
        for ac_id in self.mcd.acquisition_ids:
            imc_ac = self._get_acquisition(self.mcd, ac_id)
            if imc_ac is None:
                continue
            self.acquisitions[ac_id] = imc_ac
        print("Acqusitions loaded.")

    def peek(self):
        print(f"Peeking into MCD file {self.mcdpath}")
        self.mcd = McdParser(str(self.mcdpath))
        print("MCD loaded. Peeking started.")
        self.acquisition_ids = self.mcd.acquisition_ids
        self.offsets = {}
        self.n_channels = {}
        self.channel_metals = {}
        self.channel_labels = {}
        for ac_id in self.acquisition_ids:
            metals, labels = list(zip(*self.mcd.get_acquisition_channels(ac_id).values()))
            offset = len(metals) - len(set(metals) - set("XYZ"))
            self.offsets[ac_id] = offset
            self.channel_labels[ac_id] = labels[offset:]
            self.channel_metals[ac_id] = metals[offset:]
            self.n_channels[ac_id] = len(metals[offset:])
        print("Peeking finished.")

        
    def load_mcd(self):
        self.fileprefix = self.mcdpath.stem
        self.peek()
        self.load_acquisitions()

        self.n_acquisitions = len(self.acquisitions)

    def get_data(self, ac_id, ch_int=None):
        imc_ac = self.acquisitions.get(ac_id)
        offset = imc_ac._offset
        if ch_int is not None:
            return imc_ac._data[offset + ch_int]
        return imc_ac._data[offset:]

    def set_data(self, new_data, ac_id, ch_int=None):
        imc_ac = self.acquisitions.get(ac_id)
        offset = imc_ac._offset
        if ch_int is not None:
            imc_ac._data[offset + ch_int] = new_data
        else:
            assert len(new_data.shape) == 3
            imc_ac._data[offset:] = new_data

    def _write_imcfolder(self, suffix):
        outpath = Path(self.fileprefix + suffix)
        if not outpath.exists():
            outpath.mkdir(exist_ok=True)

        self.mcd.save_meta_xml(str(outpath))
        ifw = ImcFolderWriter(str(outpath), mcddata=self.mcd)
        ifw.write_imc_folder()
        print(f"IMC-Folder written to {str(outpath)}")

    def _write_tiff(self, suffix):
        fmt = "{}{}.a{}.{}.{}.ome.tiff"
        for ac_id, imc_ac in self.acquisitions.items():
            for k, (metal, label) in enumerate(
                zip(imc_ac.channel_metals, imc_ac.channel_labels)
            ):
                tiff = fmt.format(self.fileprefix, suffix, ac_id, metal, label)
                iw = imc_ac.get_image_writer(filename=str(tiff), metals=[metal])
                iw.save_image(mode="ome", compression=0, dtype=None, bigtiff=False)
                print(f"{tiff} saved.")

    def _write_tiffstack(self, suffix):
        fmt = "{}{}.a{}.ome.tiff"
        for ac_id, imc_ac in self.acquisitions.items():
            tiff = fmt.format(self.fileprefix, suffix, ac_id)
            iw = imc_ac.get_image_writer(filename=str(tiff))
            iw.save_image(mode="ome", compression=0, dtype=None, bigtiff=False)
            print(f"{tiff} saved.")

    def save(self, output_format, suffix=""):
        save_funcs = {
            "imc": self._write_imcfolder,
            "tiff": self._write_tiff,
            "tiffstack": self._write_tiffstack,
        }
        save_funcs[output_format](suffix)
