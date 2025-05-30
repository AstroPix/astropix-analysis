.. _fileio:

:mod:`~astropix_analysis.fileio` --- File I/O
=============================================

This module implements all the I/O for astropix persistent data, and provides two
main classes:

* :class:`~astropix_analysis.fileio.FileHeader`
* :class:`~astropix_analysis.fileio.AstroPixBinaryFile`


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

For those who are in a rush, the basic write machinery is implemented so that it
can be put to use in the following fashion:

.. code-block:: python

   from astropix_analysis.fmt import AstroPix4Readout

   # Open the output file.
   output_file = open('path/to/my/file.apx', 'wb')

   # Write the header, which can contain pretty much arbitrary information,
   # as long as the latter can be json-encoded. A python dictionary, be it nested
   # to an arbitrary level, will do as long as it does not contain too exotic structures.
   header_content = dict(version=1, stuff='hits')
   header = FileHeader(header_content)

   # ... event loop.
   readout_id = 0
   while(1):
       readout_data = astro.get_readout()
       if readout_data:
           readout = AstroPix4Readout(readout_data, readout_id)
           readout.write(output_file)
           readout_id += 1

   output_file.close()

On the input side of things, the :class:`~astropix_analysis.fileio.AstroPixBinaryFile`
class implements the context manager and iterator protocols, and the information
can be read back in the succinct form

.. code-block:: python

   from astropix_analysis.fmt import AstroPixBinaryFile, AstroPix4Readout

   with AstroPixBinaryFile(AstroPix4Readout).open('path/to/my/file.apx') as input_file:
       # Note the header is automatically read and de-serialized.
       print(input_file.header)

       # You can iterate over the readout objects in the input file.
       for readout in input_file:
           print(readout)
           for hit in readout.decode():
               print(hit)

File header
-----------

.. literalinclude:: ../astropix_analysis/fileio.py
   :pyobject: FileHeader.write

.. literalinclude:: ../astropix_analysis/fileio.py
   :pyobject: FileHeader.read



File object
-----------


Module documentation
--------------------

.. automodule:: astropix_analysis.fileio
