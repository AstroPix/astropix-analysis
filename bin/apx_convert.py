#!/usr/bin/env python3
# Copyright (C) 2025 the astropix team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Simple converter for astropix binary files.
"""

import argparse

from astropix_analysis.fmt import AstroPix4Readout
from astropix_analysis.fileio import apx_to_csv


_READOUT_CLASS_NAMES = ('AstroPix4Readout', )
_DEFAULT_READOUT_CLASS_NAME = 'AstroPix4Readout'
_READOUT_CLASS_DICT = {
    'AstroPix4Readout': AstroPix4Readout
}


def main(args: argparse.Namespace) -> None:
    """Actual conversion function.
    """
    readout_class = _READOUT_CLASS_DICT[args.readout]
    apx_to_csv(args.infile, readout_class, args.outfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Astropix 4 file converter')
    parser.add_argument('infile', type=str,
                        help='path to the input file')
    parser.add_argument('--readout', type=str, choices=_READOUT_CLASS_NAMES,
                        default=_DEFAULT_READOUT_CLASS_NAME,
                        help='the name of the readout class stored in the file')
    parser.add_argument('--outfile', type=str, default=None,
                        help='path to the output file')

    main(parser.parse_args())
