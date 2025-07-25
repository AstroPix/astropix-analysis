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

"""Simple playback application for .apx files.
"""

import argparse
import shutil

from astropix_analysis import logger
from astropix_analysis.fileio import apx_open


_DESCRIPTION = """Astropix binary data file playback facility.
"""


def main(args: argparse.Namespace) -> None:
    """Actual conversion function.
    """
    logger.info(f'About to playback {args.infile}')
    with apx_open(args.infile) as input_file:
        header = input_file.header
        print(f'{header}\n')
        for i, readout in enumerate(input_file):
            title = f'Readout {i:06d}'
            terminal_width, _ = shutil.get_terminal_size()
            pad = '-' * ((terminal_width - len(title)) // 2)
            print(f'{pad}{title}{pad}')
            print(readout.pretty_print())
            input()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=_DESCRIPTION)
    parser.add_argument('infile', type=str,
                        help='path to the input file')
    main(parser.parse_args())
