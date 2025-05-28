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


Data structures
---------------

There are two main basic data structures we deal with in this module: that of a
`hit` and that of a `readout`---a hit is a single hit from an astropix chip, while
a readout is a full binary chunk of data we get from the readout board, and that
in generally contains a variable number of hits. Accordingly, we provide two
abstract base classes:

* :class:`~astropix_analysis.fmt.AbstractAstroPixHit`
* :class:`~astropix_analysis.fmt.AbstractAstroPixReadout`

from which actual concrete classes can be derived for the different chip and DAQ
versions.


Hit structures
~~~~~~~~~~~~~~



Readout structures
~~~~~~~~~~~~~~~~~~




Module documentation
--------------------

.. automodule:: astropix_analysis.fmt
