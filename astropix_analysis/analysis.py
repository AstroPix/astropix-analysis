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

from argparse import Namespace

import numpy as np

from astropix_analysis import logger
from astropix_analysis.plt_ import plt



class Run:

    """Small conveinence class to read one input cvs file.

    dec_ord,
    id,
    payload,
    row,
    col,
    ts1,
    tsfine1,
    ts2,
    tsfine2,
    tsneg1,
    tsneg2,
    tstdc1,
    tstdc2,
    ts_dec1,
    ts_dec2,
    tot_us
    """

    _NUM_ROWS = 13
    _NUM_COLS = 16

    def __init__(self, file_path: str) -> None:
        """Constructor.
        """
        logger.info(f'Opening input file {file_path}...')
        try:
            self.dec_ord, _, _, self.row, self.col, _, _, _, _, _, _, _, _, self.rise_time,\
                self.fall_time, self.tot = np.loadtxt(file_path, skiprows=1, delimiter=',', unpack=True)
        except ValueError:
            logger.warning("ValueError found - file is probably empty")
            self.dec_ord = [] 
            self.tot = []
            self.row = []
            self.col = []
        logger.info(f'Done, {len(self)} event(s) read.')
        log_file_path = str(file_path).replace('.csv', '.log')
        logger.info(f'Reading associated log file {log_file_path}...')
        with open(log_file_path, 'r', encoding='utf-8') as log_file:
            self.voltage_card = self._parse_line(log_file)
            self.digital = self._parse_line(log_file)
            self.bias_block = self._parse_line(log_file)
            self.idac = self._parse_line(log_file)
            self.vdac = self._parse_line(log_file)
            self.receiver = self._parse_line(log_file)
            self.options = self._parse_line(log_file, False)
            logger.info(f'Command-line options: {self.options}')

    @staticmethod
    def _parse_line(log_file, split_by_colon: bool = True):
        """Parse one single line from a log file.
        """
        if split_by_colon:
            _, data = log_file.readline().split(':', 1)
        else:
            data = log_file.readline()
        data = eval(data)
        logger.debug(data)
        return data

    def filter_last_tot(self, maxtot=10000):
        """ Check for multiple trigger of the same pixel in the same buffer and return last ToT 
            Assuming events are ordered and check that dec_ord of the following line is 0
            Adding a flag to remove too-large TOT: probably a deconding issue
        """
        filtered_tot = []
        if len(self) == 0:
            return filtered_tot
        for i in range(len(self)-1):
            if self.dec_ord[i+1]==0:
                if self.tot[i]<=maxtot:
                    filtered_tot.append(self.tot[i])
        if self.tot[i]<=maxtot:
            filtered_tot.append(self.tot[-1]) # always adding last line
        return np.array(filtered_tot)
        
    def __len__(self) -> int:
        """Return the number of events in the data file.
        """
        if isinstance(self.tot, np.float64):
            return 1
        return len(self.tot)

    def inject_pixels(self):
        """
        """
        return self.options.inject
        
    def trigger_threshold(self) -> float:
        """
        """
        return self.options.threshold

    def running_time(self) -> float:
        """ Running time in seconds
        """
        return self.options.maxtime*60

    def injection_voltage(self) -> float:
        """
        """
        return self.options.vinj

    def tot_hist(self, binning: np.ndarray = None):
        """Make a histogram of the TOT.
        """
        plt.figure('TOT distribution')
        plt.hist(self.tot, bins=binning)
        plt.xlabel(r'TOT [$\mu$s]')

    def hit_map(self):
        """Make a hit map.
        """
        plt.figure('Hitmap')
        binning = (
            np.linspace(-0.5, self._NUM_COLS - 0.5, self._NUM_COLS + 1),
            np.linspace(-0.5, self._NUM_ROWS - 0.5, self._NUM_ROWS + 1)
            )
        data, _, _, _ = plt.hist2d(self.col, self.row, bins=binning)
        logger.info(f'Pixel occupancy: \n{data}')
        plt.xlabel('Column')
        plt.ylabel('Row')
        plt.gca().set_aspect('equal')
        return data



if __name__ == '__main__':
    from astropix_analysis import ASTROPIX_DATA
    import os
    file_path = os.path.join(ASTROPIX_DATA,  'runsuite_vscan_20241219-114807\\20241219-115526.csv') # a file with multiple redout
    run = Run(file_path)
    run.hit_map()
    #run.tot_hist(np.linspace(0, 500, 501))
    plt.figure('TOT distribution')
    plt.hist(run.tot, bins=np.linspace(0, 500, 201), label='all entries')
    plt.xlabel(r'TOT [$\mu$s]')
    filtered_tot = run.filter_last_tot(1000) 
    print(filtered_tot, np.mean(filtered_tot), np.std(filtered_tot, ddof=1))
    #plt.figure()
    plt.hist(filtered_tot, bins=np.linspace(0, 500, 201), alpha=0.5, label='highest entry only')
    plt.legend()
    plt.show()
