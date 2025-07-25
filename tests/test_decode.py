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

"""Unit tests for the decoding routines.
"""

from astropix_analysis.fmt import AstroPix4Hit, AstroPix4Readout, reverse_bit_order


# pylint: disable=line-too-long, unbalanced-tuple-unpacking

# Sample readout data for testing---this is a verbatim copy of tests/data/decode/test.log
SAMPLE_READOUT_DATA = [
    # Two distinct events, nothing strange
    # 1: e05042030620d701 -> [0],0,7,1,9,1408,6,1259,4,0,0,0,0,14331,14952,31.05
    # 2: e05041130620d701 -> [1],0,7,1,10,1424,6,1259,4,0,0,0,0,14084,14952,43.4
    bytes.fromhex('bcbce05042030620d701bcbce05041130620d701bcbcbcbcbcbcffffffffffffffffffffffffffff'),  # noqa: E501
    # Problem #1: no `bcbc` between the two events.
    bytes.fromhex('bcbce05042030620d701e05041130620d701bcbcbcbcbcbcffffffffffffffffffffffffffffffff'),  # noqa: E501
    # Problem #2: two events, the second is truncated---the remaining part is in
    # the following line. Note the second event should get a decoding order of 0, not 1.
    bytes.fromhex('bcbce05042030620d701bcbce05042030620ffffffffffffffffffffffffffffffffffffffffffff'),  # noqa: E501
    bytes.fromhex('d701bcbce05041130620d701bcbcbcbcbcbcffffffffffffffffffffffffffffffffffffffffffff'),  # noqa: E501
    # Problem #3: two events, the first one has two bytes missing, no `bcbc` in
    # between, and the second is complete. In this case we want to throw away the first.
    bytes.fromhex('bcbce05042030620e05041130620d701bcbcbcbcbcbcffffffffffffffffffffffffffffffffffff'),  # noqa: E501
    # Problem #4: one event which happens to have a `e0` in the middle, and
    # could either be a legitimate event, or really two incomplete events
    # amounting to 8 bytes total.
    # e05042e050411306 -> [0],0,7,1,9,1038,0,712,3,0,0,21,0,16288,7042,6091.3
    bytes.fromhex('bcbce05042e050411306bcbcbcbcbcbcffffffffffffffffffffffffffffffffffffffffffffffff'),  # noqa: E501
    # Problem #5: we have 4n `f` between the two events, and also extra `f` after
    # the second event.
    bytes.fromhex('bcbce05042030620d701bcffffffffbce05041130620d701bcbcffffbcbcbcbcffffffffffffffff')  # noqa: E501
]


def _create_hit(text_data: str, hit_class: type = AstroPix4Hit):
    """Create a fully-fledged hit object from some text data.
    """
    return hit_class(reverse_bit_order(bytes.fromhex(text_data)), 0, 0)


def _sample_readout(sample_index: int) -> AstroPix4Readout:
    """Read one of the sample readout data and turn it into an actual readout object.

    Note this assigns by default a readout_id of zero and a timestamp of zero.
    """
    return AstroPix4Readout(SAMPLE_READOUT_DATA[sample_index], readout_id=0, timestamp=0)


# And these are the two hits in the data stream
HIT_1 = _create_hit('e05042030620d701')
HIT_2 = _create_hit('e05041130620d701')
HIT_3 = _create_hit('e05042e050411306')


print(HIT_1)
print(HIT_2)


def test_sample_0():
    """Sample 0: just a normal readout.
    """
    print('Testing sample 0...')
    readout0 = _sample_readout(0)
    assert tuple(readout0.decode()) == (HIT_1, HIT_2)


def test_sample_1():
    """Sample 1: no idle bytes between events.
    """
    print('Testing sample 1...')
    readout1 = _sample_readout(1)
    assert tuple(readout1.decode()) == (HIT_1, HIT_2)
    print(readout1.decoding_status())


def test_sample_2_3():
    """Samples 2 and 3: one event fragmented across two different readouts.
    """
    print('Testing samples 2 and 3...')
    readout2 = _sample_readout(2)
    [hit] = readout2.decode()
    assert hit == HIT_1
    readout3 = _sample_readout(3)
    hit1, hit2 = readout3.decode(readout2.extra_bytes())
    assert (hit1, hit2) == (HIT_1, HIT_2)
    print(readout2.decoding_status())
    print(readout3.decoding_status())


def test_sample_4():
    """Sample 4: the first event has two bytes missing and cannot be recovered.
    """
    print('Testing sample 4...')
    readout4 = _sample_readout(4)
    [hit] = readout4.decode()
    assert hit == HIT_2
    print(readout4.decoding_status())


def test_sample_5():
    """Sample 5:
    """
    print('Testing sample 5...')
    readout5 = _sample_readout(5)
    [hit] = readout5.decode()
    assert hit == HIT_3
    print(readout5.decoding_status())


def test_sample_6():
    """Sample 6:
    """
    print('Testing sample 6...')
    readout6 = _sample_readout(6)
    hit1, hit2 = readout6.decode()
    assert (hit1, hit2) == (HIT_1, HIT_2)
    print(readout6.decoding_status())
