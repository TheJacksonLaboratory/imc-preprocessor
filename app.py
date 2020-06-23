#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

from mcd import MCD
from processing import *
from config import *


def run_config(args):
    options = generate_options_from_mcd(args.mcd)
    prefix = args.mcd.stem
    dump_config_file(options, f"{prefix}.yaml")


def run_process(args):
    mcd_or_yaml = args.mcd_or_yaml
    is_mcd = mcd_or_yaml.suffix.lower().endswith(".mcd")
    if is_mcd:
        options = generate_options_from_mcd(mcd_or_yaml)
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
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="command", dest="command", required=True)
    processer = subparsers.add_parser("process")
    processer.add_argument(
        "mcd_or_yaml", type=Path, action=check_extension({".mcd", ".yaml"})
    )
    processer.set_defaults(run_func=run_process)

    configer = subparsers.add_parser("config")
    configer.add_argument("mcd", type=Path, action=check_extension({".mcd"}))
    configer.set_defaults(run_func=run_config)

    return parser.parse_args()


def main():
    args = construct_parser()
    args.run_func(args)


if __name__ == "__main__":
    main()
