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

import numpy as np


def modelclass(cls: type) -> type:
    """Small decorator to support automatic generation of concrete model classes.
    """
    # pylint: disable=protected-access
    if cls._PARAMETER_NAMES is None:
        raise TypeError(f'{cls.__name__} must override _PARAMETER_NAMES')
    if cls._PARAMETER_DEFAULT_VALUES is None:
        raise TypeError(f'{cls.__name__} must override _PARAMETER_DEFAULT_VALUES')
    if len(cls._PARAMETER_NAMES) != len(cls._PARAMETER_DEFAULT_VALUES)
        raise RuntimeError(f'{cls.__name__} parameter mismatch')
    return cls


class AbstractFitModel(ABC):

    """Base class for a fittable model.
    """

    _PARAMETER_NAMES = None
    _PARAMETER_DEFAULT_VALUES = None
    _PARAMETER_DEFAULT_BOUNDS = None
    _DEFAULT_PLOTTING_RANGE = (0., 1.)
   
    def __init__(self) -> None:
        """Constructor.
        """
        self.__parameter_dict = {name: i for i, name in enumerate(self._PARAMETER_NAMES)}
        num_params = len(self.__parameter_dict)
        self.popt = numpy.array(self._PARAMETER_DEFAULT_VALUES, dtype='d')
        self.pcov = numpy.zeros((num_params, num_params), dtype='d')
        self.xmin, self.xmax = self._DEFAULT_PLOTTING_RANGE
        self.bounds = self._PARAMETER_DEFAULT_BOUNDS
        self.chisq = -1.
        self.ndof = -1

    def _parameter_index(self, parameter_name: str) -> int:
        """Convenience method returning the index within the parameter vector
        for a given parameter name.
        """
        return self._parameter_dict[parameter_name]
    
    @abstractmethod
    @staticmethod
    def evaluate(x, *parameter_values: float) -> float:
        """Evaluate the model at a given point and a given set of parameter values.

        This needs to be overloaded in any derived class for the thing to do
        something sensible.
        """
        pass

    def __call__(self, x, *parameter_values: float) -> float:
        """Return the value of the model at a given point and a given set of
        parameter values.

        Note that unless the proper number of parameters is passed to the
        function call, the model is evaluated at the best-fit parameter values.

        The function is defined with this signature because it is called
        with a set of parameter values during the fit process, while
        tipically we want to evaluate it with the current set of parameter
        values after the fact.
        """
        if len(parameter_values) == len(self.__parameter_dict):
            return self.evaluate(x, *parameter_values)
        elif len(parameter_values) == 0:
            return self.evaluate(x, *self.popt)
        else:
            raise RuntimeError(f'{self.name()} can only be called with 0 or {len(self.__parameter_dict)} parameters')

    def name(self) -> str:
        """Return the model name.
        """
        return self.__class__.__name__
    
    def init_parameters(self, xdata, ydata, sigma):
        """Assign a sensible set of values to the model parameters, based
        on a data set to be fitted.

        Note that in the base class the method is not doing anything, but it
        can be reimplemented in derived classes to help make sure the
        fit converges without too much manual intervention.
        """
        pass

    def parameter_value(self, parameter_name: str) -> float:
        """Return the parameter value by name.
        """
        return self.popt[self._parameter_index(parameter_name)]

    def parameter_error(self, parameter_name: str) -> float:
        """Return the parameter error by name.
        """
        index = self._parameter_index(parameter_name)
        return numpy.sqrt(self.pcov[index][index])

    def parameter_errors(self):
        """Return the vector of parameter errors.
        """
        return numpy.sqrt(self.pcov.diagonal())

    def parameters(self):
        """Return the complete status of the model in the form of a tuple
        of tuples (parameter_name, parameter_value, parameter_error).

        Note this can be overloaded by derived classes if more information
        needs to be added.
        """
        return tuple(zip(self._PARAMETER_NAMES, self.popt, self.parameter_errors()))

    def set_parameter(self, parameter_name: str, parameter_value: float) -> None:
        """Set a parameter value.
        """
        self.popt[self._parameter_index(parameter_name)] = parameter_value

    def set_parameters(self, *parameter_values: float) -> None:
        """Set all the parameter values.

        Note that the arguments must be passed in the right order.
        """
        self.popt = numpy.array(parameter_values, dtype='d')

    def set_plotting_range(self, xmin: float, xmax: float) -> None:
        """Set the plotting range.
        """
        self.xmin = xmin
        self.xmax = xmax

    def plot(self, *parameters, **kwargs):
        """Plot the model.

        Note that when this is called with a full set of parameters, the
        self.parameters class member is overwritten so that the right values
        can then be picked up if the stat box is plotted.
        """
        if len(parameters) == len(self):
            self.parameters = parameters
        display_stat_box = kwargs.pop('display_stat_box', False)
        x = numpy.linspace(self.xmin, self.xmax, 1000)
        y = self(x, *parameters)
        plt.plot(x, y, **kwargs)
        if display_stat_box:
            self.stat_box(**kwargs)

    def stat_box(self, position=None, plot=True, **kwargs):
        """Plot a ROOT-style stat box for the model.
        """
        if position is None:
            position = self.DEFAULT_STAT_BOX_POSITION
        box = xStatBox(position)
        box.add_entry('Fit model: %s' % self.name())
        box.add_entry('Chisquare', '%.1f / %d' % (self.chisq, self.ndof))
        for name, value, error in self.parameter_status():
            box.add_entry(name, value, error)
        if plot:
            box.plot(**kwargs)
        return box

    def __str__(self):
        """String formatting.
        """
        text = '%s model (chisq/ndof = %.2f / %d)' % (self.__class__.__name__,
                                                      self.chisq, self.ndof)
        for name, value, error in self.parameter_status():
            text += '\n%15s: %.5e +- %.5e' % (name, value, error)
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
        return numpy.full(x.shape, value)

    def init_parameters(self, xdata, ydata, sigma):
        """Overloaded init_parameters() method.
        """
        self.set_parameter('Constant', numpy.mean(ydata))


@modelclass
class Line(AbstractFitModel):

    """Straight-line model.

    .. math::
      f(x; m, q) = mx + q
    """

    _PARAMETER_NAMES = ('Intercept', 'Slope')
    _PARAMETER_DEFAULT_VALUES = (1., 1.)
    _DEFAULT_PLOTTING_RANGE = (0., 1.)

    @staticmethod
    def value(x, intercept, slope):
        """Overloaded value() method.
        """
        return intercept + slope * x


@modelclass
class Gaussian(AbstractFitModel):

    """
    """


@modelclass
class Erf(AbstractFitModel):

    """
    """