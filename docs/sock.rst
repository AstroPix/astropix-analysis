.. _sock:

:mod:`~astropix_analysis.sock` --- Multicast
============================================

This module provides simple facilities to multicast packets over the network
for monitoring applications, via two classes:

* :class:`~astropix_analysis.sock.MulticastSender`
* :class:`~astropix_analysis.sock.MulticastReceiver`

A DAQ (data acquisition system) saving to disk but also optionally broadcasting
binary packets to multiple passive monitors is a classic fit for UDP multicast.
The DAQ can send out packets efficiently (one-to-many, with no duplication) and
minimal overhead, without needing to know who is listening. One or more optional
monitoring applications can join or leave the group without disrupting the data
acquisition.

In a nutshell, the sender sends packets to a special IP address in the multicast
range (224.0.0.0 to 239.255.255.255 in IPv4), and receivers can join the multicast
group at that address. Routers (if configured) distribute the packet only to
networks with group members.

.. note::

   The `administratively scoped multicast is` a block of multicast addresses that
   are not routed globally, and are intended to be used and managed locally by
   an organization or enterprise. This is defined to be 239.0.0.0 -- 239.255.255.255
   in `RFC 2365 <https://datatracker.ietf.org/doc/html/rfc2365>`_.

   239.1.1.1 is a typical choice for local multicast applications.

   UDP ports range from 0 to 65535. Although there is no reserved range just for
   multicast it is good practice to avoid ports below 1024 and ephemeral ports
   above 49152. Ports in the range 5000--6000 are a typical choice for custom
   applications.


What you will want to do in typical applications is fairly simple. On the DAQ
side you will have something along the lines of

.. code-block::

   from astropix_analysis.sock import MulticastSender

   # Create a socket to broadcast packets over the network.
   sender = MulticastSender(group='239.1.1.1', port=5007)

    while True: # This is your data collection loop.
        # ...
        sender.send_readout(readout)

while on the monitoring side all you need to intercept packets is

.. code-block::

   from astropix_analysis.fmt import AstroPix4Readout
   from astropix_analysis.sock import MulticastReceiver

   # Create the receiver socket---note the receiver needs to know
   # the readout type you are expecting in order to be able to
   # reassemble the readout objects from the binary stream.
   receiver = MulticastReceiver(AstroPix4Readout, group='239.1.1.1', port=5007)

    while True:
        readout = receiver.receive()
        print(readout)
        hits = readout.decode()
        for hit in hist:
            print(hit)


Module documentation
--------------------

.. automodule:: astropix_analysis.sock

