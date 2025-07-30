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


File header
-----------

The :class:`~astropix_analysis.fileio.FileHeader` is designed to encode and write
to a binary file some generic content, using json as the serialization format.
The information about the content length is included at write time, so that thing
can be reliably read back with no further input. The basic I/O routines read:

.. literalinclude:: ../astropix_analysis/fileio.py
   :pyobject: FileHeader.write

.. literalinclude:: ../astropix_analysis/fileio.py
   :pyobject: FileHeader.read

There are no real requirements on the file header content, beside the fact that
we assume it can be json-encoded. The typical use case would be for the content
to be an arbitrary, possibly nested, Python dictionary, and as long as you only
include native Python types in it (e.g., strings, integers, floats or contained
with simple types in them) you should be ok. More complex data types can in principle
be included, but in general you would have to provide a custom serialized.

.. warning::

   Keep in mind it is the file header that is responsible for writing the magic
   number to the output file, so if you do want a properly formatted astropix
   file you will need a header object---be it populated or not.


File objects
------------

The class :class:`~astropix_analysis.fileio.AstroPixBinaryFile` provides a simple
read interface to astropix binary files, implementing the context-manager and the
iterator protocols. The recommended way to operate with astropix binary files is
the idiom

.. code-block:: python

   from astropix_analysis.fmt import AstroPixBinaryFile, AstroPix4Readout

   with AstroPixBinaryFile(AstroPix4Readout).open('path/to/my/file.apx') as input_file:
       # Note the header is automatically read and de-serialized, and you have
       # full access to the information in there.
       print(input_file.header)

       # At this point you can iterate over the readout objects in the input file,
       # which will retrieve the readout objects in there one at a time, in the
       # form of fully-fledged instances of concrete AbstractAstroPixReadout
       # subclasses.
       for readout in input_file:
           for hit in readout.decode():
               # And now you can do something useful with the hits in the readout.

.. note::

   You will notice that you have to provide the class of the readout structures
   that the binary file contains when you open it. While in principle we could
   put this information in the file header at write time and figure out everything
   auto-magically at read time, I thought we would defer this level of cleverness
   to after we have completely thought through the issue of what we want to include
   in the headers, and how we deal with evolving versions of the underlying objects.

For completeness, the :class:`~astropix_analysis.fileio.AstroPixBinaryFile`
provides a :meth:`~astropix_analysis.fileio.AstroPixBinaryFile.read_file_header`
static method that peeks into the file and return the header without entering
into the readout part (it goes without saying, in this case the information about
the readout class is not needed).


Format conversion
-----------------

We leverage the ``astropy.table`` module to allow converting binary astropix files
to several different file formats more amenable to typical offline
analysis.

The workhorse converter is :meth:`~astropix_analysis.fileio.apx_convert`, which
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

   # Convert a binary astropix file to HDF5...
   output_file_path = apx_convert('path/to/apx/file', AstroPix4Readout, 'hdf5')

   # ... and read it back in the form of an astropy table (+ header)
   header, table = apx_load(output_file_path)

Note that we keep track of the underlying :class:`~astropix_analysis.fileio.FileHeader`
in the process, and when we load back the data we should have access to all the
information in the original binary file.


Module documentation
--------------------

.. automodule:: astropix_analysis.fileio
