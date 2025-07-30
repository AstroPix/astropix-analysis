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
`readout` and that of a `hit`---a hit is a single hit from an astropix chip, while
a readout is a full binary chunk of data we get from the readout board, and that
in generally contains a variable number of hits. Accordingly, we provide two
abstract base classes:

* :class:`~astropix_analysis.fmt.AbstractAstroPixReadout`
* :class:`~astropix_analysis.fmt.AbstractAstroPixHit`

from which actual concrete classes can be derived for the different chip and DAQ
versions.

If you are in a hurry and want to have a sense of how thing works, the following
snippets illustrates the main facilities that the module provides. At data taking
time you build programmatically concrete readout objects starting from the binary
buffers that the host machine receives from the DAQ board, and you can write them
straight into an output file

.. code-block:: python

    from astropix_analysis.fileio import FileHeader, apx_open
    from astropix_analysis.fmt import AstroPix4Readout

    # Initialization...
    header = FileHeader(AstroPix4Readout)
    with open('path/to/the/output/file', 'wb', header) as output_file:

        # ...and event loop
        readout_id = 0
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


Readout structures
------------------

The vast majority of the readout machinery is coded into the abstract base class
:class:`~astropix_analysis.fmt.AbstractAstroPixReadout`. A glance at the concrete
class :class:`~astropix_analysis.fmt.AstroPix4Readout` shows in fact that the only
things you really need to do is to

* define the ``HIT_CLASS`` class variable: this indicates which type of hit  structures
  the readout contains. (Note that ``HIT_CLASS`` should be a concrete subclass of
  :class:`~astropix_analysis.fmt.AbstractAstroPixHit`; this ensures that any class
  instance is able to decode itself.)
* define ``_UID`` class variable: this gets included in the header of Astropix
  binary files and guarantees that we have all the information that we need to
  parse binary data. Note that, in order to be able to read old files, the contract
  here is that hit structures with a given ``_UID`` never change, and we create
  new structures with different ``_UID`` instead.
* overload the ``decode()`` abstract method, responsible from extracting the hits
  form the readout. (This is typically where most of the logic, and code, is needed.)

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: AstroPix4Readout


The constructor of the base class accepts three arguments, namely:

* the underlying binary data, coming from the DAQ board;
* a readout identifier, that is generally assigned by the host machine with the
  data acquisition event loop;
* a timestamp, also assigned by the host machine, expressed as nanoseconds since
  the epoch (January 1, 1970, 00:00:00 (UTC)).

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: AbstractAstroPixReadout.__init__


When instantiating readout object programmatically (e.g., in the data acquisition
event loop), you typically can omit the ``timestamp`` argument, as the latter
gets automatically latched within the class constructor, i.e.

.. code-block:: python

   readout = AstroPix4Readout(readout_data, readout_id)

On the other hand, when a readout object is read back from file, the signature with
all three parameters is obviously used.


Decoding
~~~~~~~~

Readout structures are equipped with all the necessary tool to keep track of the
full decoding process, particularly through the following class members:

* ``_decoded``: a bool flag that is asserted once the readout has been decoded,
  so that additional calls to the ``decode()`` method return the pre-compiled list
  of hits without running the decoding again;
* ``_decoding_status``: a custom object containing all the information about the
  decoding process---see :class:`~astropix_analysis.fmt.Decoding` and
  :class:`~astropix_analysis.fmt.DecodingStatus`;
* ``_extra_bytes``: the possible extra bytes at the end of the readout, that we might
  be able to match with the beginning of the next readout;
* ``_byte_mask``: a mask mapping each byte in the readout to its own role in the
  readout--see :class:`~astropix_analysis.fmt.ByteType`.

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: Decoding

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: ByteType


Hit structures
--------------

Likewise, all concrete hit classes derive from :class:`~astropix_analysis.fmt.AbstractAstroPixHit`,
although defining concrete subclasses is slightly more complex in this case, as
a the following definition shows.

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: AstroPix4Hit

In a nutshell, all you have to do is:

* override the ``_SIZE`` class variable: this indicates the total size in bytes of the
  binary buffer, as it comes from the hardware, representing a hit;
* override the ``_LAYOUT`` class variable: this is a dictionary mapping the name
  of each field to the corresponding slice in the input binary buffer and the desired
  data type when the things is to be written to persistent memory (it goes without
  saying that the fields might be defined in the same order they occur in the
  frame); for instance, the specification ``'column': (slice(8, 16), np.uint8)``
  is meant to indicate that the 8 bits ``8:16`` in the input buffer need to be
  mapped into a class attribute ``hit.column`` and the latter, when written to
  binary output, is represented as a 8-bit unsigned integer; when the slice is
  ``None``, that means that the corresponding field is not to be read from the
  input binary buffer, but it is calculated in the constructor based on the row
  quantities (and, still, the output type is obviously relevant);
* decorate the concrete class with the ``@hitclass`` decorator, which calculates
  at the time of the type creation (and not every time a class instance is created)
  some useful quantities that allows for streamlining the hit manipulation;

The layout machinery is designed to avoid addressing the underlying binary data
with hard-coded indices and make it easier to reason about the hist structure.
It leverages under the hood the small convenience class
:class:`~astropix_analysis.fmt.BitPattern`.

Hit objects come equipped with all the facilities to represent themselves, retrieve
a subset of the attributes in a programmatic fashion, and interface to astropy
table to support structured binary output:

.. code-block:: python

    print(hit)
    AstroPix4Hit(chip_id = 0, payload = 7, readout_id = 9, timestamp = 1753255537403740300,
                 decoding_order = 0, row = 0, column = 9, ts_neg1 = 0, ts_coarse1 = 14381,
                 ts_fine1 = 3, ts_tdc1 = 0, ts_neg2 = 1, ts_coarse2 = 11055, ts_fine2 = 5,
                 ts_tdc2 = 0, ts_dec1 = 97869, ts_dec2 = 102825, tot_us = 247.8,
                 raw_data = b'\x07\x02\\\x16\xb0k/\xa0')

    print(hit.attribute_values(['chip_id', row', 'column']))
    [0, 0, 9]


Module documentation
--------------------

.. automodule:: astropix_analysis.fmt
