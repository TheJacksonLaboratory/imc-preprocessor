#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

import numpy as np
from skimage.filters import gaussian
from skimage.restoration import denoise_tv_chambolle
from skimage.exposure import equalize_adapthist
from imctools.io.mcdparser import McdParser
from imctools.io.abstractparserbase import AcquisitionError


class MCDConverter:
    def __init__(self, mcdpath, outdir_root=None, overwrite=True):
        self.mcdpath = mcdpath
        self.outpath_root = outdir_root
        self.overwrite = overwrite
        self.acquisitions = {}

    def _create_output_dirs(self):
        mcdprefix = self.mcdpath.stem
        if not self.outpath_root:
            self.outpath_root = mcdpath.parent
        else:
            self.outpath_root = Path(self.outpath_root)

        self.outdir_stack = self.outpath_root / f"{mcdprefix}-ometiff-stack"
        self.outdir_stack_blur = self.outpath_root / f"{mcdprefix}-ometiff-stack-blur"
        self.outdir_tiffs = self.outpath_root / f"{mcdprefix}-ometiffs-raw"
        self.outdir_tiffs_filt = self.outpath_root / f"{mcdprefix}-ometiffs-filt"

        for d in filter(lambda s: s.startswith("outdir_"), dir(self)):
            d = getattr(self, d)
            Path(d).mkdir(parents=True, exist_ok=self.overwrite)

    @staticmethod
    def _get_acquisition(mcd, ac_id):
        try:
            imc_ac = mcd.get_imc_acquisition(ac_id)
        except AcquisitionError as e:
            imc_ac = None
        return imc_ac
    def load_acquisitions(self):
        for ac_id in self.mcd.acquisition_ids:
            imc_ac = self._get_acquisition(self.mcd, ac_id)
            if imc_ac is None: continue
            self.acquisitions[ac_id] = imc_ac


    def load_mcd(self):
        self._create_output_dirs()
        self.mcd = McdParser(str(self.mcdpath))
        self.fileprefix = self.mcdpath.stem

        self.load_acquisitions()

        print(f"MCD file {self.mcdpath} loaded")


    @staticmethod
    def filter_channel(arr, gaussian_rad=1, min_t=0.5, max_t=99.5):
        arr[np.where(
            (arr <= np.percentile(arr, min_t)) |\
            (arr >= np.percentile(arr, max_t))
        )] = 0
        if gaussian_rad > 0:
            arr = gaussian(arr, sigma=gaussian_rad)
        #arr = denoise_tv_chambolle(arr, weight=0.1)
        #arr = equalize_adapthist(arr, clip_limit=0.03)
        return arr

    def filter_stack(self, tmin, tmax, blur_rad):
        print(f"Filtiering acquisitions {tmin}%--{tmax}% with blur {blur_rad}")
        for ac_id, imc_ac in self.acquisitions.items():
            for k, (metal, label) in enumerate(zip(imc_ac.channel_metals,
                                                   imc_ac.channel_labels)):
                assert k == imc_ac._get_position(metal, imc_ac.channel_metals)
                _img = imc_ac.get_img_by_metal(metal).copy()
                _img_filt = self.filter_channel(
                    _img,
                    blur_rad,
                    tmin,
                    tmax
                )
                imc_ac._data[k] = _img_filt

    def save_individual_tiffs(self, outpath):
        ind_format = "{prefix}.a{ac_id}.{metal}.{label}.ome.tiff"
        for ac_id, imc_ac in self.acquisitions.items():
            for k, (metal, label) in enumerate(zip(imc_ac.channel_metals,
                                                   imc_ac.channel_labels)):

                tiff_file = outpath / ind_format.format(prefix=self.fileprefix,
                        ac_id=ac_id, metal=metal, label=label)
                iw = imc_ac.get_image_writer(filename=str(tiff_file), metals=[metal])
                iw.save_image(mode="ome", compression=0, dtype=None, bigtiff=False)


    def save_tiff_stack(self, outpath):
        stack_format = "{prefix}.a{ac_id}.ome.tiff"
        for ac_id, imc_ac in self.acquisitions.items():
            tiff_file = outpath / stack_format.format(prefix=self.fileprefix, ac_id=ac_id)
            iw = imc_ac.get_image_writer(str(tiff_file))
            iw.save_image(mode="ome", compression=0, dtype=None, bigtiff=False)


    def convert(self, *, cmin, cmax, segmentation_blur_radius, clip_blur_radius,
            **kwargs
        ):
        self.load_mcd()

        # save raw tiffs
        print(f"Saving raw tiffs")
        self.save_individual_tiffs(self.outdir_tiffs)

        # filter stack
        print(f"Saving clipped tiff stack")
        self.filter_stack(cmin, cmax, clip_blur_radius)
        self.save_tiff_stack(self.outdir_stack)

        # save individual filtered tiffs
        print(f"Saving clipped tiffs")
        self.save_individual_tiffs(self.outdir_tiffs_filt)

        # save stack
        print(f"Saving tiff stack for segmentation")
        self.load_acquisitions()
        self.filter_stack(cmin, cmax, segmentation_blur_radius)
        self.save_tiff_stack(self.outdir_stack_blur)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mcdfile", type=Path, help="path to file.mcd")
    parser.add_argument("-o", "--outdir", type=Path, default=None, help="Place to put tiffs")
    parser.add_argument("-b", "--clip-blur-radius", type=int, default=1)
    parser.add_argument("-s", "--segmentation-blur-radius", type=int, default=25)
    parser.add_argument("--clip-min", type=float, default=1)
    parser.add_argument("--clip-max", type=float, default=99)
    args = parser.parse_args()

    assert args.mcdfile.exists()

    converter = MCDConverter(args.mcdfile, args.outdir)
    converter.convert(
        cmin=args.clip_min, cmax=args.clip_max,
        segmentation_blur_radius=args.segmentation_blur_radius,
        clip_blur_radius=args.clip_blur_radius
    )
