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

"""Unit tests for the modeling module.
"""

import numpy as np

from astropix_analysis.modeling import Constant
from astropix_analysis.plt_ import plt


def test_constant():
    """Test the simplest module.
    """
    xdata = np.linspace(1., 10., 10)
    ydata = np.array([0.99128221, 0.94594999, 0.97208756, 1.00296311, 0.94002587,
                      0.97562304, 0.90655038, 1.03244216, 0.97426309, 0.98848519])
    sigma = 0.05
    plt.errorbar(xdata, ydata, sigma, fmt='o')
    model = Constant()
    model.fit(xdata, ydata, sigma=sigma)
    print(model)
    model.plot()
    model.stat_box()


if __name__ == '__main__':
    test_constant()
    plt.show()
