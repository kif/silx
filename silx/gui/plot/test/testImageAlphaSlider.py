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
"""Tests for ImageAlphaSlider"""


__authors__ = ["P. Knobel"]
__license__ = "MIT"
__date__ = "28/03/2017"

import numpy
import unittest

from silx.gui import qt
from silx.gui.test.utils import TestCaseQt
from silx.gui.plot import PlotWidget
from silx.gui.plot import ImageAlphaSlider

# Makes sure a QApplication exists
_qapp = qt.QApplication.instance() or qt.QApplication([])


class TestActiveImageAlphaSlider(TestCaseQt):
    def setUp(self):
        super(TestActiveImageAlphaSlider, self).setUp()
        self.plot = PlotWidget()
        self.aslider = ImageAlphaSlider.ActiveImageAlphaSlider(plot=self.plot)
        self.aslider.setOrientation(qt.Qt.Horizontal)

        toolbar = qt.QToolBar("plot", self.plot)
        toolbar.addWidget(self.aslider)
        self.plot.addToolBar(toolbar)

        self.plot.show()
        self.qWaitForWindowExposed(self.plot)

        self.mouseMove(self.plot)  # Move to center
        self.qapp.processEvents()

    def tearDown(self):
        self.qapp.processEvents()
        self.plot.setAttribute(qt.Qt.WA_DeleteOnClose)
        self.plot.close()
        del self.plot
        del self.aslider

        super(TestActiveImageAlphaSlider, self).tearDown()

    def testWidgetEnabled(self):
        # no active image initially, slider must be deactivate
        self.assertFalse(self.aslider.isEnabled())

        self.plot.addImage(numpy.array([[0, 1, 2], [3, 4, 5]]))
        # now we have an active image
        self.assertTrue(self.aslider.isEnabled())

        self.plot.setActiveImage(None)
        self.assertFalse(self.aslider.isEnabled())

    def testGetImage(self):
        self.plot.addImage(numpy.array([[0, 1, 2], [3, 4, 5]]))
        self.assertEqual(self.plot.getActiveImage(),
                         self.aslider.getImage())

        self.plot.addImage(numpy.array([[0, 1, 3], [2, 4, 6]]), legend="2")
        self.plot.setActiveImage("2")
        self.assertEqual(self.plot.getImage("2"),
                         self.aslider.getImage())

    def testGetAlpha(self):
        self.plot.addImage(numpy.array([[0, 1, 2], [3, 4, 5]]), legend="1")
        self.aslider.setValue(137)
        self.assertAlmostEqual(self.aslider.getAlpha(),
                               137. / 255)


class TestNamedImageAlphaSlider(TestCaseQt):
    def setUp(self):
        super(TestNamedImageAlphaSlider, self).setUp()
        self.plot = PlotWidget()
        self.aslider = ImageAlphaSlider.NamedImageAlphaSlider(plot=self.plot)
        self.aslider.setOrientation(qt.Qt.Horizontal)

        toolbar = qt.QToolBar("plot", self.plot)
        toolbar.addWidget(self.aslider)
        self.plot.addToolBar(toolbar)

        self.plot.show()
        self.qWaitForWindowExposed(self.plot)

        self.mouseMove(self.plot)  # Move to center
        self.qapp.processEvents()

    def tearDown(self):
        self.qapp.processEvents()
        self.plot.setAttribute(qt.Qt.WA_DeleteOnClose)
        self.plot.close()
        del self.plot
        del self.aslider

        super(TestNamedImageAlphaSlider, self).tearDown()

    def testWidgetEnabled(self):
        # no image set initially, slider must be deactivate
        self.assertFalse(self.aslider.isEnabled())

        self.plot.addImage(numpy.array([[0, 1, 2], [3, 4, 5]]), legend="1")
        self.aslider.setLegend("1")
        # now we have an image set
        self.assertTrue(self.aslider.isEnabled())

    def testGetImage(self):
        self.plot.addImage(numpy.array([[0, 1, 2], [3, 4, 5]]), legend="1")
        self.plot.addImage(numpy.array([[0, 1, 3], [2, 4, 6]]), legend="2")
        self.aslider.setLegend("1")
        self.assertEqual(self.plot.getImage("1"),
                         self.aslider.getImage())

        self.aslider.setLegend("2")
        self.assertEqual(self.plot.getImage("2"),
                         self.aslider.getImage())

    def testGetAlpha(self):
        self.plot.addImage(numpy.array([[0, 1, 2], [3, 4, 5]]), legend="1")
        self.aslider.setLegend("1")
        self.aslider.setValue(128)
        self.assertAlmostEqual(self.aslider.getAlpha(),
                               128. / 255)


def suite():
    test_suite = unittest.TestSuite()
    # test_suite.addTest(positionInfoTestSuite)
    for testClass in (TestActiveImageAlphaSlider, TestNamedImageAlphaSlider):
        test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(
            testClass))
    return test_suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')