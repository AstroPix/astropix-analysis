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

"""Small application to receive readouts over a UDP socket.
"""

import argparse

from astropix_analysis.cli import ArgumentParser
from astropix_analysis.fmt import AstroPix4Readout
from astropix_analysis.sock import MulticastReceiver


_DESCRIPTION = """Receive Astropix readouts over a UDP socket.
"""


def main(args: argparse.Namespace) -> None:
    """Main entry point.
    """
    # Note the readout class is hard-coded for the time being!
    receiver = MulticastReceiver(AstroPix4Readout, args.group, args.port)
    try:
        while True:
            readout = receiver.receive()
            print(readout)
            hits = readout.decode()
            for hit in hits:
                print(hit)
    except KeyboardInterrupt:
        print('Done, bye!')


if __name__ == "__main__":
    parser = ArgumentParser(description=_DESCRIPTION)
    parser.add_multicast()
    main(parser.parse_args())
