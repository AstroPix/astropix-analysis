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

"""Analysis facilities for scans.
"""

import pathlib

import numpy as np

from astropix_analysis import logger


def _parse_file_path(file_path: str) -> tuple:
    """Parse a single file path and extract all the relevant scan parameters.

    .. warning::
        This is ugly, and once we have a sensible header into the file, we should
        be able to get all the information that we need from the file itself.
    """
    parts = pathlib.Path(file_path).parts
    vpdac = int(parts[-4].replace('VPDAC_', ''))
    tune_dac = int(parts[-3].replace('TuneDAC_', ''))
    row = 1
    col = int(parts[-2].replace('Col_', ''))
    threshold = int(parts[-1].split('mV')[0].replace('threshold_', ''))
    return vpdac, tune_dac, row, col, threshold


def process_file(file_path: str) -> None:
    """Process a single file and extract the relevant scan parameters.
    """
    logger.info(f'Processing file {file_path}...')
    vpdac, tune_dac, target_row, target_col, threshold = _parse_file_path(file_path)
    row, col, tot = np.loadtxt(file_path, delimiter=',', skiprows=1, usecols=(3, 4, -1), unpack=True)
    row = row.astype(int)
    col = col.astype(int)
    try:
        num_hits = len(tot)
    except TypeError:
        num_hits = 0
    return vpdac, tune_dac, target_row, target_col, threshold, num_hits

def process_threshold_scan_data(folder_path: str) -> None:
    """
    """
    with open('scan.txt', 'w') as output_file:
        logger.info(f'Processing recursively all csv files in {folder_path}...')
        folder_path = pathlib.Path(folder_path)
        for _path in folder_path.rglob('Col_*'):
            if _path == folder_path:
                continue
            logger.info(f'Analyzing folder {_path}')
            threshold = []
            num_hits = []
            for file_path in sorted(_path.glob('*.csv')):
                vpdac, tune_dac, target_row, target_col, _threshold, _num_hits = process_file(file_path)
                threshold.append(_threshold)
                num_hits.append(_num_hits)

            if len(threshold) == 0:
                logger.warning(f'No data found in {_path}, skipping...')
                continue

            # Sort the arrays by threshold.
            threshold = np.array(threshold)
            idx = np.argsort(threshold)
            threshold = threshold[idx]
            num_hits = np.array(num_hits)[idx]
            output_file.write(f'{vpdac}, {tune_dac}, {target_row}, {target_col}, '
                              f'{[int(t) for t in threshold]}, {[int(n) for n in num_hits]}\n')


if __name__ == "__main__":
    process_threshold_scan_data('/home/users/lbaldini/work/astropix-data/scan3')