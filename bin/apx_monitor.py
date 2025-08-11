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

"""Simple monitoring application.
"""

import argparse
import queue
import threading
import time

import numpy as np

from astropix_analysis import __version__
from astropix_analysis.cli import ArgumentParser
from astropix_analysis.fmt import AstroPix4Readout
from astropix_analysis.plt_ import plt
from astropix_analysis.sock import MulticastReceiver


_DESCRIPTION = """Monitor Astropix readouts over a UDP socket.
"""


def main(args: argparse.Namespace) -> None:
    """Main entry point.
    """
    # Create a buffer for the readout objects. This is needed because we shall
    # be accessing the buffer from two different threads, and a queue.Queue object
    # is inherently thread-safe.
    readout_buffer = queue.Queue()

    def _listen():
        """Start receiving readouts over the UPD socket.

        Note this function will be started on a new thread.
        """
        receiver = MulticastReceiver(AstroPix4Readout, args.group, args.port)
        while True:
            readout_buffer.put(receiver.receive())

    # Setup all the necessary stuff for the actual histograms.
    tot_data = []
    tot_binning = np.linspace(0., 500., 100)
    plt.ion()
    _, tot_ax = plt.subplots(num=f'Astropix Monitor {__version__}')

    # Start the listening thread.
    threading.Thread(target=_listen, daemon=True).start()

    # Start the GUI loop.
    try:
        while True:
            # Cache the time of the last update.
            last_update = time.time()

            # Collect data, i.e., pull readout objects out of the queue, decode
            # them and fill the relevant list used for the histograms.
            while time.time() - last_update < args.refresh:
                try:
                    readout = readout_buffer.get_nowait()
                    for hit in readout.decode():
                        tot_data.append(hit.tot_us)
                except queue.Empty:
                    continue

            # Draw the histograms.
            tot_ax.cla()
            tot_ax.hist(tot_data, bins=tot_binning)
            tot_ax.set_xlabel('TOT [$\\mu$s]')
            tot_ax.set_ylabel('Entries per bin')
            # And, apparently, this is matplotlib's built-in way to keep the live
            # plot responsive and visible when doing real-time updates...
            plt.pause(0.01)
    except KeyboardInterrupt:
        print('Done, bye!')


if __name__ == "__main__":
    parser = ArgumentParser(description=_DESCRIPTION)
    parser.add_argument('--refresh', type=float, default=0.5,
                        help='refresh interval (s)')
    parser.add_multicast()
    main(parser.parse_args())
