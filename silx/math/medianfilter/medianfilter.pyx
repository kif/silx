# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2015-2017 European Synchrotron Radiation Facility
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
"""This module provides median filter function for 1D and 2D arrays.
"""

__authors__ = ["H. PAyno"]
__license__ = "MIT"
__date__ = "13/02/2017"


from cython.parallel import parallel, prange
cimport cython
cimport median_filter
import numpy
cimport numpy as cnumpy
cdef Py_ssize_t size = 10
from libcpp cimport bool

ctypedef unsigned long uint64
ctypedef unsigned int uint32
ctypedef unsigned short uint16

def medfilt2d(input, kernel_size=3, bool conditional=False, int nthread=4):
    """Function computing the median filter of the given input.
    Behavior at boundaries: the algorithm is reducing the size of the
    window/kernel for pixels at boundaries (there is no mirroring).

    :param numpy.ndarray input: the array for which we want to apply 
        the median filter
    :param kernel_size: the dimension of the kernel.
    :type kernel_size: For 1D should be an int for 2D should be a tuple or 
        a list of (kernel_height, kernel_width)
    :param bool conditional: True if we want to apply a conditional median
        filtering.
    :param int nthread: the number of threads we want to launch to solve the
        median filtering.

    :returns: the array with the median value for each pixel.
    """
    reshaped = False
    if len(input.shape) < 2 :
      input = input.reshape(input.shape[0], 1)
      reshaped = True

    # simple median filter apply into a 2D buffer
    output_buffer = numpy.zeros(input.shape, dtype=input.dtype)
    check(input, output_buffer)

    image_dim = numpy.array(input.shape, dtype=numpy.int32)

    if type(kernel_size) in (tuple, list):
      if(len(kernel_size) == 1):
          ker_dim = numpy.array(1, [kernel_size[0]], dtype=numpy.int32)
      else:
          ker_dim = numpy.array(kernel_size, dtype=numpy.int32)
    else:
      ker_dim = numpy.array([kernel_size, kernel_size], dtype=numpy.int32)

    # limit the number of threads according to the input data
    maxThread = min(nthread, input.shape[0])
    ranges = numpy.array(
        [ int(input.shape[0] * x / maxThread) for x in range(maxThread+1) ],
        dtype=numpy.int32)

    if input.dtype == numpy.float64:
        medfilterfc = _median_filter_float64
    elif input.dtype == numpy.float32:
        medfilterfc = _median_filter_float32
    elif input.dtype == numpy.int64:
        medfilterfc = _median_filter_int64
    elif input.dtype == numpy.uint64:
        medfilterfc = _median_filter_uint64
    elif input.dtype == numpy.int32:
        medfilterfc = _median_filter_int32
    elif input.dtype == numpy.uint32:
        medfilterfc = _median_filter_uint32
    elif input.dtype == numpy.int16:
        medfilterfc = _median_filter_int16
    elif input.dtype == numpy.uint16:
        medfilterfc = _median_filter_uint16
    else:
        raise ValueError("%s type is not managed by the median filter"%input.dtype)

    medfilterfc(input_buffer=input,
                output_buffer=output_buffer, 
                kernel_size=ker_dim,
                ranges=ranges,
                image_dim=image_dim,
                conditional=conditional)

    if reshaped : 
      input = input.reshape(input.shape[0])
      output_buffer = output_buffer.reshape(input.shape[0])

    return output_buffer

def check(input_buffer, output_buffer):
    """Simple chack on the two buffers to make sure we can apply the median filter
    """
    if (input_buffer.flags['C_CONTIGUOUS'] is False):
        raise ValueError('<input_buffer> must be a C_CONTIGUOUS numpy array.')

    if (output_buffer.flags['C_CONTIGUOUS'] is False):
        raise ValueError('<output_buffer> must be a C_CONTIGUOUS numpy array.')

    if not (len(input_buffer.shape) <= 2):
        raise ValueError('<input_buffer> dimension must mo higher than 2.')    

    if not (len(output_buffer.shape) <= 2):
        raise ValueError('<output_buffer> dimension must mo higher than 2.')    

    if not(input_buffer.dtype == output_buffer.dtype):
        raise ValueError('input buffer and output_buffer must be of the same type')

    if not (input_buffer.shape == output_buffer.shape):
        raise ValueError('input buffer and output_buffer must be of the same dimension and same dimension')

