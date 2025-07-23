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

import pytest

from astropix_analysis.fmt import BitPattern, AstroPix4Readout, AbstractAstroPixReadout, \
     AbstractAstroPixHit, AstroPix4Hit, uid_to_readout_class


# Mock data from a small test run with AstroPix4---the bytearray below should
# be exactly what might come out from a NEXYS board with the AstroPix 4 firmware.
# (For completeness, data were taken on 2024, December 19, and the array if
# taken verbatim from the log file. The readout contains exactly 2 hits.)
# pylint: disable=line-too-long
SAMPLE_READOUT_DATA = bytearray.fromhex('bcbce08056e80da85403bcbcbcbcbcbcbcbce080d26f04ca3005bcbcbcbcbcbcffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')  # noqa: E501


# And here are the corresponding decoded quantities from the cvs file.
DECODED_DATA0 = (0, 7, 0, 5, 5167, 3, 5418, 6, 1, 0, 0, 0, 49581, 52836, 162.75)
DECODED_DATA1 = (0, 7, 0, 5, 6124, 2, 4876, 5, 0, 1, 0, 0, 54716, 61369, 332.65)


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
    readout = AstroPix4Readout(SAMPLE_READOUT_DATA, readout_id=0)
    print(readout)
    hits = readout.decode()
    assert len(hits) == 2
    for hit in hits:
        print(hit)
        print(hit.attribute_values(['chip_id', 'payload', 'row', 'column']))
    hit0, hit1 = hits[0], hits[1]
    # Compare the hit objects with the content of the csv files---note we are
    # assuming that if the TOT value in us is ok, then all the intermediate timestamp
    # fields are ok, as well.
    assert (hit0.chip_id, hit0.payload, hit0.row, hit0.column) == DECODED_DATA0[0:4]
    assert hit0.tot_us == DECODED_DATA0[-1]
    assert (hit1.chip_id, hit1.payload, hit1.row, hit1.column) == DECODED_DATA1[0:4]
    assert hit1.tot_us == DECODED_DATA1[-1]
    # And test the exact same thing using the values() method.
    attrs = ['chip_id', 'payload', 'row', 'column']
    assert hit0.attribute_values(attrs) == list(DECODED_DATA0[0:4])
    assert hit1.attribute_values(attrs) == list(DECODED_DATA1[0:4])
    assert hit0.attribute_values(['tot_us']) == [DECODED_DATA0[-1]]
    assert hit1.attribute_values(['tot_us']) == [DECODED_DATA1[-1]]


def test_table():
    """Create a table from a readout.
    """
    readout = AstroPix4Readout(SAMPLE_READOUT_DATA, readout_id=0)
    hit_class = readout.HIT_CLASS
    col_names = hit_class.ATTRIBUTE_NAMES
    table = hit_class.empty_table(col_names)
    hits = readout.decode()
    for hit in hits:
        table.add_row(hit.attribute_values(col_names))
    print(table)


def test_abc():
    """Make sure we cannot instantiate the abstract base classes.
    """
    # pylint: disable=unused-variable, missing-class-docstring, abstract-class-instantiated

    # AbstractAstroPixHit is abstract and we need to overload the constructor!
    with pytest.raises(TypeError) as info:
        _ = AbstractAstroPixHit(None)
    print(info.value)

    # Make sure classes derived from AbstractAstroPixReadout override HIT_CLASS
    with pytest.raises(TypeError) as info:
        class Readout1(AbstractAstroPixReadout):
            pass
    print(info.value)

    # Make sure HIT_CLASS is not abstract.
    with pytest.raises(TypeError) as info:
        class Readout2(AbstractAstroPixReadout):
            HIT_CLASS = AbstractAstroPixHit
    print(info.value)

    # Make sure HIT_CLASS is of the proper type.
    with pytest.raises(TypeError) as info:
        class Readout3(AbstractAstroPixReadout):
            HIT_CLASS = float
    print(info.value)

    # Make sure _UID is overriden.
    with pytest.raises(TypeError) as info:
        class Readout4(AbstractAstroPixReadout):
            HIT_CLASS = AstroPix4Hit
    print(info.value)

    # Make sure _UID is an integer.
    with pytest.raises(TypeError) as info:
        class Readout5(AbstractAstroPixReadout):
            HIT_CLASS = AstroPix4Hit
            _UID = 'hello'
    print(info.value)


def test_uid():
    """Test the UID mechanism.
    """
    uid = AstroPix4Readout._UID
    assert AstroPix4Readout.uid() == uid
    assert uid_to_readout_class(uid) == AstroPix4Readout
