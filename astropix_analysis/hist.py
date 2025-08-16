# Copyright (C) 2025 the astropix team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Histogram facilities.
"""

from abc import ABC, abstractmethod

import numpy as np

from astropix_analysis.plt_ import plt, setup_axes, matplotlib


class InvalidShapeError(RuntimeError):

    """RuntimeError subclass to signal an invalid shape while operating with arrays.
    """

    def __init__(self, expected, actual):
        """Constructor.
        """
        super().__init__(f'Invalid array shape: {expected} expected, got {actual}')


class AbstractHistogram(ABC):

    """Base class for an n-dimensional weighted histogram.

    This interface to histograms is profoundly different for the minimal
    numpy/matplotlib approach, where histogramming methods return bare
    vectors of bin edges and counts.

    Parameters
    ----------
    bin_edges : n-dimensional tuple of arrays
        the bin edges on the different axes.

    axis_labels : n-dimensional tuple of strings
        the text labels for the different axes.
    """

    PLOT_OPTIONS = {}

    def __init__(self, bin_edges: tuple, axis_labels: list) -> None:
        """Constructor.
        """
        # Quick check on the bin_edges and label tuples---we need N + 1 axis labels
        # for an N-dimensional histogram.
        if not len(axis_labels) == len(bin_edges) + 1:
            msg = f'Length mismatch between bin edges ({len(bin_edges)}) and '\
                  f'axis_labels ({len(axis_labels)})'
            raise RuntimeError(msg)
        # The bin_edges is not supposed to change ever, so we make sure it is a tuple...
        self._bin_edges = tuple(bin_edges)
        # ...while the labels might conceivably be changed after the fact, hence a list.
        self._axis_labels = list(axis_labels)
        # Initialize all the relevant arrays. Note we cache the shape of all the
        # underlying arrays for future use; keep in mind there are N + 1 bin edges
        # for N bins.
        self._shape = tuple(len(edges) - 1 for edges in self._bin_edges)
        self._content = self._zeros()
        self._sumw2 = self._zeros()

    def _zeros(self, dtype: type = float) -> np.ndarray:
        """Return an array of zeros of the proper shape for the underlying
        histograms quantities.
        """
        return np.zeros(shape=self._shape, dtype=dtype)

    def _check_array_shape(self, data: np.array) -> None:
        """Check the shape of a given array used to update the histogram.
        """
        if data.shape == self._shape:
            raise InvalidShapeError(self._shape, data.shape)

    def reset(self) -> None:
        """Reset the histogram.
        """
        self._content = self._zeros()
        self._sumw2 = self._zeros()

    def bin_centers(self, axis: int = 0) -> np.array:
        """Return the bin centers for a specific axis.
        """
        return 0.5 * (self._bin_edges[axis][1:] + self._bin_edges[axis][:-1])

    def bin_widths(self, axis: int = 0) -> np.array:
        """Return the bin widths for a specific axis.
        """
        return np.diff(self._bin_edges[axis])

    def errors(self) -> np.array:
        """Return the errors on the bin content.
        """
        return np.sqrt(self._sumw2)

    def fill(self, *values, weights=None) -> 'AbstractHistogram':
        """Fill the histogram from unbinned data.

        Note this method is returning the histogram instance, so that the function
        call can be chained.
        """
        values = np.vstack(values).T
        if weights is None:
            content, _ = np.histogramdd(values, bins=self._bin_edges)
            sumw2 = content
        else:
            content, _ = np.histogramdd(values, bins=self._bin_edges, weights=weights)
            sumw2, _ = np.histogramdd(values, bins=self._bin_edges, weights=weights**2.)
        self._content += content
        self._sumw2 += sumw2
        return self

    def set_content(self, content: np.array, errors: np.array = None):
        """Set the bin contents programmatically from binned data.

        Note this method is returning the histogram instance, so that the function
        call can be chained.
        """
        self._check_array_shape(content)
        self._content = content
        if errors is not None:
            self.set_errors(errors)
        return self

    def set_errors(self, errors: np.array) -> None:
        """Set the proper value for the _sumw2 underlying array, given the
        errors on the bin content.
        """
        self._check_array_shape(errors)
        self._sumw2 = errors**2.

    @staticmethod
    def bisect(bin_edges: np.array, values: np.array, side: str = 'left') -> np.array:
        """Return the indices corresponding to a given array of values for a
        given bin_edges.
        """
        return np.searchsorted(bin_edges, values, side) - 1

    def find_bin(self, *coords) -> tuple:
        """Find the bin corresponding to a given set of "physical" coordinates
        on the histogram axes.

        This returns a tuple of integer indices that can be used to address
        the histogram content.
        """
        return tuple(self.bisect(bin_edges, value) for bin_edges, value in
                     zip(self._bin_edges, coords))

    def find_bin_value(self, *coords) -> float:
        """Find the histogram content corresponding to a given set of "physical"
        coordinates on the histogram axes.
        """
        return self._content[self.find_bin(*coords)]

    def normalization(self, axis: int = None):
        """return the sum of weights in the histogram.
        """
        return self._content.sum(axis)

    def empty_copy(self):
        """Create an empty copy of a histogram.
        """
        return self.__class__(*self._bin_edges, *self._axis_labels)

    def copy(self):
        """Create a full copy of a histogram.
        """
        hist = self.empty_copy()
        hist.set_content(self._content.copy(), self.errors())
        return hist

    def __add__(self, other):
        """Histogram addition.
        """
        hist = self.empty_copy()
        hist.set_content(self._content + other._content, np.sqrt(self._sumw2 + other._sumw2))
        return hist

    def __sub__(self, other):
        """Histogram subtraction.
        """
        hist = self.empty_copy()
        hist.set_content(self._content - other._content, np.sqrt(self._sumw2 + other._sumw2))
        return hist

    def __mul__(self, value):
        """Histogram multiplication by a scalar.
        """
        hist = self.empty_copy()
        hist.set_content(self._content * value, self.errors() * value)
        return hist

    def __rmul__(self, value):
        """Histogram multiplication by a scalar.
        """
        return self.__mul__(value)

    @abstractmethod
    def _draw(self, axes, **kwargs) -> None:
        """No-op method, to be overloaded by derived classes.
        """

    def draw(self, axes=None, **kwargs) -> None:
        """Plot the histogram.
        """
        if axes is None:
            axes = plt.gca()
        for key, value in self.PLOT_OPTIONS.items():
            kwargs.setdefault(key, value)
        self._draw(axes, **kwargs)
        setup_axes(axes, xlabel=self._axis_labels[0], ylabel=self._axis_labels[1])


class Histogram1d(AbstractHistogram):

    """A one-dimensional histogram.
    """

    PLOT_OPTIONS = dict(lw=1.25, alpha=0.4, histtype='stepfilled')

    def __init__(self, xbinning: np.array, xlabel: str = '', ylabel: str = 'Entries/bin') -> None:
        """Constructor.
        """
        super().__init__((xbinning, ), [xlabel, ylabel])

    def _draw(self, axes, **kwargs) -> None:
        """Overloaded method.
        """
        axes.hist(self.bin_centers(0), self._bin_edges[0], weights=self._content, **kwargs)


class Histogram2d(AbstractHistogram):

    """A two-dimensional histogram.
    """

    PLOT_OPTIONS = dict(cmap=plt.get_cmap('hot'))
    # pylint: disable=invalid-name

    def __init__(self, xbinning, ybinning, xlabel='', ylabel='', zlabel='Entries/bin'):
        """Constructor.
        """
        # pylint: disable=too-many-arguments
        super().__init__((xbinning, ybinning), [xlabel, ylabel, zlabel])
        self.color_bar = None

    def _update_color_bar(self, axes, image) -> None:
        """Update the color bar after a histogram re-draw.

        This is a little bit tricky, as by default the colorbar gets her own
        axes, and a call to plt.gca().cla() will not delete the color bar.
        This is a small utility function to draw the color bar the first time
        around, and then re-bind to the latest version of the data each time
        the histogram is re-drawn.
        """
        if self.color_bar is None:
            self.color_bar = plt.colorbar(image, ax=axes)
            if self._axis_labels[2] is not None:
                self.color_bar.set_label(self._axis_labels[2])
        else:
            self.color_bar.update_normal(image)

    def _draw(self, axes, logz=False, **kwargs):
        """Overloaded method.
        """
        # pylint: disable=arguments-differ
        x, y = (v.flatten() for v in np.meshgrid(self.bin_centers(0), self.bin_centers(1)))
        bins = self._bin_edges
        w = self._content.T.flatten()
        if logz:
            # Hack for a deprecated functionality in matplotlib 3.3.0
            # Parameters norm and vmin/vmax should not be used simultaneously
            # If logz is requested, we intercent the bounds when created the norm
            # and refrain from passing vmin/vmax downstream.
            vmin = kwargs.pop('vmin', None)
            vmax = kwargs.pop('vmax', None)
            kwargs.setdefault('norm', matplotlib.colors.LogNorm(vmin, vmax))
        _, _, _, image = axes.hist2d(x, y, bins, weights=w, **kwargs)
        self._update_color_bar(axes, image)

    def slice(self, bin_index: int, axis: int = 0):
        """Return a slice of the two-dimensional histogram along the given axis.
        """
        hist = Histogram1d(self._bin_edges[axis], self._axis_labels[axis])
        hist.set_content(self._content[:, bin_index])
        return hist

    def slices(self, axis: int = 0):
        """Return all the slices along a given axis.
        """
        return tuple(self.slice(bin_index, axis) for bin_index in range(self._shape[axis]))

    def hslice(self, bin_index: int):
        """Return the horizontal slice for a given bin.
        """
        return self.slice(bin_index, 0)

    def hslices(self):
        """Return a list of all the horizontal slices.
        """
        return self.slices(0)

    def hbisect(self, y: float):
        """Return the horizontal slice corresponding to a given y value.
        """
        return self.hslice(self.bisect(self._bin_edges[1], y))

    def vslice(self, bin_index):
        """Return the vertical slice for a given bin.
        """
        return self.slice(bin_index, 1)

    def vslices(self):
        """Return a list of all the vertical slices.
        """
        return self.slices(1)

    def vbisect(self, x):
        """Return the vertical slice corresponding to a given y value.
        """
        return self.vslice(self.bisect(self._bin_edges[0], x))


class Matrix2d(Histogram2d):

    """Specialized 2-dimensional histogram to display matrix-like data
    (e.g., hitmap in logical space).
    """

    def __init__(self, num_cols: int, num_rows: int, xlabel='Column', ylabel='Row',
                 zlabel='Entries/bin') -> None:
        """Constructor.
        """
        xedges = np.arange(-0.5, num_cols)
        yedges = np.arange(-0.5, num_rows)
        super().__init__(xedges, yedges, xlabel, ylabel, zlabel)

    def _draw(self, axes, logz=False, **kwargs):
        """Overloaded method.

        Note we have to transpose the underlying content due to the very
        nature of item addressing in numpy arrays.

        .. warning::
           This points to the fact that some of the Histogram2d interfaces might
           be broken, and we might better off with a content() method that
           one can overload.
        """
        image = axes.matshow(self._content.T, **kwargs)
        axes.set_xticks(self._bin_edges[0], minor=True)
        axes.set_yticks(self._bin_edges[1], minor=True)
        axes.grid(which='minor', linewidth=1)
        self._update_color_bar(axes, image)
