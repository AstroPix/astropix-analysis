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

"""Unit tests for the hist.py module.
"""

import numpy as np

from astropix_analysis.hist import RunningStats, Histogram1d, Histogram2d, Matrix2d
from astropix_analysis.plt_ import plt


def test_running_stats():
    """Test the RunningStats class.
    """
    # Create a couple of subsamples, and merge them.
    sample1 = np.random.normal(size=1000)
    sample2 = np.random.normal(size=1000)
    sample = np.hstack([sample1, sample2])

    # Update one value at a time.
    stats = RunningStats()
    for val in sample:
        stats.update(val)
    print(stats)
    assert stats.n == sample.size
    assert np.allclose(stats.mean, sample.mean())
    assert np.allclose(stats.stdev, sample.std(ddof=1))

    # Update passing the full arrays.
    stats = RunningStats()
    stats.update(sample1)
    print(stats)
    assert stats.n == sample1.size
    assert np.allclose(stats.mean, sample1.mean())
    assert np.allclose(stats.stdev, sample1.std(ddof=1))
    stats.update(sample2)
    print(stats)
    assert stats.n == sample.size
    assert np.allclose(stats.mean, sample.mean())
    assert np.allclose(stats.stdev, sample.std(ddof=1))


def test_hist1d(num_bins: int = 100, sample_size: int = 100000):
    """Test for one-dimensional histograms.
    """
    edges = np.linspace(-5., 5., num_bins)
    x = np.random.normal(size=sample_size)
    hist = Histogram1d(edges, 'rv')
    hist.fill(x)
    plt.figure('One-dimensional gaussian histogram')
    hist.draw()


def test_hist2d(num_bins: int = 100, sample_size: int = 100000):
    """Test for two-dimensional histograms
    """
    edges = np.linspace(-5., 5., num_bins)
    x = np.random.normal(size=sample_size)
    y = np.random.normal(size=sample_size)
    hist = Histogram2d(edges, edges, 'x', 'y')
    hist.fill(x, y)
    plt.figure('Two-dimensional gaussian histogram')
    hist.draw()


def test_matrix2d():
    """Test the Matrix2d histogram type.
    """
    hist = Matrix2d(16, 8, 'Column', 'Row')
    plt.figure('Two-dimensional matrix')
    hist.fill(6, 2)
    hist.fill(6, 2)
    hist.fill(15, 7)
    hist.draw()


if __name__ == '__main__':
    test_hist1d()
    test_hist2d()
    test_matrix2d()
    plt.show()
