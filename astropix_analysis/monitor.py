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

"""Online monitoring.
"""

from abc import ABC, abstractmethod
import queue
import threading
import time

import numpy as np

from astropix_analysis import __version__
from astropix_analysis.fmt import AbstractAstroPixReadout, AstroPix4Readout
from astropix_analysis.hist import Histogram1d, Matrix2d
from astropix_analysis.plt_ import plt
from astropix_analysis.sock import MulticastReceiver
from astropix_analysis.sock import DEFAULT_MULTICAST_GROUP, DEFAULT_MULTICAST_PORT


class AbstractMonitor(ABC):

    """Abstract base class for online monitoring applications.

    .. warning::

       Note this is very rudimentary, and the (rough) result is achieved with
       no other GUI facility than the matplotlib canvas. In the future we almost
       certainly will want to do this properly, but in the meantime this class
       provides a sensible base building block for simple online monitoring
       applications.

    Arguments
    ---------
    readout_class : type
        The type of readout objects we are expecting (e.g., `AstroPix4Readout``).

    group : str
        The multicast group.

    port : int
        The multicast port.
    """

    def __init__(self, readout_class: type, group: str = DEFAULT_MULTICAST_GROUP,
                 port: int = DEFAULT_MULTICAST_PORT) -> None:
        """Constructor.
        """
        self._receiver = MulticastReceiver(readout_class, group, port)
        self._readout_buffer = queue.Queue()
        self._num_processed_readouts = 0
        self._num_processed_hits = 0
        self._msg_ax = None
        self._axes = None

    def create_canvas(self, **kwargs):
        """Create the matplotlib canvas that will hold the monitoring plot.

        Note we are adding a row at the very top of the subplots that we
        are taking over to use it as a message dashboard.

        Arguments
        ---------
        kwargs : dict
            Any keyword argument accepted by ``plt.subplot()``.
        """
        plt.ion()
        # Retrieve the number of rows and increase it by one unity.
        nrows = kwargs.get('nrows', 1)
        nrows += 1
        kwargs['nrows'] = nrows
        # Setup the height ratios.
        ratios = kwargs.get('height_ratios')
        height_ratios = [0.1]
        if ratios is None:
            height_ratios += [1.] * (nrows - 1)
        else:
            height_ratios += list(ratios)
        kwargs['height_ratios'] = height_ratios
        # Create the canvas.
        kwargs.setdefault('num', f'Astropix Monitor {__version__}')
        _, axes = plt.subplots(**kwargs)
        # Switch the axes off for the first row of subplots.
        for ax in axes[0]:
            ax.axis('off')
        # Get pointers to the relevant objects.
        self._msg_ax = axes[0, 0]
        self._axes = axes[1:]

    def display_message(self, x, y, text, **kwargs) -> None:
        """Display a message.
        """
        self._msg_ax.cla()
        self._msg_ax.axis('off')
        self._msg_ax.text(x, y, text, **kwargs)

    def _listen(self) -> None:
        """Listening function to be started on a separate thread.

        Note the leading underscore---this is generally not intended to
        be called directly.
        """
        while True:
            self._readout_buffer.put(self._receiver.receive())

    def start_listening(self) -> None:
        """Start listening for readouts over the UDP socket on a new thread.
        """
        # Note by default Python threads are non-daemon, meaning: Python will
        # wait for them to finish before the program exits. With ``daemon=True``,
        # the thread becomes a background worker that won't block the program
        # from exiting---and since we don't care about dropping packets, this
        # is what we want, here.
        threading.Thread(target=self._listen, daemon=True).start()

    def start(self, refresh_interval: float = 0.5, update_pause: float = 0.005):
        """Start the monitoring.

        This means that we start listening to the UDP socket on a new thread,
        and we begin popping readouts from the underlying buffer and updating the
        display.

        Arguments
        ---------
        refresh_interval : float
            The plot refresh interval in s.

        update_pause : float
            The post-update pause, in s, at the end of the update.
        """
        self.setup()
        self.start_listening()
        # You will notice there is some heuristics, here. Rather than sleep for the
        # given refresh interval, empty the buffer and update the display, we
        # are continuosly emptying the buffer, and this is the timeout that we
        # use for the ``get()`` call. Roughly speaking, if the timeout is 5 times
        # smaller than the refresh interval, this means that we are always poking
        # the buffer 5 times for each cycle---and more if we are taking data at
        # high rate. Note that calling ``get_nowait()`` instead would cause this
        # function to use 100% of the CPU.
        read_timeout = 0.2 * refresh_interval
        try:
            while True:
                last_update = time.time()
                while time.time() - last_update < refresh_interval:
                    try:
                        readout = self._readout_buffer.get(timeout=read_timeout)
                        self.process_readout(readout)
                        self._num_processed_readouts += 1
                        self._num_processed_hits += len(readout.hits())
                    except queue.Empty:
                        continue
                self.update_display()
                # And, apparently, this is matplotlib's built-in way to keep the live
                # plot responsive and visible when doing real-time updates. Take this
                # out and the plots will just refuse to update :-)
                plt.pause(update_pause)
        except KeyboardInterrupt:
            print('Done, bye!')

    def setup(self) -> None:
        """Setup the monitor.

        This is a general placeholder for the operations that need to be
        performed each time the monitor in restarted.
        """

    @abstractmethod
    def process_readout(self, readout: AbstractAstroPixReadout) -> None:
        """Process a single readout.
        """

    @abstractmethod
    def update_display(self) -> None:
        """Update the matplotlib display.
        """


class AstroPix4SimpleMonitor(AbstractMonitor):

    """Simple monitor for Astropix 4 readouts.
    """

    NUM_COLS = 16
    NUM_ROWS = 35

    def __init__(self, group: str = DEFAULT_MULTICAST_GROUP,
                 port: int = DEFAULT_MULTICAST_PORT) -> None:
        """Overloaded constructor.
        """
        super().__init__(AstroPix4Readout, group, port)
        self.tot_hist = Histogram1d(np.linspace(0., 500., 100), 'TOT [$\\mu$s]')
        self.hit_map = Matrix2d(self.NUM_COLS, self.NUM_ROWS)
        self.create_canvas(ncols=2, figsize=(12, 7), width_ratios=(1., 0.5))
        self.tot_ax, self.hit_ax = self._axes[0]

    def process_readout(self, readout: AbstractAstroPixReadout):
        """Overloaded method.
        """
        for hit in readout.decode():
            self.tot_hist.fill(hit.tot_us)
            self.hit_map.fill(hit.column, hit.row)

    def update_display(self) -> None:
        """Overloaded method.
        """
        message = f'Connected to address {self._receiver.address()}\n'\
                  f'{self._num_processed_readouts} readouts '\
                  f'({self._num_processed_hits} hits) processed'
        self.display_message(0., 0.9, message, ha='left', va='top')
        self.tot_ax.cla()
        self.tot_hist.draw(self.tot_ax)
        self.hit_ax.cla()
        self.hit_map.draw(self.hit_ax)