######### implementations of the include/median_filter.hpp function ############
@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_float32(
      cnumpy.ndarray[cnumpy.float32_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.float32_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[float](<float*> input_buffer.data, 
                                               <float*> output_buffer.data, 
                                               <int*>kernel_size.data,
                                               <int*>image_dim.data,
                                               ranges[x],
                                               ranges[x+1]-1,
                                               0,
                                               image_dim[1]-1,
                                               conditional);

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_float64(
      cnumpy.ndarray[cnumpy.float64_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.float64_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[double](<double*> input_buffer.data, 
                                                <double*> output_buffer.data, 
                                                <int*>kernel_size.data,
                                                <int*>image_dim.data,
                                                ranges[x],
                                                ranges[x+1]-1,
                                                0,
                                                image_dim[1]-1,
                                                conditional);

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_int64(
      cnumpy.ndarray[cnumpy.int64_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.int64_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[long](<long*> input_buffer.data, 
                                                <long*> output_buffer.data, 
                                                <int*>kernel_size.data,
                                                <int*>image_dim.data,
                                                ranges[x],
                                                ranges[x+1]-1,
                                                0,
                                                image_dim[1]-1,
                                                conditional);
@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_uint64(
      cnumpy.ndarray[cnumpy.uint64_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.uint64_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[uint64](<uint64*> input_buffer.data, 
                                                <uint64*> output_buffer.data, 
                                                <int*>kernel_size.data,
                                                <int*>image_dim.data,
                                                ranges[x],
                                                ranges[x+1]-1,
                                                0,
                                                image_dim[1]-1,
                                                conditional);

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_int32(
      cnumpy.ndarray[cnumpy.int32_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.int32_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[int](<int*> input_buffer.data, 
                                             <int*> output_buffer.data, 
                                             <int*>kernel_size.data,
                                             <int*>image_dim.data,
                                             ranges[x],
                                             ranges[x+1]-1,
                                             0,
                                             image_dim[1]-1,
                                             conditional);

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_uint32(
      cnumpy.ndarray[cnumpy.uint32_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.uint32_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[uint32](<uint32*> input_buffer.data, 
                                                <uint32*> output_buffer.data, 
                                                <int*>kernel_size.data,
                                                <int*>image_dim.data,
                                                ranges[x],
                                                ranges[x+1]-1,
                                                0,
                                                image_dim[1]-1,
                                                conditional);

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_int16(
      cnumpy.ndarray[cnumpy.int16_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.int16_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[short](<short*> input_buffer.data, 
                                               <short*> output_buffer.data, 
                                               <int*>kernel_size.data,
                                               <int*>image_dim.data,
                                               ranges[x],
                                               ranges[x+1]-1,
                                               0,
                                               image_dim[1]-1,
                                               conditional);

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def _median_filter_uint16(
      cnumpy.ndarray[cnumpy.uint16_t, ndim=2, mode='c'] input_buffer not None, 
      cnumpy.ndarray[cnumpy.uint16_t, ndim=2, mode='c'] output_buffer not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] kernel_size not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] ranges not None,
      cnumpy.ndarray[cnumpy.int32_t, ndim=1, mode='c'] image_dim not None,
      bool conditional):

    # init x range
    cdef int nthread = len(ranges) -1
    cdef int x = 0
    with nogil, parallel():
        # we are only dividing the image by column (only in x) in order to deal 
        # with n threads computation.
        for x in prange(nthread):
            median_filter.median_filter[uint16](<uint16*> input_buffer.data, 
                                                <uint16*> output_buffer.data, 
                                                <int*>kernel_size.data,
                                                <int*>image_dim.data,
                                                ranges[x],
                                                ranges[x+1]-1,
                                                0,
                                                image_dim[1]-1,
                                                conditional);
