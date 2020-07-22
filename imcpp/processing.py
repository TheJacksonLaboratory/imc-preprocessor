#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .mcd import MCD

import numpy as np
from argparse import Namespace
from scipy.signal import convolve2d
from skimage.morphology import white_tophat
from skimage.morphology import square, disk, diamond
from skimage.exposure import equalize_hist, equalize_adapthist

from .logger import logger
from .spillover import align_spillmat, load_spillmat


def cross(n):
    s = 2 * n + 1
    sel = np.zeros((s, s), dtype=int)
    sel[:, n] = 1
    sel[n, :] = 1
    return sel


selems = Namespace(square=square, disk=disk, cross=cross)


def conway(im, selem=disk(1), threshold=None):
    if threshold is None:
        threshold = selem.sum() // 2 + 1

    b = im.astype(bool).astype(int)
    m = convolve2d(b, selem, mode="same")
    im_ = im.copy()
    im_[m < threshold] = 0
    return im_


def tophat(im, selem=square(2)):
    b = im.copy().astype(bool).astype(int)
    m = b - white_tophat(b, selem=selem)
    im_ = im.copy()
    im_[~m.astype(bool)] = 0
    return im_


def compensate(img_stack, spillmat):
    swapped = False
    if img_stack.shape[0] == spillmat.shape[0]:
        img_stack = np.moveaxis(img_stack, 0, 2)
        swapped = True
    comp_ = img_stack @ np.linalg.inv(spillmat.T)
    comp_ = np.round(np.clip(comp_, 0, comp_.max())).astype(np.uint16)
    if swapped:
        comp_ = np.moveaxis(img_stack, 2, 0)
    return comp_


def equalize(img_stack, adaptive=False):
    L = img_stack.shape[0]

    logger.debug("5th and 95th percentile before equalization")
    logger.debug(
        np.column_stack(
            (
                np.arange(1, L + 1),
                np.percentile(img_stack, 5, axis=(1, 2)),
                np.percentile(img_stack, 95, axis=(1, 2)),
            )
        )
    )

    if adaptive:
        equalized = np.array(
            [
                equalize_adapthist(img_stack[k, ...], nbins=2 ** 16, clip_limit=0.4)
                for k in range(L)
            ]
        )
    else:
        equalized = np.array(
            [equalize_hist(img_stack[k, ...], nbins=2 ** 16) for k in range(L)]
        )
    return equalized


pixel_removal_functions = {
    "conway": conway,
    "tophat": tophat
}


def run_compensation(mcd, options):
    logger.info("Running compensation")
    logger.debug(
        "Note that all channels of the aquisition to be utilized during the "
        "compensation calculation but only those specified in the config "
        "file will be saved."
    )
    if options.spillover_matrix_file:
        logger.info(
            f"Using provided spillover matrix {options.spillover_matrix_file}"
        )
    spillmat_raw = load_spillmat(options.spillover_matrix_file)

    for ac_options in options.acquisitions:
        ac_id = ac_options.acquisition_id
        logger.debug(f". compensating acquisition {ac_id}.")
        spillmat = align_spillmat(spillmat_raw, mcd.channel_metals[ac_id])
        uncomp = mcd.get_data(ac_id)
        comp = compensate(uncomp, spillmat.values)
        mcd.set_data(comp, ac_id)

    if options.compensate_output_type:
        logger.info("Saving compensation results.")
        acquisitions = options.export_acquisitions()
        mcd.save(
            acquisitions,
            options.compensate_output_type,
            prefix=options.output_prefix,
            suffix=options.compensate_output_suffix,
        )

    logger.info("Compensation complete.")


def run_pixel_removal(mcd, options):
    logger.info("Running pixel removal")

    method = options.pixel_removal_method
    if method not in pixel_removal_functions:
        logger.error(
            f"Pixel removal function [{method}] is not in "
            f"allowed methods [{list(pixel_removal_functions.keys())}]."
        )
        logger.warn("Proceeding without pixel removal!")
        return
    method_func = pixel_removal_functions[method]


    global_threshold, global_selem = None, None
    if options.global_pixel_removal_neighbors is not None:
        global_threshold = options.global_pixel_removal_neighbors
        logger.debug(f"Will use global pixel removal threshold of {global_threshold}")
    if options.global_pixel_removal_selem is not None:
        global_selem = options.global_pixel_removal_selem
        logger.debug("Will use global pixel removal selem")

    for ac_options in options.acquisitions:
        ac_id = ac_options.acquisition_id

        for ch_opts in ac_options.channels:
            ch_id = ch_opts.ch_id
            clean = mcd.get_data(ac_id, ch_int=ch_id)

            logger.debug(f". cleaning acquisition/channel {ac_id}/{ch_opts.metal}.")
            selem = global_selem if global_selem is not None else ch_opts.pixel_removal_selem
            params = dict(selem=selem)
            if method == "conway":
                params["threshold"] = global_threshold if global_threshold is not None else ch_opts.pixel_removal_neighbors

            for k in range(ch_opts.pixel_removal_iterations):
                logger.debug(
                    f".. iteration {k} using method {method} with parameters "
                    "{', '.join('='.join(params.items()))}"
                )
                clean = method_func(clean, **params)

            mcd.set_data(clean, ac_id, ch_int=ch_id)

    if options.pixel_removal_output_type:
        logger.info("Saving pixel removal results.")
        acquisitions = options.export_acquisitions()
        mcd.save(
            acquisitions,
            options.pixel_removal_output_type,
            prefix=options.output_prefix,
            suffix=options.pixel_removal_output_suffix,
        )

    logger.info("Pixel removal complete.")


def run_equalization(mcd, options):
    logger.info("Running equalization")

    for ac_options in options.acquisitions:
        ac_id = ac_options.acquisition_id
        logger.debug(f". equalizing acquisition {ac_id}.")
        unequalized = mcd.get_data(ac_id)
        equalized = equalize(unequalized, adaptive=False)
        mcd.set_data(equalized, ac_id)

    if options.equalization_output_type:
        logger.info("Saving equalization results.")
        acquisitions = options.export_acquisitions()
        mcd.save(
            acquisitions,
            options.equalization_output_type,
            prefix=options.output_prefix,
            suffix=options.equalization_output_suffix,
        )

    logger.info("Equalization complete.")


def process(options):
    mcd = MCD(options.mcdpath)
    mcd.load_mcd()

    if options.do_compensate:
        run_compensation(mcd, options)

    if options.do_pixel_removal:
        run_pixel_removal(mcd, options)

    if options.do_equalization:
        run_equalization(mcd, options)
