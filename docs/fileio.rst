.. _fileio:

:mod:`~astropix_analysis.fileio` --- File I/O
=============================================

This module implements all the I/O for astropix persistent data, and provides two
main classes:

* :class:`~astropix_analysis.fileio.FileHeader`
* :class:`~astropix_analysis.fileio.AstroPixBinaryFile`

in addition to the necessary facilities to read and write astropix binary files,
process them and decode the readouts to extract the hits, and save the latter
to different output formats (e.g., csv):

* :meth:`~astropix_analysis.fileio.apx_open`: open an astropix (``.apx``) binary
  file for read or write;
* :meth:`~astropix_analysis.fileio.apx_process`: process and astropix binary file,
  extract the hits and save the latter in a variety of tabular format, leveraging
  the astropy ``Table`` functionaloty;
* :meth:`~astropix_analysis.fileio.apx_load`: load back hit tabular data from file.

As usual, if you are in a rush, all you really have to know is how you create a
file and write readout objects to it

.. code-block:: python

   from astropix_analysis.fileio import FileHeader, apx_open
   from astropix_analysis.fmt import AstroPix4Readout

   # In order to create a proper binary file you do need a header, and the header
   # needs to be aware of the type of readouts that the file contains---this will
   # ensure that the file can be properly read and decoded later.
   # The optional content argument can hold any additional metadata that go in the
   # header, the only condition being that it must be a dictionary and must
   # be json-serializable (i.e., stick to simple Python types for the values).
   header = FileHeader(AstroPix4Readout, content={'creator': 'Santa Claus'})

   # apx_open() is the main interface to astropix binary files, and it is
   # loosely modeled on the Python ``open()`` builtin. Note, again, that when
   # opening a file in write mode you do need to provide a header.
   with apx_open('path/to/file.apx', 'wb', header) as output_file:
      while True: # This is your data collection loop.
         # ...
         readout.write(output_file)

and how to read back the content of an actual astropix files saved in memory---which
is even simpler

.. code-block:: python

   from astropix_analysis.fileio import apx_open

   with apx_open('path/to/file.apx') as input_file:
      # All the header information is readily available.
      print(input_file.header)

      # Note the underlying class support the iterator protocol, so that you can
      # simply loop over the readouts in the files.
      for readout in input_file:
         print(readout)
         for hit in readout.decode():
            print(hit)


File format
-----------

The basic astropix file format is defined as a binary stream, where a
`magic number <https://en.wikipedia.org/wiki/File_format#Magic_number>`_
is followed by a text header (both encoded in UTF-8) and then by the bulk of
binary data. More specifically we have

* a magic number, provisionally set to ``%APXDF`` (the pdf format, e.g., uses ``%PDF``),
  which can be used to determine whether a given file is an astropix binary file
  by just peeking at it;
* a single integer representing the length of the following (variable-size) part
  of the header, which is necessary to be able to parse the header and place the
  pointer to the current position within the file to the right place to start
  iterating over the readout objects;
* the actual header, in the form of an arbitrary set of information, json encoded;
* a sequence of readout objects, written as binary data.

The following block illustrate a realistic example of the initial part of an
astropix binary file.

.. code-block:: text

   %APXDF1^F^@^@{"readout_uid": 4000, "Voltagecard": {"thpmos": 0, "cardConf2": 0,
   "vcasc2": 1.1, "BL": 1, "cardConf5": 0, "cardConf6": 0, "vminuspix": 0.8,
   "thpix": 1.04}, "Digital": {"interrupt_pushpull": 0, "clkmux": 0, "timerend": 0,
   "slowdownldpix": 0, "slowdownldcol": 0, "maxcyc": 63, "resetckdiv": 15, "nu1": 0,
   "tdacmux": 0, "Reset": 0, "PCH": 0, "enRamPCH": 1, "nu2": 0, "enLVDSterm": 1,
   "enPLL": 1, "enLVDS": 0, "nu3": 0}, "Biasblock": {"DisHiDR": 0, "q01": 0,
   "qon0": 0, "qon1": 1, "qon2": 0, "qon3": 1}, "iDAC": {"blres": 0, "vpdac": 10,
   "vn1": 20, "vnfb": 1, "vnfoll": 2, "nu5": 0, "vndel": 30, "incp": 10, "ipvco": 0,
   "vn2": 0, "vnfoll2": 1, "vnbias": 10, "vpload": 5, "nu13": 0, "vncomp": 10,
   "vpfoll": 10, "nu16": 0, "vprec": 10, "vnrec": 10}, "vDAC": {"blpix": 568,
   "thpix": 610, "vcasc2": 625, "vtest": 682, "vinj": 170}, "Receiver": {"col0":
   206158430206, "col1": 68719476735, "col2": 68719476734, "col3": 68719476734,
   "col4": 68719476734, "col5": 68719476734, "col6": 68719476734, "col7":
   68719476734, "col8": 68719476734, "col9": 137438953466, "col10": 68719476734,
   "col11": 68719476734, "col12": 68719476734, "col13": 68719476734, "col14":
   68719476734, "col15": 68719476734}, "options": {"name": "threshold_40mV",
   "outdir": "E:/data/VPDAC_Testing_With_Grant/scan3/VPDAC_10/TuneDAC_0/Col_9",
   "yaml": "testconfig_v4_none_TuneDACs", "chipVer": 4, "showhits": false,
   "plotsave": false, "saveascsv": false, "newfilter": false, "inject": [1, 9],
   "vinj": 300.0, "analog": 0, "threshold": 40.0, "errormax": 100, "maxruns": null,
   "maxtime": 0.33333333, "timeit": false, "loglevel": "I"}}<F<FE>ܺ^@^@^@^@^@^@^@
   ^@^@^@^@^@^P^@^@^@<BC><BC><E0>P<FE><CD>^F|<C5>^@<BC><BC><BC><B<BC><BC><BC><FE>ܺ
   ^A^@^@^@^@^@^@^@^@^@^@^@^P^@^@^@<BC><BC><E0>P<92><C9>^@<8A>G^A<B<BC><BC><BC><BC>
   <BC><BC><FE>ܺ^B^@^@^@^@^@^@^@^@^@^@^@^P^@^@^@<BC><BC><E0>P2<8F>^D<DA>6^C<BC><BC>
   <BC><BC><BC><BC><FE>ܺ^C^@^@^@^@^@^@^@^@^@^@^@^P^@^@^@<BC><BC><E0>P<U+008A>



