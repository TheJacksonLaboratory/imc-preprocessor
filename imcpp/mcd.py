#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
import pandas as pd
from imctools.io.mcdparser import McdParser
from imctools.io.abstractparserbase import AcquisitionError
from imctools.io.imcfolderwriter import ImcFolderWriter
from xml.etree import cElementTree as ElementTree

from .logger import logger


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
        logger.debug("Loading acquisitions.  Make take some time...")
        for ac_id in self.mcd.acquisition_ids:
            imc_ac = self._get_acquisition(self.mcd, ac_id)
            if imc_ac is None:
                continue
            #imc_ac.original_metadata = ElementTree.fromstring(imc_ac.original_metadata)
            #imc_ac.original_metadata = imc_ac.original_metadata.decode("ascii")
            self.acquisitions[ac_id] = imc_ac
        logger.info(f"{len(self.acquisitions)} acquisitions loaded.")

    def peek(self):
        logger.info(f"Going to peek inside MCD file {self.mcdpath}")
        logger.debug("Loading MCD.")
        self.mcd = McdParser(str(self.mcdpath))
        logger.debug("MCD loaded. Peeking started.")
        acquisition_ids = self.mcd.acquisition_ids
        self.acquisition_ids = []
        self.offsets = {}
        self.n_channels = {}
        self.channel_metals = {}
        self.channel_labels = {}
        for ac_id in acquisition_ids:
            ac = self.mcd.meta.get_acquisitions()[ac_id]
            if ac.data_offset_end - ac.data_offset_start < 1e5:
                logger.warn(f"Acquisition {ac_id} appears empty.  Skipping.")
                continue

            metals, labels = list(zip(*self.mcd.get_acquisition_channels(ac_id).values()))
            metals = [m.replace("(", "").replace(")", "") for m in metals]
            offset = len(metals) - len(set(metals) - set("XYZ"))
            self.offsets[ac_id] = offset
            self.channel_labels[ac_id] = labels[offset:]
            self.channel_metals[ac_id] = metals[offset:]
            self.n_channels[ac_id] = len(metals[offset:])
            self.acquisition_ids.append(ac_id)
        logger.debug("Peeking finished.")

    def load_mcd(self):
        self.fileprefix = self.mcdpath.stem
        self.peek()
        self.load_acquisitions()

        self.n_acquisitions = len(self.acquisitions)

    def get_xyz_data(self, ac_id):
        imc_ac = self.acquisitions.get(ac_id)
        return imc_ac._data[:3]

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

    def _write_imcfolder(self, acquisitions, prefix, suffix):
        raise NotImplementedError("This is broken")
        logger.debug(f"Saving IMCfolder with prefix:[{prefix}] and suffix:[{suffix}]")
        # TODO:This doesn't utilize acquisitions yet
        outpath = Path(prefix + suffix)
        if not outpath.exists():
            outpath.mkdir(exist_ok=True)

        self.mcd.save_meta_xml(str(outpath))
        ifw = ImcFolderWriter(str(outpath), mcddata=self.mcd)
        ifw.write_imc_folder()
        logger.info(f"IMC-Folder written to {str(outpath)}")

    def _write_tiff(self, acquisitions, prefix, suffix):
        logger.debug(f"Saving tiffs with prefix:[{prefix}] and suffix:[{suffix}]")
        outpath = Path(prefix + suffix)
        if not outpath.exists():
            outpath.mkdir(exist_ok=True)
        for ac_id in acquisitions.keys():
            subdir = outpath / f"{prefix}{suffix}.a{ac_id}"
            if not subdir.exists():
                subdir.mkdir(exist_ok=True)

        fmt = "{0}/{1}{2}.a{3}/{1}{2}.a{3}.{4}.{5}.ome.tiff"
        for ac_id, channel_list in acquisitions.items():
            imc_ac = self.acquisitions.get(ac_id)
            for ch_id, metal, label in channel_list:
                tiff = fmt.format(outpath, prefix, suffix, ac_id, metal, label)
                iw = imc_ac.get_image_writer(filename=str(tiff), metals=[metal])
                iw.save_image(mode="ome", compression=0, dtype=None, bigtiff=False)
                logger.debug(f"{tiff} saved.")
        logger.info(f"All tiffs saved.")

    def _write_tiffstack(self, acquisitions, prefix, suffix):
        logger.debug(f"Saving tiffstack with prefix:[{prefix}] and suffix:[{suffix}]")
        fmt = "{}{}.a{}.ome.tiff"
        for ac_id in acquisitions.keys():
            tiff = fmt.format(prefix, suffix, ac_id)
            imc_ac = self.acquisitions.get(ac_id)
            iw = imc_ac.get_image_writer(filename=str(tiff))
            iw.save_image(mode="ome", compression=0, dtype=None, bigtiff=False)
            logger.debug(f"{tiff} saved.")
        logger.info(f"All tiffstacks saved.")

    def _write_text(self, acquisitions, prefix, suffix):
        logger.debug(f"Saving text data with prefix:[{prefix}] and suffix:[{suffix}]")
        fmt = "{}{}.a{}.txt"
        for ac_id, channel_list in acquisitions.items():
            logger.debug(f"Creating text data for acquisition {ac_id}...")
            outfile = fmt.format(prefix, suffix, ac_id)

            ch_ids, ch_metals, ch_labels = map(list, zip(*channel_list))

            xyz = self.get_xyz_data(ac_id)
            xyz = xyz[:].reshape(3, -1).T
            logger.debug(f"XYZ data size for {ac_id}: {xyz.shape}")
            data = self.get_data(ac_id)[ch_ids]
            _n = data.shape[0]
            data = data[:].reshape(_n, -1).T
            logger.debug(f"Channel data size for {ac_id}: {data.shape}")
            logger.debug(f"Merging XYZ data with channel data.")
            data = np.column_stack((xyz, data))
            size = data.nbytes

            metals = [f"{metal}({label})" for _, metal, label in channel_list]
            data = pd.DataFrame(data, columns=["X", "Y", "Z"] + metals)
            logger.debug(f"Downcasting as much as possible to unsigned integers.")
            data = data.apply(pd.to_numeric, downcast="unsigned", errors="ignore")
            logger.debug(
                f"Text data formatted. Saving {size//1024//1024}MB now. This may take a while..."
            )
            data.to_csv(outfile, header=True, index=False, sep="\t")
            logger.debug(f"{outfile} saved.")
        logger.info(f"All text files saved.")

    def save(self, acquisitions, output_format, prefix="", suffix=""):
        save_funcs = {
            "imc": self._write_imcfolder,
            "tiff": self._write_tiff,
            "tiffstack": self._write_tiffstack,
            "text": self._write_text,
        }
        if not prefix:
            prefix = self.fileprefix
        save_funcs[output_format](acquisitions, prefix, suffix)


if __name__ == "__main__":
    mcd = MCD(Path("/Users/flynnb/projects/singlecell/ibc/imc/IMC0042.mcd"))
    mcd.load_mcd()
    mcd.save("text")
