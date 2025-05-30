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
``HIT_CLASS`` class variable, setting it to the proper type describing the hit
objects that the readout include. Note that ``HIT_CLASS`` should be a concrete
subclass of :class:`~astropix_analysis.fmt.AbstractAstroPixHit`; this ensures that
any class instance is able to decode itself. (The abstract base class has
``HIT_CLASS = None`` and therefore should not be instantiated.)

The class constructor

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: AbstractAstroPixReadout.__init__

accepts three arguments, namely:

* the underlying binary data, coming from the DAQ board;
* a readout identifier, that is generally assigned by the host machine with the
  data acquisition event loop;
* a timestamp, also assigned by the host machine, expressed as nanoseconds since
  the epoch (January 1, 1970, 00:00:00 (UTC)).

When instantiating readout object programmatically (e.g., in the data acquisition
event loop), you typically can omit the ``timestamp`` argument, as the latter
gets automatically latched within the class constructor, i.e.

.. code-block:: python

   readout = AstroPix4Readout(readout_data, readout_id)

On the other hand, when a readout object is read back from file, the signature with
all three parameters is obviously used.


Hit structures
--------------

Likewise, all concrete hit classes derive from :class:`~astropix_analysis.fmt.AbstractAstroPixHit`,
although defining concrete subclasses is slightly more complex in this case, as
a the following definition shows.

.. literalinclude:: ../astropix_analysis/fmt.py
   :pyobject: AstroPix4Hit

At the very minimum you have to:

* override the ``_LAYOUT`` class variable: this is a dictionary mapping the name
  of the fields within each hit frame to their width in bits (it goes without
  saying that the fields might be defined in the same order they occur in the
  frame);
* override the ``_ATTRIBUTES`` class variable, which generally includes all the
  fields defined in the ``_LAYOUT``, plus any additional quantity that is
  calculated from the aforementioned fields when the class is instantiated;
* override the ``SIZE`` class variable with the overall size of the overall hit
  frame in bytes.

.. note::

   The ``SIZE`` class variable can be in principle calculated from the ``_LAYOUT``
   by just summing up all the field widths, and in fact the
   :meth:`~astropix_analysis.fmt.AbstractAstroPixHit._calculate_size()` static
   method does just that, but we need the cope with the nuisance of having to type
   the boilerplate line

   .. code-block:: python

      SIZE = AbstractAstroPixHit._calculate_size(_LAYOUT)

   each time in the class definition in order to not recalculate the same thing
   at runtime over and over again for each class instance.

The layout machinery is designed to avoid addressing the underlying binary data
with hard-coded indices and make it easier to reason about the hist structure.
It leverages under the hood the small convenience class
:class:`~astropix_analysis.fmt.BitPattern`.

Hit objects come equipped with all the facilities to represent themselves in
different formats, including, e.g., text and comma-separated values.

.. code-block:: python

    print(hit)
    AstroPix4Hit(chip_id=0, payload=7, row=0, column=5, ts_neg1=1, ts_coarse1=5167,
                 ts_fine1=3, ts_tdc1=0, ts_neg2=0, ts_coarse2=5418, ts_fine2=6,
                 ts_tdc2=0, ts_dec1=49581, ts_dec2=52836, tot_us=162.75, readout_id=0,
                 timestamp=1748518075318049813)

    print(hit.text_header())
    chip_id,payload,row,column,ts_neg1,ts_coarse1,ts_fine1,ts_tdc1,ts_neg2,ts_coarse2,ts_fine2,ts_tdc2,ts_dec1,ts_dec2,tot_us,readout_id,timestamp

    print(hit.to_csv())
    0,7,0,5,1,5167,3,0,0,5418,6,0,49581,52836,162.75,0,1748518075318049813



Module documentation
--------------------

.. automodule:: astropix_analysis.fmt