File header
-----------

The :class:`~astropix_analysis.fileio.FileHeader` is designed to encode and write
to a binary file some generic content, using json as the serialization format.

The :class:`~astropix_analysis.fileio.FileHeader` constructor requires the type
of readout we are writing to the output file, and allows for an arbitrary amount
of metadata, which are passed in to the form of a dictionary to the ``content``
argument. There are no real requirements on the file header content, beside the
fact that we assume the dictionary can be json-encoded. As long as you only
include native Python types in it (e.g., strings, integers, floats or contained
with simple types in them) you should be ok. More complex data types can in principle
be included, but in general you would have to provide a custom serialized.

.. code-block:: python

   from astropix_analysis.fileio import FileHeader
   from astropix_analysis.fmt import AstroPix4Readout

   header = FileHeader(AstroPix4Readout, content={'creator': 'Santa Claus'})

The information about the content length is included at write time, so that thing
can be reliably read back with no further input. The basic I/O routines read:

.. literalinclude:: ../astropix_analysis/fileio.py
   :pyobject: FileHeader.write

.. literalinclude:: ../astropix_analysis/fileio.py
   :pyobject: FileHeader.read


File objects
------------

The class :class:`~astropix_analysis.fileio.AstroPixBinaryFile` provides a simple
read interface to astropix binary files, implementing the context-manager and the
iterator protocols. The recommended way to operate with astropix binary files is
the idiom

.. code-block:: python

   from astropix_analysis.fileio import apx_open

   with apx_open('path/to/file.apx') as input_file:
      # All the header information is readily available.
      print(input_file.header)

      # Note the underlying class support the iterator protocol, so that you can
      # simply loop over the readouts in the files.
      for readout in input_file:
         print(readout)
         for hit in readout.decode():
            print(hit)


Readout processing
------------------

We leverage the ``astropy.table`` module to process binary astropix files and save
the decoded hits to several different file formats more amenable to typical offline
analysis.

The workhorse converter is :meth:`~astropix_analysis.fileio.apx_process`, which
internally creates an astropy table of hits looping over the input binary file,
and writes it to an output file in some of the formats that astropy supports
(e.g., csv, FITS, HDF5).

.. note::

   One important thing to notice is that, while the astropix binary I/O is readout
   based (i.e., readout objects are written one at a time), the event loop within
   the conversion function factory is set up so that readout objects are unpacked
   into hits, and the latter are written to the output file.

The function is wrapped into a command line utility, living in the ``bin`` folder,
that can be used to trigger a conversion.

Conversely, the :meth:`~astropix_analysis.fileio.apx_load` function allows to
read back the table from file. In a nutshell, the following syntax should round-trip

.. code-block:: python

   from astropix_analysis.fileio import apx_process, apx_load

   # Convert a binary astropix file to HDF5...
   output_file_path = apx_process('path/to/apx/file', 'hdf5')

   # ... and read it back in the form of an astropy table (+ header)
   header, table = apx_load(output_file_path)

Note that we keep track of the underlying :class:`~astropix_analysis.fileio.FileHeader`
in the process, and when we load back the data we should have access to all the
information in the original binary file.


Module documentation
--------------------

.. automodule:: astropix_analysis.fileio
