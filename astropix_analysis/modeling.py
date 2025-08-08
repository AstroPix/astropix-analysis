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

"""Modeling facilities.
"""

from abc import ABC, abstractmethod
import typing

from loguru import logger
import numpy as np
from scipy.optimize import curve_fit
import uncertainties

from astropix_analysis.plt_ import plt, PlotCard


def modelclass(cls: type) -> type:
    """Small decorator to support automatic generation of concrete model classes.
    """
    # pylint: disable=protected-access
    if cls._PARAMETER_NAMES is None:
        raise TypeError(f'{cls.__name__} must override _PARAMETER_NAMES')
    if cls._PARAMETER_DEFAULT_VALUES is None:
        raise TypeError(f'{cls.__name__} must override _PARAMETER_DEFAULT_VALUES')
    if len(cls._PARAMETER_NAMES) != len(cls._PARAMETER_DEFAULT_VALUES):
        raise RuntimeError(f'{cls.__name__} parameter mismatch')
    return cls


class AbstractFitModel(ABC):

    """Base class for a fittable model.
    """

    _PARAMETER_NAMES = None
    _PARAMETER_DEFAULT_VALUES = None
    _PARAMETER_DEFAULT_BOUNDS = (-np.inf, np.inf)
    _DEFAULT_PLOTTING_RANGE = (0., 1.)

    def __init__(self) -> None:
        """Constructor.
        """
        self._parameter_dict = {name: i for i, name in enumerate(self._PARAMETER_NAMES)}
        self.popt = np.array(self._PARAMETER_DEFAULT_VALUES, dtype='d')
        self.pcov = np.zeros((len(self), len(self)), dtype='d')
        self.xmin, self.xmax = self._DEFAULT_PLOTTING_RANGE
        self.bounds = self._PARAMETER_DEFAULT_BOUNDS
        self.chisq = -1.
        self.ndof = -1

    def _parameter_index(self, parameter_name: str) -> int:
        """Convenience method returning the index within the parameter vector
        for a given parameter name.

        Arguments
        ---------
        parameter_name : str
            The name of the parameter.
        """
        return self._parameter_dict[parameter_name]

    def __len__(self) -> int:
        """Return the number of parameters in the model.
        """
        return len(self._parameter_dict)

    def name(self) -> str:
        """Return the name of the underlying class.
        """
        return self.__class__.__name__

    def parameter_value(self, parameter_name: str) -> float:
        """Return the parameter value by name.

        Arguments
        ---------
        parameter_name : str
            The name of the parameter.
        """
        return self.popt[self._parameter_index(parameter_name)]

    def parameter_error(self, parameter_name: str) -> float:
        """Return the parameter error by name.

        Arguments
        ---------
        parameter_name : str
            The name of the parameter.
        """
        return self.parameter_errors()[self._parameter_index(parameter_name)]

    def parameter_errors(self):
        """Return the vector of parameter errors.
        """
        return np.sqrt(self.pcov.diagonal())

    def __iter__(self):
        """Allow iteration over the full parameter information.
        """
        return iter(zip(self._PARAMETER_NAMES, self.popt, self.parameter_errors()))

    def set_parameter(self, parameter_name: str, parameter_value: float) -> None:
        """Set a parameter value.
        """
        self.popt[self._parameter_index(parameter_name)] = parameter_value

    @staticmethod
    @abstractmethod
    def evaluate(x, *parameter_values: float) -> float:
        """Evaluate the model at a given point and a given set of parameter values.
        """

    def __call__(self, x, *parameter_values: float) -> float:
        """Return the value of the model at a given point and a given set of
        parameter values.

        Note that unless the proper number of parameters is passed to the
        function call, the model is evaluated at the best-fit parameter values.

        The function is defined with this signature because it is called
        with a set of parameter values during the fit process, while
        typically we want to evaluate it with the current set of parameter
        values after the fact.
        """
        if len(parameter_values) == len(self):
            return self.evaluate(x, *parameter_values)
        if len(parameter_values) == 0:
            return self.evaluate(x, *self.popt)
        raise RuntimeError(f'{self.name()} can only be called with 0 or {len(self)} parameters')

    def init_parameters(self, xdata, ydata, sigma):
        """Assign a sensible set of values to the model parameters, based
        on a data set to be fitted.

        Note that in the base class the method is not doing anything, but it
        can be reimplemented in derived classes to help make sure the
        fit converges without too much manual intervention.
        """

    def fit(self, xdata, ydata, p0=None, sigma=None, xmin=-np.inf, xmax=np.inf,
            absolute_sigma=True, check_finite=True, method=None, **kwargs):
        """Lightweight wrapper over the ``scipy.optimize.curve_fit()`` function
        to take advantage of the modeling facilities. More specifically, in addition
        to performing the actual fit, we update all the model parameters so that,
        after the fact, we do have a complete picture of the fit outcome.

        Arguments
        ---------

        xdata : array_like
            The independent variable where the data is measured.

        ydata : array_like
            The dependent data --- nominally f(xdata, ...)

        p0 : None, scalar, or sequence, optional
            Initial guess for the parameters. If None, then the initial
            values will all be 1.

        sigma : None or array_like, optional
            Uncertainties in `ydata`. If None, all the uncertainties are set to
            1 and the fit becomes effectively unweighted.

        xmin : float
            The minimum value for the input x-values.

        xmax : float
            The maximum value for the input x-values.

        absolute_sigma : bool, optional
            If True, `sigma` is used in an absolute sense and the estimated
            parameter covariance `pcov` reflects these absolute values.
            If False, only the relative magnitudes of the `sigma` values matter.
            The returned parameter covariance matrix `pcov` is based on scaling
            `sigma` by a constant factor. This constant is set by demanding that the
            reduced `chisq` for the optimal parameters `popt` when using the
            *scaled* `sigma` equals unity.

        method : {'lm', 'trf', 'dogbox'}, optional
            Method to use for optimization.  See `least_squares` for more details.
            Default is 'lm' for unconstrained problems and 'trf' if `bounds` are
            provided. The method 'lm' won't work when the number of observations
            is less than the number of variables, use 'trf' or 'dogbox' in this
            case.

        kwargs
            Keyword arguments passed to `leastsq` for ``method='lm'`` or
            `least_squares` otherwise.
        """
        # Select data based on the x-axis range passed as an argument.
        _mask = np.logical_and(xdata >= xmin, xdata <= xmax)
        xdata = xdata[_mask]
        ydata = ydata[_mask]
        if len(xdata) <= len(self):
            raise RuntimeError('Not enough data to fit ({len(xdata)} points)')
        if isinstance(sigma, np.ndarray):
            sigma = sigma[_mask]
        # If we are not passing default starting points for the model parameters,
        # try and do something sensible.
        if p0 is None:
            self.init_parameters(xdata, ydata, sigma)
            p0 = self.popt
            logger.debug(f'{self.name()} parameters initialized to {p0}.')
        # If sigma is None, assume all the errors are 1. (If we don't do this,
        # the code will crash when calculating the chisquare.
        if sigma is None:
            sigma = np.full((len(ydata), ), 1.)
        popt, pcov = curve_fit(self, xdata, ydata, p0, sigma, absolute_sigma,
                               check_finite, self.bounds, method, **kwargs)
        # Update the model parameters.
        self.set_plotting_range(xdata.min(), xdata.max())
        self.popt = popt
        self.pcov = pcov
        self.chisq = (((ydata - self(xdata))/sigma)**2).sum()
        self.ndof = len(ydata) - len(self)

    def set_plotting_range(self, xmin: float, xmax: float) -> None:
        """Set the plotting range.
        """
        self.xmin = xmin
        self.xmax = xmax

    def plot(self, **kwargs):
        """Plot the model.
        """
        x = np.linspace(self.xmin, self.xmax, 1000)
        y = self(x, *self.popt)
        plt.plot(x, y, **kwargs)

    def stat_box(self, position: typing.Tuple[float, float] = (0.05, 0.95), **kwargs):
        """Plot a ROOT-style stat box for the model.
        """
        card = PlotCard()
        card.add_line('Fit model', self.name())
        card.add_line('Chisquare/dof', f'{self.chisq:.2f} / {self.ndof}')
        for name, value, error in self:
            card.add_line(name, uncertainties.ufloat(value, error))
        card.draw(position, **kwargs)
        return card

    def __str__(self):
        """String formatting.
        """
        text = f'{self.name()} (Chisquare/dof = {self.chisq:.2f} / {self.ndof})'
        for name, value, error in self:
            value = uncertainties.ufloat(value, error)
            text += f'\n{name:15s}: {value}'
        return text


