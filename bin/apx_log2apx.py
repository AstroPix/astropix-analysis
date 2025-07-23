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

"""Simple converter for astropix log files.
"""

import argparse

from astropix_analysis.fileio import log_to_apx


_DESCRIPTION = """Astropix log file file converter.
"""



def main(args: argparse.Namespace) -> None:
    """Actual conversion function.
    """
    log_to_apx(args.infile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=_DESCRIPTION)
    parser.add_argument('infile', type=str,
                        help='path to the input file')
    parser.add_argument('--outfile', type=str, default=None,
                        help='path to the output file (optional)')
    main(parser.parse_args())