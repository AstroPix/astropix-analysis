.. _legacy:

:mod:`~astropix_analysis.legacy` --- Legacy data
================================================

This module provides support for legacy log files, where readout data are written
in text format. More specifically, the :class:`~astropix_analysis.legacy.AstroPixLogFile`
class provides a simple interface to log file that implements both the context
manager and the iterator protocol, and parses at the same time all the metadata
in the file header.

.. code-block:: python

   from astropix_analysis.legacy import AstroPixLogFile

   with AstroPixLogFile('path/to/my/file.log') as input_file:
        header = input_file.header
        print(header)
        print(header.options().get('threshold'))
        for readout_id, readout_data in input_file:
            print(readout_id, readout_data)

The ``bin/apx_log2apx.py`` scripts is a simple tool to convert legacy .log files
into new .apx binary files.


Module documentation
--------------------

.. automodule:: astropix_analysis.legacy
