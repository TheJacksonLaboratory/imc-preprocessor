#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

from logger import logger
from mcd import MCD
from processing import *
from config import *


def run_config(args):
    options = generate_options_from_mcd(args.mcd)

    if args.config_output:
        outfile = args.config_output
    else:
        outfile = f"{options.output_prefix}.yaml"

    logger.info(f"Saving configuration file to {outfile}")
    dump_config_file(options, outfile)


def run_process(args):
    mcd_or_yaml = args.mcd_or_yaml
    is_mcd = mcd_or_yaml.suffix.lower().endswith(".mcd")
    if is_mcd:
        options = generate_options_from_mcd(mcd_or_yaml)
        options.mcdpath = Path(options.mcdpath)
    else:
        options = load_config_file(mcd_or_yaml)
    process(options)


def check_extension(choices):
    class Act(argparse.Action):
        def __call__(self, parser, namespace, path, option_string=None):
            suffix = path.suffix.lower()
            if suffix not in choices:
                parser.error(f"File provided is does not end in '{','.join(choices)}'")
            else:
                setattr(namespace, self.dest, path)

    return Act


def construct_parser():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose output/logging"
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="command",
        dest="command",
        required=True,
        help="Generate a YAML config file or process an MCD/YAML file",
    )
    processer = subparsers.add_parser("process", parents=[parent])
    processer.add_argument(
        "mcd_or_yaml",
        type=Path,
        action=check_extension({".mcd", ".yaml"}),
        help="Path to .MCD or .YAML file for processing",
    )
    processer.set_defaults(run_func=run_process)

    configer = subparsers.add_parser("config", parents=[parent])
    configer.add_argument(
        "mcd", type=Path, action=check_extension({".mcd"}), help="Path to .MCD file"
    )
    configer.add_argument(
        "-c",
        "--config-output",
        type=Path,
        help="Optional custom filename/location to save .YAML config file",
    )
    configer.set_defaults(run_func=run_config)

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(10)
    return args


def main():
    args = construct_parser()
    args.run_func(args)


if __name__ == "__main__":
    main()
