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
from enum import IntEnum
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
    """Reverses the bit order within a bytearray.
    """
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
    # with @hitclass (and still we initialize them here to None to make the linters happy.)
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

    def dict(self) -> dict:
        """Return the hit content as a dict---this will be essentially identical
        to the ``__dict__`` dunder method, except for the order of the field.

        .. warning::
          This will be slow, so do not abuse it. It is good for printing :-)
        """
        _dict = {key: getattr(self, key) for key in self.ATTRIBUTE_NAMES}
        _dict['raw_data'] = self._data
        return _dict

    def __str__(self) -> str:
        """String formatting.
        """
        return f'{self.__class__.__name__}'\
               f"({', '.join(f'{key} = {value}' for key, value in self.dict().items())})"


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
        'readout_id': (None, np.uint32),
        'timestamp': (None, np.uint64),
        'decoding_order': (None, np.uint8),
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
        'tot_us': (None, np.float64)
    }

    CLOCK_CYCLES_PER_US = 20.
    CLOCK_ROLLOVER = 2**17

    def __init__(self, data: bytearray, readout_id: int, timestamp: int,
                 decoding_order: int) -> None:
        """Constructor.
        """
        # pylint: disable=no-member
        super().__init__(data)
        self.decoding_order = decoding_order
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


class Decoding(IntEnum):

    """Enum class for all the possible issue that can happen during decoding.

    * ``ORPHAN_BYTES_MATCHED``: the readout has orphan bytes at the beginning that
      were succesfully matched with the extra bytes from the previous readout;
    * ``ORPHAN_BYTES_DROPPED``: the readout has orphan bytes at the beginning that
      we were not able to match with the extra bytes from the previous readout;
    * ``ORPHAN_BYTES_NOT_USED``: the readout has orphan bytes at the beginning
      that we could not use because the previous readout had no extra bytes;
    * ``VALID_EXTRA_BYTES``: the readout had extra bytes at the end, starting
      with a valid start-hit byte, that could be potentially matched with the
      beginning of the next buffer;
    * ``INVALID_EXTRA_BYTES``: the readout had extra bytes at the end, but since
      the first byte is not a valid start-hit byte, these cannot effectively be used;
    * ``INCOMPLETE_DATA_DROPPED``: the readout had incomplete hit data somewhere
      that we had to drop.
    """

    ORPHAN_BYTES_MATCHED = 0
    ORPHAN_BYTES_DROPPED = 1
    ORPHAN_BYTES_NOT_USED = 2
    VALID_EXTRA_BYTES = 3
    INVALID_EXTRA_BYTES = 4
    INCOMPLETE_DATA_DROPPED = 5
    FATAL_ERROR = 6


class DecodingStatus:

    """Small class representing the status of a readout decoding.
    """

    def __init__(self) -> None:
        """Constructor.
        """
        self._status_code = 0

    def __bool__(self):
        """Evaluate the status as a bool.

        This implements the simple semantics `if(status)` to check if any of the
        error bytes is set.
        """
        return self._status_code > 0

    def set(self, bit: Decoding) -> None:
        """Set a status bit.
        """
        self._status_code |= (1 << bit)

    def __getitem__(self, bit: Decoding) -> bool:
        """Retrieve the value of a status bit.
        """
        return (self._status_code >> bit) & 0x1

    def __str__(self) -> str:
        """String formatting.
        """
        text = f'DecodingStatus {hex(self._status_code)} ({bin(self._status_code)})'
        for bit in Decoding:
            text = f'{text}\n{bit.name.ljust(25, ".")} {self[bit]}'
        return text


