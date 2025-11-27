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

"""Unit tests for the decoding routines for the quad chip.
"""

from astropix_analysis import ASTROPIX_ANALYSIS_TESTS_DATA
from astropix_analysis.fmt import AstroPix3QuadChipHit


def test():
    """Process the small input file provided by Adrien and compare with the
    processed csv file.
    """
    bin_file_path = ASTROPIX_ANALYSIS_TESTS_DATA / 'quad_chip' / 'quad_chip_data.bin'
    csv_file_path = ASTROPIX_ANALYSIS_TESTS_DATA / 'quad_chip' / 'quad_chip_data.csv'
    with open(bin_file_path, 'rb') as bin_file, open(csv_file_path, 'r') as csv_file:
        csv_file.readline()
        for i in range(10):
            readout_id, readout, layer, chip_id, payload, location, column, timestamp, \
                tot_msb, tot_lsb, tot_total, tot_us, fpga_ts = csv_file.readline().strip('\n').split(',')
            hit_data = bin_file.read(AstroPix3QuadChipHit._SIZE)
            hit = AstroPix3QuadChipHit(hit_data, i, 0, 0)
            print(hit)
            print(readout_id, hit.readout_id)
            print(payload, hit.payload)
            print(chip_id, hit.chip_id)
            print(location, hit.location)
            print(fpga_ts, hit.fpga_timestamp)