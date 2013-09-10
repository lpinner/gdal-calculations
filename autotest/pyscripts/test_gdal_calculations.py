#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# $Id: test_gdal_calculations_py.py 26369 2013-08-25 19:48:28Z goatbar $
#
# Project:  GDAL/OGR Test Suite
# Purpose:  gdal_calculations testing
# Author:   Luke Pinner
#
###############################################################################
# Copyright (c) 2013, Luke Pinner
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

import sys
import os
import shutil
import tempfile

sys.path.append( '../pymod' )
sys.path.append( '../../lib' )

import gdaltest
from osgeo import gdal

###############################################################################
# Test import
def test_gdal_calculations_py_1():
    try:
        import gdal_calculations
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'

# Test environment getting/setting
def test_gdal_calculations_py_2():
    try:
        from gdal_calculations import Env

        #Get/set cellsize
        assert Env.cellsize=="DEFAULT", "Env.cellsize != 'DEFAULT'"
        Env.cellsize="DEFAULT"
        Env.cellsize="MINOF"
        Env.cellsize="MAXOF"
        Env.cellsize=1
        Env.cellsize=[1,1]
        try:Env.cellsize="INCORRECT"
        except:pass
        else:
            gdaltest.post_reason('Env.cellsize accepted an incorrect value')
            return 'fail'

        #Get/set extent
        assert Env.extent=="MINOF", "Env.extent != 'MINOF'"
        Env.extent="MINOF"
        Env.extent="MAXOF"
        Env.extent=[1,1,2,2]
        try:Env.extent="INCORRECT"
        except:pass
        else:
            gdaltest.post_reason('Env.extent accepted an incorrect value')
            return 'fail'

        #Get/set extent
        assert Env.nodata==False, "Env.nodata != False"
        Env.nodata=True
        Env.nodata=False

        #Get/set overwrite
        assert Env.overwrite==False, "Env.overwrite != False"
        Env.overwrite=True
        Env.overwrite=False

        #Get/set reproject
        assert Env.reproject==False, "Env.reproject != False"
        Env.reproject=True
        Env.reproject=False

        #Get/set resampling
        assert Env.resampling==gdal.GRA_NearestNeighbour, 'Env.resampling != "NEAREST"'
        Env.resampling="AVERAGE"
        Env.resampling="BILINEAR"
        Env.resampling="CUBIC"
        Env.resampling="CUBICSPLINE"
        Env.resampling="LANCZOS"
        Env.resampling="MODE"
        Env.resampling="NEAREST"
        try:Env.resampling="INCORRECT"
        except:pass
        else:
            gdaltest.post_reason('Env.resampling accepted an incorrect value')
            return 'fail'

        #Get/set tempdir
        assert Env.tempdir==tempfile.tempdir, 'Env.resampling != %s'%tempfile.tempdir

        #Get/set tiled
        assert Env.tiled==True, "Env.tiled != True"
        Env.tiled=False
        Env.tiled=True

        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'

# Test dataset open from filepath and gdal.Dataset object
def test_gdal_calculations_py_3():
    try:
        import gdal_calculations
        f='data/tgc_geo.tif'
        d=gdal.Open(f)
        dsf=gdal_calculations.Dataset(f)
        dsd=gdal_calculations.Dataset(d)
        dsf=None
        dsd=None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'

# Test dataset reads
def test_gdal_calculations_py_4():
    try:
        import gdal_calculations
        f='data/tgc_geo.tif'
        d=gdal.Open(f)
        dsf=gdal_calculations.Dataset(f)
        data=dsf.ReadAsArray()
        assert data.shape==(100,100), "data.shape==%s"%repr(data.shape)
        data=None
        for block in dsf.ReadBlocksAsArray():
            assert block.data.shape==(40,100), "data.shape==%s"%repr(block.data.shape)
            break
        del block
        dsd=None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'

###############################################################################
gdaltest_list = [
                 test_gdal_calculations_py_1,
                 test_gdal_calculations_py_2,
                 test_gdal_calculations_py_3,
                 test_gdal_calculations_py_4,
                ]

#raster_list=setup()

if __name__ == '__main__':

    gdaltest.setup_run( 'test_gdal_calculations_py' )
    gdaltest.run_tests( gdaltest_list )
    gdaltest.summarize()
    del raster_list