class ByteType(IntEnum):

    """Enum class used to keep track of the byte types within a readout.

    The main purpose of this utility class is to be able to pretty-print readout
    raw data in order to debug the decoding process.

    * ``NOT_ASSIGNED``: bit not assigned (this should never happen unless the readout
      cannot be properly decoded);
    * ``PADDING``: padding byte;
    * ``IDLE``: idle byte;
    * ``HIT_START``: byte signaling the start of a hit (e.g., ``0xe0`` for chipi_id = 0);
    * ``HIT``: the byte is part of a valid hit (but not the start byte);
    * ``EXTRA``: the byte is an extra byte at the end of the readout, and possibly
      the initial part of a valid hit that is split across readouts;
    * ``ORPHAN``: the byte is an orphan byte at the beginning of the readout, and
      we might be able to reassemble with the extra bytes from the previous readout;
    * ``DROPPED``: the byte could not be assigned to a valid hit and was dropped.
    """

    NOT_ASSIGNED = 0
    PADDING = 1
    IDLE = 2
    HIT_START = 3
    HIT = 4
    EXTRA = 5
    ORPHAN = 6
    DROPPED = 7

    @classmethod
    def _fmt(cls, byte: str, *escape_codes: int) -> str:
        """Format a single byte using standard ANSI escape sequences for colors
        and formatting.

        Note we always append a reset escape sequence at the end---this will have
        the terminal working a little bit harder, but we are relieved from the
        responsibility to put the terminal back in the original state. (And this
        will never be used in CPU-intensive contexts, anyway.)

        Common color codes:

        | Color   | Code |
        | ------- | ---- |
        | Black   | `30` |
        | Red     | `31` |
        | Green   | `32` |
        | Yellow  | `33` |
        | Blue    | `34` |
        | Magenta | `35` |
        | Cyan    | `36` |
        | White   | `37` |
        | Reset   | `0`  |

        Common background color codes:

        | Color   | Code |
        | ------- | ---- |
        | Black   | `40` |
        | Red     | `41` |
        | Green   | `42` |
        | Yellow  | `43` |
        | Blue    | `44` |
        | Magenta | `45` |
        | Cyan    | `46` |
        | White   | `47` |

        Common text modifiers:

        | Style         | Code |
        | ------------- | ---- |
        | Reset         | `0`  |
        | Bold          | `1`  |
        | Faint         | `2`  |
        | Italic        | `3`  |
        | Underline     | `4`  |
        | Blink         | `5`  |
        | Reverse       | `7`  |
        | Conceal       | `8`  |
        | Strikethrough | `9`  |
        """
        return f'\033[{";".join([str(code) for code in escape_codes])}m{byte}\033[0m'

    @classmethod
    def format_byte(cls, byte: str, byte_type) -> str:
        """Format a single byte according to its type.
        """
        if byte_type == cls.HIT_START:
            return cls._fmt(byte, 31, 47)
        if byte_type == cls.HIT:
            return cls._fmt(byte, 30, 47)
        if byte_type == cls.IDLE:
            return cls._fmt(byte, 33)
        if byte_type == cls.DROPPED:
            return cls._fmt(byte, 9)
        if byte_type in (cls.EXTRA, cls.ORPHAN):
            return cls._fmt(byte, 35)
        return byte


def readoutclass(cls: type) -> type:
    """Small decorator to support automatic generation of concrete hit classes.

    Decorating concrete readout classes with this allows for some minimal checks
    on the class definition---note this is only done one, when the class is defined
    and not at runtime (every time a class instance is created.)
    """
    # pylint: disable=protected-access
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
    return cls


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
        # Initialize all the status variable for the decoding.
        self._decoded = False
        self._decoding_status = DecodingStatus()
        self._extra_bytes = None
        self._byte_mask = np.zeros(len(self._readout_data), dtype=int)
        self._hits = []

    @abstractmethod
    def decode(self, extra_bytes: bytes = None) -> list[AbstractAstroPixHit]:
        """Placeholder for the decoding function---this needs to be reimplemented
        in derived classes.
        """

    def data(self) -> bytes:
        """Return the underlyng binary data.
        """
        return self._readout_data

    def decoded(self) -> bool:
        """Return True if the readout has been decoded.
        """
        return self._decoded

    def decoding_status(self) -> bool:
        """Return the full decodin status.
        """
        return self._decoding_status

    def extra_bytes(self) -> bytes:
        """Return the extra bytes, if any, at the end of the readout (None if
        there are no extra bytes).
        """
        return self._extra_bytes

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

    def _add_hit(self, hit_data: bytes, reverse: bool = True) -> None:
        """Add a hit to readout.

        This will be typically called during the readout decoding.
        """
        # pylint: disable=not-callable
        if reverse:
            hit_data = reverse_bit_order(hit_data)
        decoding_order = len(self._hits)
        hit = self.HIT_CLASS(hit_data, self.readout_id, self.timestamp, decoding_order)
        self._hits.append(hit)

    def hex(self) -> str:
        """Return a string with the hexadecimal representation of the underlying
        binary data (two hexadecimal digits per byte).
        """
        return self._readout_data.hex()

    def pretty_hex(self):
        """Return a pretty version of the hexadecimal representation, where the
        hit portion of the readout are colored.
        """
        # pylint: disable=protected-access
        # This uses the underlying ``_byte_mask``, so we have to make sure the
        # thing has been decoded.
        if not self.decoded():
            self.decode()
        hex_bytes = self.hex()
        text = ''
        for i, byte_type in enumerate(self._byte_mask):
            byte = hex_bytes[i * 2:i * 2 + 2]
            text = f'{text}{ByteType.format_byte(byte, byte_type)}'
        return text

    def pretty_print(self) -> str:
        """Full, glorious pretty print of the readout object.
        """
        text = f'{self}\nRaw: {self.data()}\nHex: {self.pretty_hex()}\n\n'
        for hit in self.decode():
            text = f'{text}{hit}\n'
        text = f'{text}\n{self.decoding_status()}'
        return text

    def __str__(self) -> str:
        """String formatting.
        """
        return f'{self.__class__.__name__}({len(self._readout_data)} bytes, ' \
               f'readout_id = {self.readout_id}, timestamp = {self.timestamp} ns)'


