.. _hist:

:mod:`~astropix_analysis.hist` --- Histograms
=============================================

`matplotlib <https://matplotlib.org/>`_ histograms are not super-great for real time
monitoring. Sure enough, matplotlib will allow you to draw a histogram, but not, e.g.,
to update the content without rebinning the entire sample each time.

This module provides a base abstract class (:class:`~astropix_analysis.hist.AbstractHistogram`)
implemening a general, n-dimensional histogram, as well as concrete classes that can be
used for online monitoring.

* :class:`~astropix_analysis.hist.Histogram1d`: generic one-dimensional histogram;
* :class:`~astropix_analysis.hist.Histogram2d`: generic two-dimensional histogram;
* :class:`~astropix_analysis.hist.Matrix2d`: specialized two-dimensional histogram to display
   matrix-like data (e.g., hitmaps in logical space).

.. warning::
   This module is still experimental and interfaces might change.


Module documentation
--------------------

.. automodule:: astropix_analysis.hist
