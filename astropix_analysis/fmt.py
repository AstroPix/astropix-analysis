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

"""Data format description for the astropix chip.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import struct
import time
import typing

import astropy.table
import numpy as np

from astropix_analysis import logger

# Table to reverse the bit order within a byte---we pre-compute this once and
# forever to speedup the computation at runtime and avoid doing the same
# calculation over and over again.
_BIT_REVERSE_TABLE = bytes.maketrans(
    bytes(range(256)),
    bytes(int(f'{i:08b}'[::-1], 2) for i in range(256))
)


def reverse_bit_order(data: bytearray) -> None:
    """Reverses the bit order within of a bytearray."""
    return data.translate(_BIT_REVERSE_TABLE)


class BitPattern(str):

    """Small convenience class representing a bit pattern, that we can slice
    (interpreting the result as the binary representation of an integer) without
    caring about the byte boundaries.

    This is not very memory-efficient and probably not blazingly fast either, but
    it allows to reason about the incoming bits in a straightforward fashion, and
    I doubt we will ever need to optimize this. (If that is the case, there are
    probably ways, using either numpy or the bitarray third-party package.)

    Arguments
    ---------
    data : bytes
        The binary representation of the bit pattern.
    """

    def __new__(cls, data: bytes) -> None:
        """Strings are immutable, so use __new__ to start.
        """
        return super().__new__(cls, ''.join(f'{byte:08b}' for byte in data))

    def __getitem__(self, index):
        """Slice the underlying string and convert to integer in base 2.
        """
        return int(super().__getitem__(index), 2)


def hitclass(cls: type) -> type:
    """Small decorator to support automatic generation of concrete hit classes.

    Here we simply calculate some useful class variables that are needed to
    unpack the binary data and/or write the hit to different data formats. Having
    a decorator allows to do the operation once and for all at the time the
    type is created, as opposed to do it over and over again each time an instance
    of the class is created. More specifically:

    * ``ATTRIBUTE_NAMES`` is a tuple containing all the hit field names that can be
      used, e.g., for printing out the hit itself;
    * ``_ATTR_IDX_DICT`` is a dictionary mapping the name of each attribute to
      the corresponding slice of the input binary buffer---note it does not include
      the attributes that are not encoded in the input buffer, but are calculated
      at construction time; this facilitates unpacking the input buffer;
    * ``_ATTR_TYPE_DICT`` is a dictionary mapping the name of each class attribute to
      the corresponding data type for the purpose of writing it to a binary file
      (e.g., in HDF5 or FITS format).
    """
    # pylint: disable=protected-access
    cls.ATTRIBUTE_NAMES = tuple(cls._LAYOUT.keys())
    cls._ATTR_IDX_DICT = {name: idx for name, (idx, _) in cls._LAYOUT.items() if idx is not None}
    cls._ATTR_TYPE_DICT = {name: type_ for name, (_, type_) in cls._LAYOUT.items()}
    return cls


class AbstractAstroPixHit(ABC):

    """Abstract base class for a generic AstroPix hit.

    While the original decode routine was working in terms of the various bytes
    in the binary representation of the hit, since there seem to be no meaning
    altogether in the byte boundaries (at least for AstroPix 4), and the various
    fields are arbitrary subsets of a multi-byte word, it seemed more natural to
    describe the hit as a sequence of fields, each one with its own length in bits.

    Note this is an abstract class that cannot be instantiated. (Note the ``__init__()``
    special method is abstract and needs to be overloaded, based on the assumption
    that for concrete classes we always want to calculate derived quantities based
    on the row ones parsed from the input binary buffer.)
    Concrete subclasses must by contract:

    * overload the ``_SIZE``;
    * overload the ``_LAYOUT``;
    * be decorated with the ``@hitclass`` decorator.

    Arguments
    ---------
    data : bytearray
        The portion of a full AstroPix readout representing a single hit.
    """

    # These first two class variables must be overriden by concrete subclasses...
    _SIZE = 0
    _LAYOUT = {}
    # ... while these get populated automatically once the subclass is decorated
    # with @hitclass (and still we initialize them here to None to make the linters
    # happy.)
    ATTRIBUTE_NAMES = ()
    _ATTR_IDX_DICT = {}
    _ATTR_TYPE_DICT = {}

    @abstractmethod
    def __init__(self, data: bytearray) -> None:
        """Constructor.
        """
        # Since we don't need the underlying bit pattern to be mutable, turn the
        # bytearray object into a bytes object.
        self._data = bytes(data)
        # Build a bit pattern to extract the fields and loop over the hit fields
        # to set all the class members.
        bit_pattern = BitPattern(self._data)
        for name, idx in self._ATTR_IDX_DICT.items():
            setattr(self, name, bit_pattern[idx])

    @staticmethod
    def gray_to_decimal(gray: int) -> int:
        """Convert a Gray code (integer) to decimal.

        A Gray code (or reflected binary code) is a binary numeral system where
        two consecutive values differ by only one bit, which makes it useful in
        error correction and minimizing logic transitions in digital circuits.
        This function is provided as a convenience to translate counter values
        encoded in Gray code into actual decimal values.
        """
        decimal = gray  # First bit is the same
        mask = gray
        while mask:
            mask >>= 1
            decimal ^= mask  # XOR each shifted bit
        return decimal

    @classmethod
    def empty_table(cls, attribute_names: list[str] = None) -> astropy.table.Table:
        """Return an astropy empty table with the proper column types for the
        concrete hit type.

        Note this is checking that all the attribute names are valid and tries and
        raise a useful exception if that is not the case.

        Arguments
        ---------
        attribute_names : str
            The name of the hit attributes.
        """
        if attribute_names is None:
            attribute_names = cls.ATTRIBUTE_NAMES
        for name in attribute_names:
            if name not in cls.ATTRIBUTE_NAMES:
                raise RuntimeError(f'Invalid attribute "{name}" for {cls.__name__}---'
                                   f'valid attributes are {cls.ATTRIBUTE_NAMES}')
        types = [cls._ATTR_TYPE_DICT[name] for name in attribute_names]
        return astropy.table.Table(names=attribute_names, dtype=types)

    def attribute_values(self, attribute_names: list[str] = None) -> list:
        """Return the value of the hit attributes for a given set of attribute names.

        Arguments
        ---------
        attribute_names : str
            The name of the hit attributes.
        """
        if attribute_names is None:
            attribute_names = self.ATTRIBUTE_NAMES
        return [getattr(self, name) for name in attribute_names]

    def __eq__(self, other: 'AbstractAstroPixHit') -> bool:
        """Comparison operator---this is handy in the unit tests.
        """
        return self._data == other._data

    def __str__(self) -> str:
        """String formatting.
        """
        return f'{self.__class__.__name__}'\
               f"({', '.join(f'{key} = {value}' for key, value in self.__dict__.items())})"


@hitclass
class AstroPix3Hit(AbstractAstroPixHit):

    """Class describing an AstroPix3 hit.

    .. warning::

        This is copied from decode.py and totally untested.
    """

    _SIZE = 5
    _LAYOUT = {
        'chip_id': (slice(0, 5), np.uint8),
        'payload': (slice(5, 8), np.uint8),
        'column': (8, np.uint8),
        'location': (slice(10, 16), np.uint8),
        'timestamp': (slice(16, 24), np.uint8),
        'tot_msb': (slice(28, 32), np.uint8),
        'tot_lsb': (slice(32, 40), np.uint8),
        'tot_dec': (None, np.uint16),
        'tot_us': (None, np.float32)
    }

    CLOCK_CYCLES_PER_US = 200.

    def __init__(self, data: bytearray) -> None:
        """Constructor.
        """
        # pylint: disable=no-member
        super().__init__(data)
        # Calculate the TOT in physical units.
        self.tot_dec = (self.tot_msb << 8) + self.tot_lsb
        self.tot_us = self.tot_dec / self.CLOCK_CYCLES_PER_US


@hitclass
class AstroPix4Hit(AbstractAstroPixHit):

    """Class describing an AstroPix4 hit.
    """

    _SIZE = 8
    _LAYOUT = {
        'chip_id': (slice(0, 5), np.uint8),
        'payload': (slice(5, 8), np.uint8),
        'row': (slice(8, 13), np.uint8),
        'column': (slice(13, 18), np.uint8),
        'ts_neg1': (18, np.uint8),
        'ts_coarse1': (slice(19, 33), np.uint16),
        'ts_fine1': (slice(33, 36), np.uint8),
        'ts_tdc1': (slice(36, 41), np.uint8),
        'ts_neg2': (41, np.uint8),
        'ts_coarse2': (slice(42, 56), np.uint16),
        'ts_fine2': (slice(56, 59), np.uint8),
        'ts_tdc2': (slice(59, 64), np.uint8),
        'ts_dec1': (None, np.uint32),
        'ts_dec2': (None, np.uint32),
        'tot_us': (None, np.float64),
        'readout_id': (None, np.uint32),
        'timestamp': (None, np.uint64)
    }

    CLOCK_CYCLES_PER_US = 20.
    CLOCK_ROLLOVER = 2**17

    def __init__(self, data: bytearray, readout_id: int, timestamp: int) -> None:
        """Constructor.
        """
        # pylint: disable=no-member
        super().__init__(data)
        # Calculate the values of the two timestamps in clock cycles.
        self.ts_dec1 = self._compose_ts(self.ts_coarse1, self.ts_fine1)
        self.ts_dec2 = self._compose_ts(self.ts_coarse2, self.ts_fine2)
        # Take into account possible rollovers.
        if self.ts_dec2 < self.ts_dec1:
            self.ts_dec2 += self.CLOCK_ROLLOVER
        # Calculate the actual TOT in us.
        self.tot_us = (self.ts_dec2 - self.ts_dec1) / self.CLOCK_CYCLES_PER_US
        self.readout_id = readout_id
        self.timestamp = timestamp

    @staticmethod
    def _compose_ts(ts_coarse: int, ts_fine: int) -> int:
        """Compose the actual decimal representation of the timestamp counter,
        putting together the coarse and fine counters (in Gray code).

        Arguments
        ---------
        ts_coarse : int
            The value of the coarse counter (MSBs) in Gray code.

        ts_fine : int
            The value of the fine counter (3 LSBs) in Gray code.

        Returns
        -------
        int
            The actual decimal value of the timestamp counter, in clock cycles.
        """
        return AbstractAstroPixHit.gray_to_decimal((ts_coarse << 3) + ts_fine)


class AbstractAstroPixReadout(ABC):

    """Abstract base class for a generic AstroPix readout.

    This is basically a wrapper around the bytearray object that is returned by
    the DAQ board, and it provides some basic functionality to write the readout
    to a binary file.

    A full readout comes in the form of a fixed-length bytearray object that is
    padded at the end with a padding byte (0xff). The hit data are surrounded by a
    (generally variable) number of idle bytes (0xbc), see the documentation of the
    decode() class method.

    Arguments
    ---------
    readout_data : bytearray
        The readout data from the DAQ board.

    readout_id : int
        A sequential id for the readout, assigned by the host DAQ machine.

    timestamp : int
        A timestamp for the readout, assigned by the host DAQ machine, in ns since
        the epoch, from time.time_ns().
    """

    # The class representing the hit type encoded in the readout, e.g., ``AstroPix4Hit``.
    HIT_CLASS = None

    # A unique identifier for the readout class.
    _UID = None

    # The padding byte used to pad the readout.
    PADDING_BYTE = bytes.fromhex('ff')

    # The idle byte, output by the chip while gathering data.
    IDLE_BYTE = bytes.fromhex('bc')

    # The readout header, which is prepended to the buffer read from the NEXYS board
    # before the thing gets written to disk.
    _HEADER = bytes.fromhex('fedcba')
    _HEADER_SIZE = len(_HEADER)

    # Basic bookkeeping for the additional fields assigned by the host machine.
    _READOUT_ID_FMT = '<L'
    _TIMESTAMP_FMT = '<Q'
    _LENGTH_FMT = '<L'

    def __init__(self, readout_data: bytearray, readout_id: int,
                 timestamp: int = None) -> None:
        """Constructor.
        """
        # If the timestamp is None, automatically latch the system time.
        # Note this is done first in order to latch the timestamp as close as
        # possible to the actual readout.
        self.timestamp = self.latch_ns() if timestamp is None else timestamp
        # Strip all the trailing padding bytes from the input bytearray object
        # and turn it into a bytes object to make it immutable.
        self._readout_data = bytes(readout_data.rstrip(self.PADDING_BYTE))
        self.readout_id = readout_id
        self.extra_bytes = None

    def __init_subclass__(cls):
        """Overloaded method.

        Now, this might be an overkill, but we want to help the user understand
        that ``HIT_CLASS`` *must* be redefined to a concrete AbstractAstroPixHit
        subclass.

        And this could be achieved at the class level definition with a decorator,
        so that we are not going through a bunch of ifs every time we instantiate
        an object.
        """
        super().__init_subclass__()
        if cls.HIT_CLASS is None:
            raise TypeError(f'{cls.__name__} must override HIT_CLASS')
        if cls.HIT_CLASS is AbstractAstroPixHit:
            raise TypeError(f'{cls.__name__}.HIT_CLASS is abstract')
        if not issubclass(cls.HIT_CLASS, AbstractAstroPixHit):
            raise TypeError(f'{cls.__name__}.HIT_CLASS is not a subclass of AbstractAstroPixHit')
        if cls._UID is None:
            raise TypeError(f'{cls.__name__} must override _UID')
        if not isinstance(cls._UID, int):
            raise TypeError(f'{cls.__name__} must be an integer ({cls._UID} is invalid)')

    @classmethod
    def uid(cls) -> int:
        """Return the unique identifier for the readout class.
        """
        return cls._UID

    @staticmethod
    def latch_ns() -> int:
        """Convenience function returning the time of the function call as an
        integer number of nanoseconds since the epoch, i.e., January 1, 1970,
        00:00:00 (UTC) on all platforms.
        """
        return time.time_ns()

    @staticmethod
    def read_and_unpack(input_file: typing.BinaryIO, fmt: str) -> typing.Any:
        """Convenience function to read and unpack a fixed-size field from an input file.

        Arguments
        ---------
        input_file : BinaryIO
            A file object opened in "rb" mode.

        fmt : str
            The format string for the field to be read.
        """
        return struct.unpack(fmt, input_file.read(struct.calcsize(fmt)))[0]

    def write(self, output_file: typing.BinaryIO) -> None:
        """Write the complete readout to a binary file.

        Arguments
        ---------
        output_file : BinaryIO
            A file object opened in "wb" mode.
        """
        output_file.write(self._HEADER)
        output_file.write(struct.pack(self._READOUT_ID_FMT, self.readout_id))
        output_file.write(struct.pack(self._TIMESTAMP_FMT, self.timestamp))
        output_file.write(struct.pack(self._LENGTH_FMT, len(self._readout_data)))
        output_file.write(self._readout_data)

    @classmethod
    def from_file(cls, input_file: typing.BinaryIO) -> AbstractAstroPixReadout:
        """Create a Readout object reading the underlying data from an input binary file.

        By contract this should return None when there are no more data to be
        read from the input file, so that downstream code can use the information
        to stop iterating over the file.

        Arguments
        ---------
        input_file : BinaryIO
            A file object opened in "rb" mode.
        """
        _header = input_file.read(cls._HEADER_SIZE)
        # If the header is empty, this means we are at the end of the file, and we
        # return None to signal that there are no more readouts to be read. This
        # can be used downstream, e.g., to raise a StopIteration exception with
        # the implementation of an iterator protocol.
        if len(_header) == 0:
            return None
        # If the header is not empty, we check that it is what we expect, and raise
        # a RuntimeError if it is not.
        if _header != cls._HEADER:
            raise RuntimeError(f'Invalid readout header ({_header}), expected {cls._HEADER}')
        # Go ahead, read all the fields, and create the AstroPix4Readout object.
        readout_id = cls.read_and_unpack(input_file, cls._READOUT_ID_FMT)
        timestamp = cls.read_and_unpack(input_file, cls._TIMESTAMP_FMT)
        data = input_file.read(cls.read_and_unpack(input_file, cls._LENGTH_FMT))
        return cls(data, readout_id, timestamp)

    def is_valid_hit_start_byte(self, byte: bytes) -> bool:
        """Return True if the byte is of the form `111xxxxx`.

        Consider moving this to the AstroPix4 class.
        """
        return ord(byte) >> 5 == 7

    def decode(self, extra_bytes: bytes = None) -> list[AbstractAstroPixHit]:
        """Generic decoding function to be used by subclasses.

        .. warning::
          This is really taylored on Astropix4 readout, and it is not entirely
          clear to me how other chip version differ. When we finally support other
          Astropix versions, this method will need to be refactored in the actual
          subclasses, and should probably become abstract.

        Here is some important details about the underlying generation of idle bytes,
        verbatim from a comment by Nicolas to the github pull request
        https://github.com/AstroPix/astropix-python/pull/22

        Regarding the number of IDLE bytes ("BC"), you typically see two when you start
        reading from the chip. This happens because the chip's SPI interface is clocked
        by the SPI master in the DAQ. The data isn't immediately available because it
        has to be transferred from an asynchronous FIFO to a FSM and then to the SPI
        arbiter which needs few clock cycles. While the chip is preparing the data, it
        sends out two IDLE bytes. After these 16 spi clock cycles, data is ready and
        the chip can start transmitting. As the data is being read, the chip uses the
        clock cycles to fetch new data, allowing multiple data words to be transmitted
        without IDLE bytes in between or just one. The "line break" shown by @grant-sommer
        is due to the fact that the firmware reads a certain number of bytes which is
        not synchronized to beginning or ending of dataframes coming from the chip,
        so it might just stop reading in the middle of a frame.
        """
        # pylint: disable=not-callable, protected-access
        hits = []
        pos = 0
        while pos < len(self._readout_data):
            # Skip the idle bytes---note we need to address the input buffer with
            # a proper slice, otherwise we get an int.
            while self._readout_data[pos:pos + 1] == self.IDLE_BYTE:
                pos += 1

            # Handle the case where the last hit is truncated in the original
            # readout data. In this case we put the thing aside in the
            # extra_bytes class member so that, potentially, we have the data
            # available to be matched with the beginning of the next readout.
            if pos + self.HIT_CLASS._SIZE >= len(self._readout_data):
                data = self._readout_data[pos:]
                logger.warning(f'Found {len(data)} byte(s) of truncated hit data '
                               f'({data}) at the end of the readout.')
                if self.is_valid_hit_start_byte(data[0:1]):
                    logger.info('Valid start byte, extra bytes set aside for next readout!')
                    self.extra_bytes = data
                break

            # Look at the first byte in the (potential) hit data---note we need to
            # address the buffer with a proper slice, otherwise we get an int.
            # If this is the beginning of a legitimate event, *for Astropix 4* this
            # should be of the form of `111xxxxx`, where the 5 LSBs encode the
            # chip ID.
            start_byte = self._readout_data[pos:pos + 1]
            if not self.is_valid_hit_start_byte(start_byte):
                logger.warning(f'Starting byte for hit data @ position {pos} is 0b{ord(start_byte):08b}')
                offset = 1
                while not self.is_valid_hit_start_byte(self._readout_data[pos + offset:pos + offset + 1]):
                    offset += 1
                orphan_bytes = self._readout_data[pos:pos + offset]
                logger.warning(f'{len(orphan_bytes)} orphan bytes found ({orphan_bytes})...')
                if extra_bytes is not None:
                    logger.info('Trying to re-assemble the hit across readouts...')
                    data = extra_bytes + orphan_bytes
                    print(len(data))
                    if len(data) == self.HIT_CLASS._SIZE:
                        logger.warning(f'Total size matches!')
                    print(data)
                pos += offset

            data = self._readout_data[pos:pos + self.HIT_CLASS._SIZE]
            # Reverse the bit order in the hit data.
            data = reverse_bit_order(data)
            hits.append(self.HIT_CLASS(data, self.readout_id, self.timestamp))
            pos += self.HIT_CLASS._SIZE
            while self._readout_data[pos:pos + 1] == self.IDLE_BYTE:
                pos += 1
        return hits

    def __str__(self) -> str:
        """String formatting.
        """
        return f'{self.__class__.__name__}({len(self._readout_data)} bytes, ' \
               f'readout_id = {self.readout_id}, timestamp = {self.timestamp} ns)'


class AstroPix4Readout(AbstractAstroPixReadout):

    """Class describing an AstroPix 4 readout.
    """

    HIT_CLASS = AstroPix4Hit
    _UID = 4000


__READOUT_CLASSES = (AstroPix4Readout, )
__READOUT_CLASS_DICT = {readout_class.uid(): readout_class for readout_class in __READOUT_CLASSES}


def uid_to_readout_class(uid: int) -> type:
    """Return the readout class corresponding to a given unique ID.

    Arguments
    ---------
    uid : int
        The unique ID of the readout class.
    """
    if uid not in __READOUT_CLASS_DICT:
        raise RuntimeError(f'Unknown readout class with identifier {uid}')
    return __READOUT_CLASS_DICT[uid]
