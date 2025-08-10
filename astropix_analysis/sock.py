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

"""Network facilities for moitoring applications.
"""

import socket
import struct


DEFAULT_MULTICAST_GROUP = '224.1.1.1'
DEFAULT_MULTICAST_PORT = 5007
DEFAULT_MAX_PACKET_SIZE = 65535


class MulticastSender(socket.socket):

    """
    """

    def __init__(self, group: str = DEFAULT_MULTICAST_GROUP, port: int = DEFAULT_MULTICAST_PORT):
        """
        """
        super().__init__(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self._address = (group, port)

    def send(self, data: bytes) -> int:
        """
        """
        return self.sendto(data, self._address)


class MulticastReceiver(socket.socket):

    """
    """

    def __init__(self, readout_class: type, group: str = DEFAULT_MULTICAST_GROUP,
                 port: int = DEFAULT_MULTICAST_PORT):
        """
        """
        super().__init__(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.bind(('', port))  # Bind to all interfaces on port
        _mreq = struct.pack('4sl', socket.inet_aton(group), socket.INADDR_ANY)
        self.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, _mreq)
        self._readout_class = readout_class

    def receive(self, max_size: int = DEFAULT_MAX_PACKET_SIZE):
        """
        """
        # The return value of the recvfrom() call is a pair (bytes, address) where
        # bytes is a bytes object representing the data received and address is
        # the address of the socket sending the data.
        data, _ = self.recvfrom(max_size)
        return self._readout_class.from_bytes(data)