@readoutclass
class AstroPix4Readout(AbstractAstroPixReadout):

    """Class describing an AstroPix 4 readout.
    """

    HIT_CLASS = AstroPix4Hit
    _UID = 4000
    DEFAULT_START_BYTE = bytes.fromhex('e0')

    @staticmethod
    def is_valid_start_byte(byte: bytes) -> bool:
        """Return True if the byte is a valid start byte for Astropix4 hit.

        This, effectively, entiles to make sure that the byte is of the form `111xxxxx`,
        where the 5 least significant bits are the chip id.

        .. note::
          This assume the byte is before the bit order is reverse, i.e., this operates
          in the space of the data stream from the Nexys board. The rational for
          this is that all the error checking happens at the readout level, before
          the bit order is reversed and before the hit is even created.

        .. warning::
          We have an amusing edge case, here, in that 0xff is both the padding byte
          and a valid start byte for Astropix 4. We should probably put some thought
          into this, but we are tentatively saying that 0xff is *not* a valid
          start byte for a hit, in order to keep the decoding as simple as possible.
        """
        return byte != AbstractAstroPixReadout.PADDING_BYTE and ord(byte) >> 5 == 7

    @staticmethod
    def _invalid_start_byte_msg(start_byte: bytes, position: int) -> str:
        """Generic error message for an invalid start byte.
        """
        return f'Invalid start byte {start_byte} (0b{ord(start_byte):08b}) @ position {position}'

    def decode(self, extra_bytes: bytes = None) -> list[AbstractAstroPixHit]:  # noqa: C901
        """Astropix4 decoding function.

        .. note::
          Note that you always need to addess single bytes in the data stream with
          a proper slice, as opposed to an integer, i.e., `data[i:i + 1]` instead
          of `data[i]`, because Python will return an integer, otherwise.

        Arguments
        ---------
        extra_bytes : bytes
            Optional extra bytes from the previous readout that might be re-assembled
            together with the beginning of this readout.
        """
        # pylint: disable=not-callable, protected-access, line-too-long, too-many-branches, too-many-statements # noqa
        # If the event has been already decoded, return the list of hits that
        # has been previsouly calculated.
        if self._decoded:
            return self._hits

        # Ready to start---the cursor indicates the position within the readout.
        self._decoded = True
        cursor = 0

        # Skip the initial idle and padding bytes.
        # (In principle we would only expect idle bytes, here, but it is a
        # known fact that we occasionally get padding bytes interleaved with
        # them, especially when operating at high rate.)
        while self._readout_data[cursor:cursor + 1] in [self.IDLE_BYTE, self.PADDING_BYTE]:
            self._byte_mask[cursor] = ByteType.IDLE
            cursor += 1

        # Look at the first legitimate hit byte---if it is not a valid hit start
        # byte, then we might need to piece the first few bytes of the readout
        # with the leftover of the previous readout.
        byte = self._readout_data[cursor:cursor + 1]
        if not self.is_valid_start_byte(byte):
            logger.warning(self._invalid_start_byte_msg(byte, cursor))
            offset = 1
            # Move forward until we find the next valid start byte.
            while not self.is_valid_start_byte(self._readout_data[cursor + offset:cursor + offset + 1]):  # noqa: E501
                offset += 1
            # Note we have to strip all the idle bytes at the end, if any.
            # Also note the Jedi trick here: we first set all the bytes in the
            # portion to idle...
            self._byte_mask[cursor:cursor + offset] = ByteType.IDLE
            orphan_bytes = self._readout_data[cursor:cursor + offset].rstrip(self.IDLE_BYTE)
            # ... and then we override the bit mask in the actual orphan part.
            self._byte_mask[cursor:cursor + len(orphan_bytes)] = ByteType.ORPHAN
            logger.info(f'{len(orphan_bytes)} orphan bytes found ({orphan_bytes})...')
            if extra_bytes is not None:
                logger.info('Trying to re-assemble the hit across readouts...')
                data = extra_bytes + orphan_bytes
                if len(data) == self.HIT_CLASS._SIZE:
                    logger.info('Total size matches---we got a hit!')
                    self._add_hit(data)
                    self._decoding_status.set(Decoding.ORPHAN_BYTES_MATCHED)
                else:
                    self._decoding_status.set(Decoding.ORPHAN_BYTES_DROPPED)
            else:
                self._decoding_status.set(Decoding.ORPHAN_BYTES_NOT_USED)
            cursor += offset

        # And now we can proceed with business as usual.
        while cursor < len(self._readout_data):
            # Skip all the idle bytes and the padding bytes that we encounter.
            # (In principle we would only expect idle bytes, here, but it is a
            # known fact that we occasionally get padding bytes interleaved with
            # them, especially when operating at high rate.)
            while self._readout_data[cursor:cursor + 1] in [self.IDLE_BYTE, self.PADDING_BYTE]:
                self._byte_mask[cursor] = ByteType.IDLE
                cursor += 1

            # Check if we are at the end of the readout.
            if cursor == len(self._readout_data):
                return self._hits

            # Handle the case where the last hit is truncated in the original readout data.
            # If the start byte is valid we put the thing aside in the extra_bytes class
            # member so that, potentially, we have the data available to be matched
            # with the beginning of the next readout.
            if cursor + self.HIT_CLASS._SIZE >= len(self._readout_data):
                data = self._readout_data[cursor:]
                self._byte_mask[cursor:] = ByteType.EXTRA
                logger.warning(f'Found {len(data)} byte(s) of truncated hit data '
                               f'({data}) at the end of the readout.')
                if self.is_valid_start_byte(data[0:1]):
                    self._byte_mask[cursor] = ByteType.HIT_START
                    logger.info('Valid start byte, extra bytes set aside for next readout!')
                    self._extra_bytes = data
                    self._decoding_status.set(Decoding.VALID_EXTRA_BYTES)
                else:
                    self._decoding_status.set(Decoding.INVALID_EXTRA_BYTES)
                break

            # At this point we do expect a valid start hit for the next event.
            # If this is not the case, then there is more logic that we need to have.
            # (And I'll raise a RuntimeError, for the moment, but this might warrant
            # a custom exception.)
            byte = self._readout_data[cursor:cursor + 1]
            if not self.is_valid_start_byte(byte):
                logger.error(self._invalid_start_byte_msg(byte, cursor))
                self._decoding_status.set(Decoding.FATAL_ERROR)
                return self._hits

            # We have a tentative 8-byte word, with the correct start byte,
            # representing a hit.
            data = self._readout_data[cursor:cursor + self.HIT_CLASS._SIZE]

            # Loop over bytes 1--7 (included) in the word to see whether there is
            # any additional valid start byte in the hit.
            for offset in range(1, len(data)):
                byte = data[offset:offset + 1]
                if self.is_valid_start_byte(byte):
                    # At this point we have really two cases:
                    # 1 - this is a legitimate hit containing a start byte by chance;
                    # 2 - this is a truncated hit, and the start byte signals the next hit.
                    # I don't think there is any way we can get this right 100% of the
                    # times, but a sensible thing to try is to move forward by the hit size,
                    # skip all the subsequent idle bytes and see if the next thing in line
                    # is a valid start byte. In that situation we are probably
                    # dealing with case 1.
                    forward_cursor = cursor + self.HIT_CLASS._SIZE
                    while self._readout_data[forward_cursor:forward_cursor + 1] == self.IDLE_BYTE:
                        forward_cursor += 1
                    if forward_cursor < len(self._readout_data):
                        byte = self._readout_data[forward_cursor:forward_cursor + 1]
                        if not self.is_valid_start_byte(byte):
                            # Here we are really in case 2, and there is not other thing
                            # we can do except dropping the hit.
                            logger.warning(f'Unexpected start byte {byte} @ position {cursor}+{offset}')  # noqa: E501
                            logger.warning(f'Dropping incomplete hit {data[:offset]}')
                            self._decoding_status.set(Decoding.INCOMPLETE_DATA_DROPPED)
                            self._byte_mask[cursor:cursor + offset] = ByteType.DROPPED
                            cursor = cursor + offset
                            data = self._readout_data[cursor:cursor + self.HIT_CLASS._SIZE]

            # And this should be by far the most common case.
            self._add_hit(data)
            self._byte_mask[cursor:cursor + 1] = ByteType.HIT_START
            self._byte_mask[cursor + 1:cursor + self.HIT_CLASS._SIZE] = ByteType.HIT
            cursor += self.HIT_CLASS._SIZE
            while self._readout_data[cursor:cursor + 1] == self.IDLE_BYTE:
                self._byte_mask[cursor] = ByteType.IDLE
                cursor += 1
        return self._hits


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
