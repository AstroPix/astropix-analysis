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
from astropix_analysis.fmt import reverse_bit_order


def test():
    """
    """
    file_path = ASTROPIX_ANALYSIS_TESTS_DATA / 'quad_chip' / 'quad_chip_data.bin'
    with open(file_path, 'rb') as input_file:
        data = input_file.read(11)
        for i in range(11):
            byte = data[i:i + 1]
            print(bin(ord(reverse_bit_order(byte))))