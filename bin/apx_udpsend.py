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

"""Small application to send readouts over a UDP socket.
"""

import argparse
import time

from astropix_analysis import logger
from astropix_analysis.cli import ArgumentParser
from astropix_analysis.fileio import sanitize_path, AstroPixBinaryFile, apx_open
from astropix_analysis.sock import MulticastSender


_DESCRIPTION = """Read Astropix readouts from a file and multicast them over a UDP socket.
"""


def main(args: argparse.Namespace) -> None:
    """Main entry point.
    """
    file_path = sanitize_path(args.infile, AstroPixBinaryFile.EXTENSION)
    sender = MulticastSender(args.group, args.port)
    try:
        with apx_open(file_path) as input_file:
            for readout in input_file:
                logger.debug(f'Sending {readout}')
                sender.send_readout(readout)
                time.sleep(args.sleep)
    except KeyboardInterrupt:
        print('Done, bye!')


if __name__ == "__main__":

    parser = ArgumentParser(description=_DESCRIPTION)
    parser.add_infile()
    parser.add_argument('--sleep', type=float, default=1.,
                        help='sleep time between readouts (s)')
    parser.add_multicast()
    main(parser.parse_args())
