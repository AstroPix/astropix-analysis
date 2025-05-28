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


"""Unit tests for the fmt.py module.
"""

import time

from astropix_analysis.fmt import BitPattern, AstroPix4Readout


# Mock data from a small test run with AstroPix4---the bytearray below should
# be exactly what might come out from a NEXYS board with the AstroPix 4 firmware.
# (For completeness, data were taken on 2024, December 19, and the array if
# taken verbatim from the log file. The readout contains exactly 2 hits.)
sample_readout_data = bytearray.fromhex('bcbce08056e80da85403bcbcbcbcbcbcbcbce080d26f04ca3005bcbcbcbcbcbcffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')

# And here are the corresponding decoded quantities from the cvs file.
decoded_header = 'dec_ord,id,payload,row,col,ts1,tsfine1,ts2,tsfine2,tsneg1,tsneg2,tstdc1,tstdc2,ts_dec1,ts_dec2,tot_us'
decoded_data0 = (0,7,0,5,5167,3,5418,6,1,0,0,0,49581,52836,162.75)
decoded_data1 = (0,7,0,5,6124,2,4876,5,0,1,0,0,54716,61369,332.65)


def test_bit_pattern():
    """Small test fucntion for the BitPattern class.
    """
    data = bytes.fromhex('bcff')
    pattern = BitPattern(data)
    print(pattern)
    # Test the text representation---note the class inherits the comparison operators
    # from the str class.
    assert pattern == '1011110011111111'
    # Same for __len__().
    assert len(pattern) == 16
    # Test slicing within the byte boundaries.
    assert pattern[0:4] == 11
    assert pattern[4:8] == 12
    assert pattern[8:12] == 15
    assert pattern[12:16] == 15
    # Test slicing across bytes.
    assert pattern[6:10] == 3


def test_new_decoding():
    """Test the new decoding stuff.
    """
    trigger_id = 0
    timestamp = time.time_ns()
    readout = AstroPix4Readout(trigger_id, timestamp, sample_readout_data)
    print(readout)
    hits = readout.decode()
    assert len(hits) == 2
    for hit in hits:
        print(hit)
    hit0, hit1 = hits
    # Compare the hit objects with the conten of the csv files---note we are
    # assuming that if the TOT value in us is ok, then all the intermediate timestamp
    # fields are ok, as well.
    assert (hit0.chip_id, hit0.payload, hit0.row, hit0.column) == decoded_data0[0:4]
    assert hit0.tot_us == decoded_data0[-1]
    assert (hit1.chip_id, hit1.payload, hit1.row, hit1.column) == decoded_data1[0:4]
    assert hit1.tot_us == decoded_data1[-1]

