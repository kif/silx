# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2017 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""This module provides the :class:`Curve` item of the :class:`Plot`.
"""

__authors__ = ["T. Vincent"]
__license__ = "MIT"
__date__ = "06/03/2017"


import logging

import numpy

from .. import Colors
from .core import (Points, LabelsMixIn, SymbolMixIn,
                   ColorMixIn, YAxisMixIn, FillMixIn)
from ....utils.decorators import deprecated


_logger = logging.getLogger(__name__)


def _computeEdges(x, histogramType):
    """Compute the edges from a set of xs and a rule to generate the edges

    :param x: the x value of the curve to transform into an histogram
    :param histogramType: the type of histogram we wan't to generate.
         This define the way to center the histogram values compared to the
         curve value. Possible values can be::

         - 'left'
         - 'right'
         - 'center'

    :return: the edges for the given x and the histogramType
    """
    # for now we consider that the spaces between xs are constant
    edges = x.copy()
    if histogramType is 'left':
        width = 1
        if len(x) > 1:
            width = x[1] - x[0]
        edges = numpy.append(x[0] - width, edges)
    if histogramType is 'center':
        edges = _computeEdges(edges, 'right')
        widths = (edges[1:] - edges[0:-1]) / 2.0
        widths = numpy.append(widths, widths[-1])
        edges = edges - widths
    if histogramType is 'right':
        width = 1
        if len(x) > 1:
            width = x[-1] - x[-2]
        edges = numpy.append(edges, x[-1] + width)

    return edges


def _getHistogramValue(x, y, histogramType):
    """Returns the x and y value of a curve corresponding to the histogram

    :param x: the x value of the curve to transform in an histogram
    :param y: the y value of the curve to transform in an histogram
    :param histogramType: the type of histogram we wan't to generate.
         This define the way to center the histogram values compared to the
         curve value. Possible values can be::

         - 'left'
         - 'right'
         - 'center'

    :return: a tuple(x, y) which are the value of the histogram to be
         displayed as a curve
    """
    assert histogramType in ('left', 'right', 'center')
    if len(x) == len(y) + 1:
        edges = x
    else:
        edges = _computeEdges(x, histogramType)
    assert len(edges) > 1

    resx = numpy.empty((len(edges) - 1) * 2, dtype=edges.dtype)
    resy = numpy.empty((len(edges) - 1) * 2, dtype=edges.dtype)
    # duplicate x and y values with a small shift to get the stairs effect
    resx[:-1:2] = edges[:-1]
    resx[1::2] = edges[1:]
    resy[:-1:2] = y
    resy[1::2] = y

    assert len(resx) == len(resy)
    return resx, resy


class Curve(Points, ColorMixIn, YAxisMixIn, FillMixIn, LabelsMixIn):
    """Description of a curve"""

    _DEFAULT_Z_LAYER = 1
    """Default overlay layer for curves"""

    _DEFAULT_SELECTABLE = True
    """Default selectable state for curves"""

    _DEFAULT_LINEWIDTH = 1.
    """Default line width of the curve"""

    _DEFAULT_LINESTYLE = '-'
    """Default line style of the curve"""

    _DEFAULT_HIGHLIGHT_COLOR = (0, 0, 0, 255)
    """Default highlight color of the item"""

    def __init__(self):
        Points.__init__(self)
        ColorMixIn.__init__(self)
        YAxisMixIn.__init__(self)
        FillMixIn.__init__(self)
        LabelsMixIn.__init__(self)

        self._linewidth = self._DEFAULT_LINEWIDTH
        self._linestyle = self._DEFAULT_LINESTYLE
        self._histogram = None

        self._highlightColor = self._DEFAULT_HIGHLIGHT_COLOR
        self._highlighted = False

    def _addBackendRenderer(self, backend):
        """Update backend renderer"""
        # Filter-out values <= 0
        xFiltered, yFiltered, xerror, yerror = self.getData(
            copy=False, displayed=True)

        if len(xFiltered) == 0:
            return None  # No data to display, do not add renderer to backend

        # if we want to plot an histogram
        if self.getHistogramType() in ('left', 'right', 'center'):
            assert len(xFiltered) in (len(yFiltered), len(yFiltered)+1)
            # FIXME: setData does not allow len(yFiltered)+1 for now

            # TODO move this in Histogram class and avoid histo if
            xFiltered, yFiltered = _getHistogramValue(
                xFiltered,  yFiltered, histogramType=self.getHistogramType())
            if (self.getXErrorData(copy=False) is not None or
                    self.getYErrorData(copy=False) is not None):
                _logger.warning("xerror and yerror won't be displayed"
                                " for histogram display")
            xerror, yerror = None, None

        return backend.addCurve(xFiltered, yFiltered, self.getLegend(),
                                color=self.getCurrentColor(),
                                symbol=self.getSymbol(),
                                linestyle=self.getLineStyle(),
                                linewidth=self.getLineWidth(),
                                yaxis=self.getYAxis(),
                                xerror=xerror,
                                yerror=yerror,
                                z=self.getZValue(),
                                selectable=self.isSelectable(),
                                fill=self.isFill(),
                                alpha=self.getAlpha(),
                                symbolsize=self.getSymbolSize())

    @deprecated
    def __getitem__(self, item):
        """Compatibility with PyMca and silx <= 0.4.0"""
        if isinstance(item, slice):
            return [self[index] for index in range(*item.indices(5))]
        elif item == 0:
            return self.getXData(copy=False)
        elif item == 1:
            return self.getYData(copy=False)
        elif item == 2:
            return self.getLegend()
        elif item == 3:
            info = self.getInfo(copy=False)
            return {} if info is None else info
        elif item == 4:
            params = {
                'info': self.getInfo(),
                'color': self.getColor(),
                'symbol': self.getSymbol(),
                'linewidth': self.getLineWidth(),
                'linestyle': self.getLineStyle(),
                'xlabel': self.getXLabel(),
                'ylabel': self.getYLabel(),
                'yaxis': self.getYAxis(),
                'xerror': self.getXErrorData(copy=False),
                'yerror': self.getYErrorData(copy=False),
                'z': self.getZValue(),
                'selectable': self.isSelectable(),
                'fill': self.isFill()
            }
            return params
        else:
            raise IndexError("Index out of range: %s", str(item))

    def setVisible(self, visible):
        """Set visibility of item.

        :param bool visible: True to display it, False otherwise
        """
        visibleChanged = self.isVisible() != bool(visible)
        super(Curve, self).setVisible(visible)

        # TODO hackish data range implementation
        if visibleChanged:
            plot = self.getPlot()
            if plot is not None:
                plot._invalidateDataRange()

    def isHighlighted(self):
        """Returns True if curve is highlighted.

        :rtype: bool
        """
        return self._highlighted

    def setHighlighted(self, highlighted):
        """Set the highlight state of the curve

        :param bool highlighted:
        """
        highlighted = bool(highlighted)
        if highlighted != self._highlighted:
            self._highlighted = highlighted
            # TODO inefficient: better to use backend's setCurveColor
            self._updated()

    def getHighlightedColor(self):
        """Returns the RGBA highlight color of the item

        :rtype: 4-tuple of int in [0, 255]
        """
        return self._highlightColor

    def setHighlightedColor(self, color):
        """Set the color to use when highlighted

        :param color: color(s) to be used for highlight
        :type color: str ("#RRGGBB") or (npoints, 4) unsigned byte array or
                     one of the predefined color names defined in Colors.py
        """
        color = Colors.rgba(color)
        if color != self._highlightColor:
            self._highlightColor = color
            self._updated()

    def getCurrentColor(self):
        """Returns the current color of the curve.

        This color is either the color of the curve or the highlighted color,
        depending on the highlight state.

        :rtype: 4-tuple of int in [0, 255]
        """
        if self.isHighlighted():
            return self.getHighlightedColor()
        else:
            return self.getColor()

    def getLineWidth(self):
        """Return the curve line width in pixels (int)"""
        return self._linewidth

    def setLineWidth(self, width):
        """Set the width in pixel of the curve line

        See :meth:`getLineWidth`.

        :param float width: Width in pixels
        """
        width = float(width)
        if width != self._linewidth:
            self._linewidth = width
            self._updated()

    def getLineStyle(self):
        """Return the type of the line

        Type of line::

            - ' '  no line
            - '-'  solid line
            - '--' dashed line
            - '-.' dash-dot line
            - ':'  dotted line

        :rtype: str
        """
        return self._linestyle

    def setLineStyle(self, style):
        """Set the style of the curve line.

        See :meth:`getLineStyle`.

        :param str style: Line style
        """
        style = str(style)
        assert style in ('', ' ', '-', '--', '-.', ':', None)
        if style is None:
            style = self._DEFAULT_LINESTYLE
        if style != self._linestyle:
            self._linestyle = style
            self._updated()

    # TODO make a separate class for histograms
    def getHistogramType(self):
        """Histogram curve rendering style.

        Histogram type::

            - None (default)
            - 'left'
            - 'right'
            - 'center'

        :rtype: str or None
        """
        return self._histogram

    def setHistogramType(self, histogram):
        assert histogram in ('left', 'right', 'center', None)
        if histogram != self._histogram:
            self._histogram = histogram
            self._updated()
            # TODO hackish data range implementation
            if self.isVisible():
                plot = self.getPlot()
                if plot is not None:
                    plot._invalidateDataRange()