@modelclass
class Constant(AbstractFitModel):

    """Constant model.

    .. math::
      f(x; C) = C
    """

    _PARAMETER_NAMES = ('Value',)
    _PARAMETER_DEFAULT_VALUES = (1.,)
    _DEFAULT_PLOTTING_RANGE = (0., 1.)

    @staticmethod
    def evaluate(x: np.ndarray, value: float) -> np.ndarray:
        """Overloaded value() method.
        """
        # pylint: disable=arguments-differ
        return np.full(x.shape, value)

    def init_parameters(self, xdata, ydata, sigma):
        """Overloaded init_parameters() method.
        """
        self.set_parameter('Value', np.mean(ydata))


@modelclass
class Line(AbstractFitModel):

    """Straight-line model.

    .. math::
      f(x; m, q) = mx + q
    """

    _PARAMETER_NAMES = ('Slope', 'Intercept')
    _PARAMETER_DEFAULT_VALUES = (1., 0.)
    _DEFAULT_PLOTTING_RANGE = (0., 1.)

    @staticmethod
    def value(x, slope, intercept):
        """Overloaded value() method.
        """
        return slope * x + intercept


# @modelclass
# class Gaussian(AbstractFitModel):

#     """
#     """


# @modelclass
# class Erf(AbstractFitModel):

#     """
#     """
