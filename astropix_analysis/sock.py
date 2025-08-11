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

"""Network facilities for monitoring applications.
"""

import socket
import struct

from astropix_analysis import logger
from astropix_analysis.fmt import AbstractAstroPixReadout


# Note this is parte of the administratively scoped block.
DEFAULT_MULTICAST_GROUP = '239.1.1.1'
DEFAULT_MULTICAST_PORT = 5007


class MulticastSender(socket.socket):

    """Simple socket class to multicast packets over the network.

    Arguments
    ---------
    group : str
        The multicast group.

    port : int
        The multicast port.

    ttl : int
        The TTL (time-to-live) for multicast packets. TTL controls how far multicast
        packets can go. (Each router decrements the TTL by 1, and when TTL hits 0,
        the packet is dropped.) Common TTL values are 1 (stay on the local subnet),
        2 (allow routing to directly connected subnets), or >2 (allow more hops)
    """

    def __init__(self, group: str = DEFAULT_MULTICAST_GROUP,
                 port: int = DEFAULT_MULTICAST_PORT, ttl: int = 2) -> None:
        """Constructor.
        """
        # Since the underlying socket is is not bound to any specific address,
        # we need to cache the address information here in order to have it
        # available in ``sendto()`` calls.
        self._address = (group, port)
        logger.info(f'Creating {self.__class__.__name__} with address {self._address}...')
        # AF_INET specify the IPv4 address family, SOCK_DGRAM the socket type,
        # and IPPROTO_UDP specifies the UDP protocol.
        super().__init__(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Here we are defining the TTL setting for multicast packets
        self.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def send_data(self, data: bytes) -> int:
        """Send a packet over the network.

        Arguments
        ---------
        data : bytes
            The data to be sent.
        """
        return self.sendto(data, self._address)

    def send_readout(self, readout: AbstractAstroPixReadout) -> int:
        """Send a readout over the network.

        Arguments
        ---------
        readout : AbstractAstroPixReadout
            The readout to be sent.
        """
        return self.send_data(readout.to_bytes())


class MulticastReceiver(socket.socket):

    """Simple socket class to receive multicast packets.

    Arguments
    ---------
    readout_class : type
        The type of readout objects we are expecting (e.g., `AstroPix4Readout``).

    group : str
        The multicast group.

    port : int
        The multicast port.
    """

    DEFAULT_MAX_PACKET_SIZE = 65535

    def __init__(self, readout_class: type, group: str = DEFAULT_MULTICAST_GROUP,
                 port: int = DEFAULT_MULTICAST_PORT) -> None:
        """Constructor.
        """

        logger.info(f'Creating {self.__class__.__name__} with address ({group}, {port})...')
        # AF_INET specify the IPv4 address family, SOCK_DGRAM the socket type,
        # and IPPROTO_UDP specifies the UDP protocol.
        super().__init__(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Bind to all interfaces on port
        self.bind(('', port))
        _mreq = struct.pack('4sl', socket.inet_aton(group), socket.INADDR_ANY)
        self.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, _mreq)
        self._readout_class = readout_class

    def receive(self, max_size: int = DEFAULT_MAX_PACKET_SIZE) -> AbstractAstroPixReadout:
        """Wait for a packet to be available, read the binary data and
        return the corresponding readout object.
        """
        # The return value of the recvfrom() call is a pair (bytes, address) where
        # bytes is a bytes object representing the data received and address is
        # the address of the socket sending the data.
        data, _ = self.recvfrom(max_size)
        return self._readout_class.from_bytes(data)
