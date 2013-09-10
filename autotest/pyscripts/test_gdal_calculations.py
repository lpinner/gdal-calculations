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
import numpy as np

sys.path.append( '../pymod' )
sys.path.append( '../../lib' )

import gdaltest
from osgeo import gdal

###############################################################################
def test_gdal_calculations_py_1():
    ''' Test imports '''
    try:
        import gdal_calculations
        from gdal_calculations import *
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def test_gdal_calculations_py_2():
    ''' Test environment getting/setting '''
    try:
        from gdal_calculations import Env

        #Get/set cellsize
        assert Env.cellsize=="DEFAULT", "Env.cellsize != 'DEFAULT' ('%s')"%Env.cellsize
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
        assert Env.extent=="MINOF", "Env.extent != 'MINOF' ('%s')"%Env.extent
        Env.extent="MINOF"
        Env.extent="MAXOF"
        Env.extent=[1,1,2,2]
        try:Env.extent="INCORRECT"
        except:pass
        else:
            gdaltest.post_reason('Env.extent accepted an incorrect value')
            return 'fail'

        #Get/set extent
        assert Env.nodata==False, "Env.nodata != False ('%s')"%Env.nodata
        Env.nodata=True
        Env.nodata=False

        #Get/set overwrite
        assert Env.overwrite==False, "Env.overwrite != False ('%s')"%Env.overwrite
        Env.overwrite=True
        Env.overwrite=False

        #Get/set reproject
        assert Env.reproject==False, "Env.reproject != False ('%s')"%Env.reproject
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
        assert Env.tiled==True, "Env.tiled != True ('%s')"%Env.tiled
        Env.tiled=False
        Env.tiled=True

        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def test_gdal_calculations_py_3():
    ''' Test dataset open from filepath and gdal.Dataset object '''
    try:
        from gdal_calculations import Dataset
        from gdal_calculations.gdal_dataset import Band
        f='data/tgc_geo.tif'
        d=gdal.Open(f)
        dsf=Dataset(f)
        assert isinstance(dsf,Dataset), "isinstance(%s,Dataset)!=True"%repr(dsf)
        assert isinstance(dsf[0],Band), "isinstance(%s,Band)!=True"%repr(dsf[0])
        dsd=Dataset(d)
        assert isinstance(dsf,Dataset), "isinstance(%s,Dataset)!=True"%repr(dsf)
        assert isinstance(dsf[0],Band), "isinstance(%s,Band)!=True"%repr(dsf[0])
        dsf=None
        dsd=None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def test_gdal_calculations_py_4():
    ''' Test dataset reads and getattr calls '''
    try:
        from gdal_calculations import Env,Dataset
        Env.tiled=True

        f='data/tgc_geo.tif'
        dsf=Dataset(f)

        #ReadAsArray() (also a __getattr__ gdal.Dataset method)
        data=dsf.ReadAsArray()
        assert data.shape==(100,100), "data.shape==%s"%repr(data.shape)
        data=None

        #ReadBlocksAsArray() (gdal_calculations.Dataset method)
        for block in dsf.ReadBlocksAsArray():
            assert block.data.shape==(40,100), "data.shape==%s"%repr(block.data.shape)
            break
        del block

        #__getattr__ np attribute
        assert dsf.shape==(40,100), "dsf.shape==%s"%repr(dsf.shape)

        #__getattr__ np method that doesn't return a temp dataset
        Env.tiled=False
        s=dsf.sum()
        assert s==50005000, "dsf.sum()==%s"%repr(s)
        s=dsf.max()
        assert s==10000, "dsf.max()==%s"%repr(s)

        #__getattr__ np method that returns a temp dataset
        Env.tiled=True
        s=dsf.astype(np.int32)
        assert isinstance(s,Dataset), "isinstance(%s,Dataset)!=True"%repr(s)
        del s

        #__getattr__ gdal.Dataset method
        gt=dsf.GetGeoTransform()
        assert gt==(147.5, 0.01, 0.0, -34.5, 0.0, -0.01), "dsf.GetGeoTransform()==%s"%repr(gt)
        del gt

        Env.tiled=True
        dsf=None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def test_gdal_calculations_py_5():
    ''' Test type conversion functions '''
    try:
        from gdal_calculations import Dataset,Byte,Int16,UInt32,Int32,Float32,Float64

        #Regular raster
        f='data/tgc_geo.tif'
        dsf=Dataset(f)

        d=Byte(dsf)
        assert d._data_type==gdal.GDT_Byte, "data_type!=Byte (%s)"%gdal.GetDataTypeName(d._data_type)
        d=Int16(dsf)
        assert d._data_type==gdal.GDT_Int16, "data_type!=Int16 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=UInt32(dsf)
        assert d._data_type==gdal.GDT_UInt32, "data_type!=UInt32 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=Int32(dsf)
        assert d._data_type==gdal.GDT_Int32, "data_type!=Int32 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=Float32(dsf)
        assert d._data_type==gdal.GDT_Float32, "data_type!=Float32 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=Float64(dsf)
        assert d._data_type==gdal.GDT_Float64, "data_type!=Float64 (%s)"%gdal.GetDataTypeName(d._data_type)

        #Warped VRT
        f='data/tgc_alb.vrt'
        dsf=Dataset(f)

        d=Byte(dsf)
        assert d._data_type==gdal.GDT_Byte, "data_type!=Byte (%s)"%gdal.GetDataTypeName(d._data_type)
        d=None
        d=Int16(dsf)
        assert d._data_type==gdal.GDT_Int16, "data_type!=Int16 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=None
        d=UInt32(dsf)
        assert d._data_type==gdal.GDT_UInt32, "data_type!=UInt32 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=None
        d=Int32(dsf)
        assert d._data_type==gdal.GDT_Int32, "data_type!=Int32 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=None
        d=Float32(dsf)
        assert d._data_type==gdal.GDT_Float32, "data_type!=Float32 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=None
        d=Float64(dsf)
        assert d._data_type==gdal.GDT_Float64, "data_type!=Float64 (%s)"%gdal.GetDataTypeName(d._data_type)
        d=None

        dsf=None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def test_gdal_calculations_py_6():
    ''' Test some arithmetic '''
    try:
        from gdal_calculations import Dataset

        #Regular raster
        f='data/tgc_geo.tif'
        dsf=Dataset(f)

        val=dsf.ReadAsArray(0, 0, 1, 1)
        assert val==1, "dsf.ReadAsArray(0, 0, 1, 1)==%s"%repr(val)
        newds=(dsf[0]*2+1)/1
        val=newds.ReadAsArray(0, 0, 1, 1)
        assert val==3, "newds.ReadAsArray(0, 0, 1, 1)==%s"%repr(val)

        dsf,newds=None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def test_gdal_calculations_py_7():
    '''Test on-the-fly reprojection'''
    try:
        from gdal_calculations import Dataset, Env

        #Regular raster
        f='data/tgc_geo.tif'
        dsf=Dataset(f)
        #Warped raster
        f='data/tgc_alb.vrt'
        dsw=Dataset(f)

        try:out_alb=dsw+dsf
        except:pass
        else:raise Exception('operation succeeded when coordinate systems differ and Env.reproject is False')

        Env.reproject=True
        out_alb=dsw+dsf
        assert out_alb._srs==dsw._srs, "out_alb._srs!=dsw._srs"

        out_geo=dsf+dsw
        assert out_geo._srs==dsf._srs, "out_geo._srs==dsf._srs"

        dsf,dsw,out_alb,out_geo=None,None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def test_gdal_calculations_py_8():
    ''' Test on-the-fly clipping '''
    try:
        from gdal_calculations import Dataset, Env

        #Smaller raster
        f='data/tgc_geo.tif'
        ds1=Dataset(f)
        #Larger raster
        f='data/tgc_geo_resize.vrt'
        ds2=Dataset(f)
        #Even larger raster
        f='data/tgc_geo_resize_2.vrt'
        ds3=Dataset(f)
        #Larger raster (warped)
        #f='data/tgc_geo_resize_warp.vrt'
        #ds4=Dataset(f)

        #Default extent = Min extent
        out=ds1+ds2
        assert approx_equal(out.extent,ds1.extent),'out.extent!=ds1.extent'
        out=ds2+ds1
        assert approx_equal(out.extent,ds1.extent),'out.extent!=ds1.extent'
        out=ds3+ds2+ds1
        assert approx_equal(out.extent,ds1.extent),'out.extent!=ds1.extent'

        #Max extent
        Env.extent='MAXOF'
        out=ds1+ds2
        assert approx_equal(out.extent,ds2.extent),'Env.extent="MAXOF" and out.extent!=ds2.extent'
        out=ds1+ds2+ds3
        assert approx_equal(out.extent,ds3.extent),'Env.extent="MINOF" and out.extent!=ds3.extent'

        ds1,ds2,ds3,ds4,out=None,None,None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        gdaltest.post_reason(e.message)
        return 'fail'
    finally:cleanup()

def cleanup():
    for mod in list(sys.modules):
        if mod[:17]=='gdal_calculations':
            del sys.modules[mod]
    return

def approx_equal( a, b ):
    try: #Are they numeric?
        a,b = float(a),float(b)
        return gdaltest.approx_equal(a,b)
    except TypeError: #Maybe they're lists?
        eq=[gdaltest.approx_equal(a,b) for a,b in zip(a,b)]
        return 0 not in eq

###############################################################################
gdaltest_list = [
                 test_gdal_calculations_py_1,
                 test_gdal_calculations_py_2,
                 test_gdal_calculations_py_3,
                 test_gdal_calculations_py_4,
                 test_gdal_calculations_py_5,
                 test_gdal_calculations_py_6,
                 test_gdal_calculations_py_7,
                 test_gdal_calculations_py_8,
                ]

if __name__ == '__main__':
    gdaltest.setup_run( 'test_gdal_calculations_py' )
    gdaltest.run_tests( gdaltest_list )
    gdaltest.summarize()
