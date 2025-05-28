.. _fmt:

:mod:`~astropix_analysis.fmt` --- Data format
=============================================

The module contains the basic definition of the data structures that are involved
in writing and reading persistent astropix data.

.. warning::
    While this is supposed to be chip-version- and setup-agnostic, everything in
    the package at this time has been essentially tested on a setup with a
    single v4 astropix chip. Help is welcome to make sure that the stuff here makes
    sense in other contexts, too.

There are two main basic data structures we deal with in this module: that of a
`hit` and that of a `readout`---a hit is a single hit from an astropix chip, while
a readout is a full binary chunk of data we get from the readout board, and that
in generally contains a variable number of hits. Accordingly, we provide two
abstract base classes:

* :class:`~astropix_analysis.fmt.AbstractAstroPixHit`
* :class:`~astropix_analysis.fmt.AbstractAstroPixReadout`

from which actual concrete classes can be derived for the different chip and DAQ
versions.

If you are in a hurry and want to have a sense of how thing works, the following
snippets illustrates the main facilities that the module provides. At data taking
time you build programmatically concrete readout objects starting from the binary
buffers that the host machine receives from the DAQ board, and you can write them
straight into an output file open in binary mode.

.. code-block:: python

    from astropix_analysis.fmt import AstroPix4Readout

    # Initialization...
    output_file = open('path/to/the/output/file', 'wb')
    readout_id = 0

    # ...and event loop
    while(True):
        # Get the data from the board.
        readout_data = astro.get_readout()
        if readout_data:
            # Note the readout_id and (internally) the timestamp, are assigned
            # by the host machine.
            readout = AstroPix4Readout(readout_data, readout_id)
            readout.write(output_file)
            readout_id += 1

You can then read the readout objects back from file and have them re-assembled
into a fully fledged instance of the proper class.

.. seealso::

    And in fact there's a few subtleties, here, dealing with the file header and
    how readout objects are read back from file, which are fully described in the
    :ref:`fileio` section.

By default, when you create a readout object, nothing fancy happens with the underlying
binary data, beside the fact that the trailing padding bytes ``b'\xff'`` are stripped
away in order to avoid writing unnecessary stuff on disk. That does not mean that
the readout object is not aware of its own structure, and in fact the base class
provides a :meth:`~astropix_analysis.fmt.AbstractAstroPixReadout.decode()` method
unpacking the binary data and returning a list of hits, so that you can do stuff
like

.. code-block:: python

    hits = readout.decode()
    for hit in hits:
        print(hit)

This can be used no matter if the readout is constructed programmatically from
some binary data or read back from file, and you can imagine using the decode
function, e.g., for

* monitoring and/or doing some sanity check during the data acquisition;
* read back the binary data from disk and convert them in a format that is more
  amenable to analysis.

.. warning::

    The decoding part is still fragile and needs to be integrated with the work
    that Grant is doing, which is almost certainly more sophisticated.


Readout structures
------------------

The vast majority of the readout machinery is coded into the abstract base class
:class:`~astropix_analysis.fmt.AbstractAstroPixReadout`. A glance at the concrete
class :class:`~astropix_analysis.fmt.AstroPix4Readout`

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: AstroPix4Readout

shows in fact that the only thing you really need to do is to redefine the
``_HIT_CLASS`` class variable, setting it to the proper type describing the hit
objects that the readout include. Note that ``_HIT_CLASS`` should be a concrete
subclass of :class:`~astropix_analysis.fmt.AbstractAstroPixHit`.
(The abstract base class has ``_HIT_CLASS = None`` and therefore should not be
instantiated.)






Module documentation
--------------------

.. automodule:: astropix_analysis.fmt
