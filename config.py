#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import yaml
import typing
from pathlib import Path
from dataclasses import dataclass, field
from ast import literal_eval

import numpy as np

from mcd import MCD
from processing import selems


def numpy_representer(dumper, data):
    return dumper.represent_scalar(u'!array', repr(data.tolist()))


def numpy_constructor(loader, node):
    value = loader.construct_scalar(node)
    value = re.sub(r"([^[])\s+([^]])", r"\1 \2", value)
    return np.array(literal_eval(value))


yaml.add_representer(np.ndarray, numpy_representer)
yaml.add_constructor(u'!array', numpy_constructor)

@dataclass
class Channel(yaml.YAMLObject):
    yaml_tag = "!Channel"

    ch_id: int
    metal: str 
    label: str 
    pixel_removal_neighbors: int = 5 
    pixel_removal_selem: np.array = selems.square(3)

    def __repr__(self):
        return (
            "{self.__class__.__name__}(id={self.ch_id}, metal={self.metal}, "
            "label={self.label}, pixel_removal_neighbors={self.pixel_removal_neighbors}, "
            "selem={self.pixel_removal_selem}"
        ).format( self=self)

@dataclass
class Acquisition(yaml.YAMLObject):
    yaml_tag = "!Acquisition"
    acquisition_id: str
    channels: list = field(default_factory=list)

    @classmethod
    def from_mcd(cls, mcd, ac_id):
        channels = []
        for k, (chl, chm) in enumerate(zip(mcd.channel_labels[ac_id], mcd.channel_metals[ac_id])):
            channels.append(Channel(k, chm, chl))
        return cls(acquisition_id=ac_id, channels=channels)

    def __repr__(self):
        return (
            "{self.__class__.__name__}(id={self.acquisition_id}, channels={self.channels})"
        ).format(self=self)


@dataclass
class ProcessingOptions(yaml.YAMLObject):
    yaml_tag = "!ConfigOptions"
    mcdpath: str
    acquisitions: list = field(default_factory=list)

    do_compensate: bool = True
    compensate_output_type: typing.Union[None, typing.Literal["tiff", "tiffstack", "imc"]] = None
    do_pixel_removal: bool = True
    pixel_removal_method: typing.Literal["conway", "tophat"] = "conway"
    pixel_removal_output_type: typing.Union[None, typing.Literal["tiff", "tiffstack", "imc"]] = None
    do_equalization: bool = True
    equalization_output_type: typing.Union[None, typing.Literal["tiff", "tiffstack", "imc"]] = None

    def __repr__(self):
        return (
            "%s(file=%r, do_compensate=%r, compensation_output_type=%r, "
            "do_pixel_removal=%r, pixel_removal_method=%r, pixel_removal_output_type=%r, "
            "do_equalization=%r, equalization_output_type=%r, "
            "acquisitions=%r)"
        ) % (
            self.__class__.__name__, str(self.mcdpath), self.do_compensate, self.compensate_output_type,
            self.do_pixel_removal, self.pixel_removal_method, self.pixel_removal_output_type,
            self.do_equalization, self.equalization_output_type,
            self.acquisitions
        )


def generate_options_from_mcd(mcd_file):
    mcd = MCD(mcd_file)
    mcd.peek()

    options = ProcessingOptions(
        mcdpath=str(mcd_file),
        acquisitions=[
            Acquisition.from_mcd(mcd, ac_id)
            for ac_id in mcd.acquisition_ids
        ],
        compensate_output_type="tiff",
        pixel_removal_output_type="tiff",
        equalization_output_type="tiff"
    )

    return options


def load_config_file(config_path: Path) -> ProcessingOptions:
    with open(config_path, "r") as fin:
        options = yaml.load(fin, Loader=yaml.Loader)
    options.mcdpath = Path(options.mcdpath)
    return options


def dump_config_file(options: ProcessingOptions, config_path:Path) -> None:
    with open(config_path, "w") as fout:
        yaml.dump(options, fout)#, default_flow_style=False)
