#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# Project:  Gdal Calculations GDAL/OGR style Test Suite
# Purpose:  gdal_calculations testing
# Author:   Luke Pinner
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
from osgeo import gdal, osr

sys.path.insert(0, '../gcore' )
sys.path.insert(0, '../pymod' )
sys.path.insert(0,'../../lib' )

import gdaltest
import test_py_scripts

###############################################################################
def test_gdal_calculations_py_1():
    ''' Test imports '''
    try:
        import gdal_calculations
        from gdal_calculations import Dataset
        return 'success'
    except Exception as e:
        return fail(e.message)
    finally:cleanup()

def test_gdal_calculations_py_2():
    ''' Test environment getting/setting '''
    try:
        from gdal_calculations import Env,Dataset

        #Get/set cellsize
        assert Env.cellsize=="DEFAULT", "Env.cellsize != 'DEFAULT' ('%s')"%Env.cellsize
        Env.cellsize="DEFAULT"
        Env.cellsize="MINOF"
        Env.cellsize="MAXOF"
        Env.cellsize=1
        Env.cellsize=[1,1]
        try:Env.cellsize="INCORRECT"
        except:pass
        else:return fail('Env.cellsize accepted an incorrect value')

        #Get/set extent
        assert Env.extent=="MINOF", "Env.extent != 'MINOF' ('%s')"%Env.extent
        Env.extent="MINOF"
        Env.extent="MAXOF"
        Env.extent=[1,1,2,2]
        try:Env.extent="INCORRECT"
        except:pass
        else:return fail('Env.extent accepted an incorrect value')

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
        else:return fail('Env.resampling accepted an incorrect value')

        #Get/set snap
        assert Env.snap is None, 'Env.snap should be None not %s'%repr(Env.snap)
        Env.snap=Dataset('data/tgc_geo.tif')
        assert isinstance(Env.snap,Dataset), 'Env.snap is not a Dataset'

        #Get/set srs
        epsg=4283
        wkt='GEOGCS["GDA94",DATUM["Geocentric_Datum_of_Australia_1994",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6283"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4283"]]'
        srs=osr.SpatialReference(wkt)
        assert Env.srs is None, 'Env.srs should be None'
        Env.srs=epsg
        assert isinstance(Env.srs,osr.SpatialReference), 'Env.srs is not a SpatialReference (EPSG)'
        Env.srs=wkt
        assert isinstance(Env.srs,osr.SpatialReference), 'Env.srs is not a SpatialReference (WKT)'
        Env.srs=srs
        assert isinstance(Env.srs,osr.SpatialReference), 'Env.srs is not a SpatialReference (SpatialReference)'
        gue=osr.GetUseExceptions()
        osr.DontUseExceptions()
        try:Env.srs=1
        except:pass
        else:return fail('Env.srs accepted an invalid EPSG (1)')
        try:Env.srs='INCORRECT'
        except:pass
        else:return fail('Env.extent accepted an invalid WKT ("INCORRECT")')
        try:Env.srs=osr.SpatialReference('sdfsdfsdf')
        except:pass
        else:return fail('Env.extent accepted an invalid SpatialReference')
        if gue:osr.UseExceptions()
        else:osr.DontUseExceptions()

        #Get/set tempdir
        assert Env.tempdir==tempfile.tempdir, 'Env.resampling != %s'%tempfile.tempdir
        Env.tempdir='tmp' #Exists in autotest/pyscripts/tmp
        try:Env.tempdir="INCORRECT"
        except:pass
        else:
            gdaltest.post_reason('Env.tempdir accepted an incorrect value')
            return 'fail'

        #Get/set tiled
        assert Env.tiled==True, "Env.tiled != True ('%s')"%Env.tiled
        Env.tiled=False
        Env.tiled=True

        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
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
        return fail(e.message)
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
        return fail(e.message)
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
        return fail(e.message)
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
        return fail(e.message)
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
        f='data/tgc_geo_resize_warp.vrt'
        ds4=Dataset(f)

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
        assert approx_equal(out.extent,ds3.extent),'Env.extent="MAXOF" and out.extent!=ds3.extent'

        #specified extent
        Env.extent=[147.55, -35.45, 148.45, -34.55]
        out=ds1+ds2
        assert approx_equal(out.extent,Env.extent),'Env.extent=%s and out.extent==%s'%(Env.extent,out.extent)
        out=ds1+ds2+ds4
        assert approx_equal(out.extent,Env.extent),'Env.extent=%s and out.extent==%s'%(Env.extent,out.extent)

        ds1,ds2,ds3,ds4,out=None,None,None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:cleanup()

def test_gdal_calculations_py_9():
    ''' Test on-the-fly resampling '''
    try:
        from gdal_calculations import Dataset, Env

        #Smaller raster
        f='data/tgc_geo.tif'
        ds1=Dataset(f)
        #Larger pixel raster
        f='data/tgc_geo_resize_warp.vrt'
        ds2=Dataset(f)

        #Default cellsize = left dataset
        out=ds1+ds2
        assert approx_equal([out._gt[1],out._gt[5]],[ds1._gt[1],ds1._gt[5]]),'out cellsize!=ds1 cellsize'
        out=ds2+ds1
        assert approx_equal([out._gt[1],out._gt[5]],[ds2._gt[1],ds2._gt[5]]),'out cellsize!=ds2 cellsize'

        #MINOF cellsize
        Env.cellsize='MINOF'
        out=ds1+ds2
        assert approx_equal([out._gt[1],out._gt[5]],[ds1._gt[1],ds1._gt[5]]),'Env.cellsize=MINOF and out cellsize!=ds1 cellsize'
        out=ds2+ds1
        assert approx_equal([out._gt[1],out._gt[5]],[ds1._gt[1],ds1._gt[5]]),'Env.cellsize=MINOF and out cellsize!=ds1 cellsize'

        #MAXOF cellsize
        Env.cellsize='MAXOF'
        out=ds1+ds2
        assert approx_equal([out._gt[1],out._gt[5]],[ds2._gt[1],ds2._gt[5]]),'Env.cellsize=MAXOF and out cellsize!=ds2 cellsize'
        out=ds2+ds1
        assert approx_equal([out._gt[1],out._gt[5]],[ds2._gt[1],ds2._gt[5]]),'Env.cellsize=MAXOF and out cellsize!=ds2 cellsize'

        #specific cellsize
        Env.cellsize=0.015
        out=ds1+ds2
        assert approx_equal([out._gt[1],out._gt[5]],[0.015,-0.015]),'Env.cellsize=0.015 and out cellsize==(%s,%s)'%(out._gt[1],abs(out._gt[5]))
        out=ds2+ds1
        assert approx_equal([out._gt[1],out._gt[5]],[0.015,-0.015]),'Env.cellsize=0.015 and out cellsize==(%s,%s)'%(out._gt[1],abs(out._gt[5]))
        Env.cellsize=(0.019,0.018)
        out=ds1+ds2
        assert approx_equal([out._gt[1],out._gt[5]],[0.019,-0.018]),'Env.cellsize=(0.019,0.018) and out cellsize==(%s,%s)'%(out._gt[1],abs(out._gt[5]))
        out=ds2+ds1
        assert approx_equal([out._gt[1],out._gt[5]],[0.019,-0.018]),'Env.cellsize=(0.019,0.018) and out cellsize==(%s,%s)'%(out._gt[1],abs(out._gt[5]))

        #Inappropriate cellsize
        Env.cellsize=25
        out=ds1+1 #Environment settings don't get applied with a single raster in the expression
        assert not approx_equal([out._gt[1],out._gt[5]],[25,-25]),'Env.cellsize=25 and out cellsize==%s'%(out._gt[1])
        try:out=ds1+ds1
        except:pass
        else:raise Exception('Inappropriate cellsize ds1+ds1')

        ds1,ds2,out=None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:cleanup()

def test_gdal_calculations_py_10():
    ''' Test snap dataset '''
    try:
        from gdal_calculations import Dataset, Env

        f='data/tgc_geo.tif'
        ds1=Dataset(f)
        f='data/tgc_geo_shifted.vrt'
        ds2=Dataset(f)
        f='data/tgc_geo_shifted_2.vrt'
        snap_ds=Dataset(f)

        Env.snap=ds2
        out=ds1+ds2
        assert approx_equal([out._gt[0],out._gt[3]],[ds2._gt[0],ds2._gt[3]]),'out geotransform doesnae match ds2'

        Env.snap=snap_ds
        out=ds2+ds1
        assert approx_equal([out._gt[0],out._gt[3]],[snap_ds._gt[0],snap_ds._gt[3]]),'out geotransform doesnae match snap_ds'

        ds1,ds2,snap_ds,out=None,None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:cleanup()

def test_gdal_calculations_py_11():
    ''' Test snap dataset '''
    try:
        from gdal_calculations import Dataset, Env

        f='data/tgc_geo.tif'
        ds1=Dataset(f)
        f='data/tgc_geo_shifted.vrt'
        ds2=Dataset(f)
        f='data/tgc_geo_shifted_2.vrt'
        snap_ds=Dataset(f)

        Env.snap=ds2
        out=ds1+ds2
        assert approx_equal([out._gt[0],out._gt[3]],[ds2._gt[0],ds2._gt[3]]),'out geotransform doesnae match ds2'

        Env.snap=snap_ds
        out=ds2+ds1
        assert approx_equal([out._gt[0],out._gt[3]],[snap_ds._gt[0],snap_ds._gt[3]]),'out geotransform doesnae match snap_ds'

        ds1,ds2,snap_ds,out=None,None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:cleanup()

def test_gdal_calculations_py_12():
    ''' Test srs '''
    try:
        from gdal_calculations import Dataset, Env

        Env.srs=3112 #GDA94 / Australia Lambert

        f='data/tgc_geo.tif' #GDA94 / Geographic
        ds1=Dataset(f)
        f='data/tgc_alb.vrt' #GDA94 / Australia Albers
        ds2=Dataset(f)

        out=ds1[0]+ds2[0]
        outsrs=osr.SpatialReference(out._srs)
        assert Env.srs.IsSame(outsrs),'out srs != Env.srs'

        ds1,ds2,out=None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:cleanup()

def test_gdal_calculations_py_13():
    ''' Test nodata handling '''
    try:
        from gdal_calculations import Dataset, Env

        f='data/tgc_geo_resize.vrt'
        dsf=Dataset(f, gdal.GA_ReadOnly)

        Env.nodata=True

        #1st pixel should be 0
        #tgc_geo_resize.vrt does not have a nodata value set
        val=dsf[0].ReadAsArray(0, 0, 1, 1)
        assert val==0, "dsf[0].ReadAsArray(0, 0, 1, 1)==%s"%repr(val)

        #Add 1.
        #Create a copy of the VRT so GDAL doesn't modify it on disk
        dsg=Dataset(gdal.GetDriverByName('VRT').CreateCopy('',dsf._dataset))
        out=dsg[0]+1
        val=out.ReadAsArray(0, 0, 1, 1)
        assert val==1, "dsg[0] nodata not set (%s) out.ReadAsArray(0, 0, 1, 1)==%s"% \
                        (repr(dsf[0].GetNoDataValue()), repr(val))

        #Set nodata and add 1 again
        dsg[0].SetNoDataValue(0)
        out=dsg[0]+1
        val=out.ReadAsArray(0, 0, 1, 1)
        assert val==0, "dsg[0] nodata is set (%s) out.ReadAsArray(0, 0, 1, 1)==%s"% \
                        (repr(dsf[0].GetNoDataValue()), repr(val))

        dsf,dsg,out=None,None,None
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:cleanup()

def test_gdal_calculations_py_14():
    ''' Test numexpr '''
    try:
        from gdal_calculations import Dataset, Env
        import numexpr as ne

        Env.enable_numexpr=True

        f='data/tgc_geo.tif'
        ds1=Dataset(f)
        f='data/tgc_geo_resize.vrt'
        ds2=Dataset(f)

        #Must not be tiled for numexpr
        try:ne.evaluate('ds1+1')
        except:pass
        else:fail('numexpr.evaluate succeeded and Env.tiled=True')
        Env.tiled=False
        out=ne.evaluate('ds1+1') #returns a numpy ndarray
        assert out.shape==(ds1.RasterXSize,ds1.RasterYSize), "out.shape == %s not %s"% \
                        (repr(out.shape), repr((ds1.RasterXSize,ds1.RasterYSize)))

        #No subscripting or methods in the expression
        try:ne.evaluate('Float32(ds1[0])+1')
        except:pass
        else:fail('numexpr.evaluate succeeded and with subscripting / methods in the expression')

        #Must be same coordinate systems and dimensions
        #The apply_environment method will reproject/resample/clip if required
        try:ne.evaluate('ds1+ds2')
        except:pass
        else:fail('numexpr.evaluate succeeded when ds1 and ds2 extents differ')
        ds3,ds4=ds1.apply_environment(ds2)
        out=ne.evaluate('ds3+ds4') #returns a numpy ndarray
        assert out.shape==(ds1.RasterXSize,ds1.RasterYSize), "out.shape == %s not %s"% \
                        (repr(out.shape), repr((ds1.RasterXSize,ds1.RasterYSize)))

        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:
        cleanup()
        cleanup('numexpr')

def test_gdal_calculations_py_15():
    ''' Test numpy methods '''
    try:
        from gdal_calculations import Dataset, Env
        Env.reproject=True

        #Regular raster
        f='data/tgc_geo.tif'
        dsf=Dataset(f)
        #Warped raster
        f='data/tgc_alb.vrt'
        dsw=Dataset(f)

        out=np.sum([dsf,dsw])
        out=np.mean([dsf,dsw])
        return 'success'
    except ImportError:
        return 'skip'
    except Exception as e:
        return fail(e.message)
    finally:
        cleanup()

def test_gdal_calculations_py_16():
    ''' Test commandline '''
    #In the unlikely event this code ever ends up _in_ GDAL, this function
    #will need modification to comply with standard GDAL script/sample paths
    try:
        from gdal_calculations import Dataset, __version__
        cd=os.path.abspath(os.curdir)

        testdir=os.path.abspath(os.path.dirname(__file__))
        datadir=os.path.join(testdir,'data')
        tmpdir=os.path.join(testdir,'tmp')
        topdir=os.path.abspath(os.path.join(testdir,'..','..'))
        bindir=os.path.join(topdir,'bin')
        libdir=os.path.join(topdir,'lib')

        f1=os.path.join(datadir,'tgc_geo.tif')
        f2=os.path.join(datadir,'tgc_geo_resize.vrt')

        #test commandline scripts (assumes orig googlecode svn structure, not various gdal setups)
        #All the commandline gdal_calculate and gdal_calculate.cmd scripts do
        #is call python -m gdal_calculations <args>
        os.chdir(libdir) #So script can find module
        script=os.path.join(bindir,'gdal_calculate')
        if sys.platform == 'win32':script+='.cmd'
        #gdaltest.runexternal() doesn't read stderr
        ret = gdaltest.runexternal(script + ' --version --redirect-stderr').strip()
        assert ret==__version__,'Script version (%s) != %s'%(ret,__version__)
        try:del ret
        except:pass

        #Try running something that numexpr can handle
        #if numexpr is not available, this should be handled by standard python eval
        out=os.path.join(tmpdir,'tgc_15a.ers')
        args='--calc="ds+1" --ds="%s" --outfile="%s" --numexpr --of=ERS --redirect-stderr' % (f1,out)
        try:
            ret = gdaltest.runexternal(script+' '+args).strip()
            ds=Dataset(out)
            del ds
        except Exception as e:raise RuntimeError(ret+'\n'+e.message)
        finally:
            try:
                gdal.Unlink(out)
                gdal.Unlink(out[:-4])
            except:pass
        del ret

        #Try running something that numexpr can't handle,
        #this should be handled by standard python eval
        out=os.path.join(tmpdir,'tgc_15b.ers')
        args='--calc="ds1+ds2" --ds1="%s" --ds2="%s" --outfile="%s" --numexpr --of=ERS --redirect-stderr' % (f1,f2, out)
        try:
            ret = gdaltest.runexternal(script+' '+args).strip()
            ds=Dataset(out)
            del ds
        except Exception as e:raise RuntimeError(ret+'\n'+e.message)
        finally:
            try:
                gdal.Unlink(out)
                gdal.Unlink(out[:-4])
            except:pass
        del ret


        return 'success'
    except Exception as e:
        return fail(e.message)
    finally:
        os.chdir(cd)
        cleanup()

#-----------------------------------------------------------
def fail(reason):
    gdaltest.post_reason(reason)
    return 'fail'

def cleanup(name='gdal_calculations'):
    ''' Unload specified modules '''
    for mod in list(sys.modules):
        if mod[:len(name)]==name:
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
                 test_gdal_calculations_py_9,
                 test_gdal_calculations_py_10,
                 test_gdal_calculations_py_11,
                 test_gdal_calculations_py_12,
                 test_gdal_calculations_py_13,
                 test_gdal_calculations_py_14,
                 test_gdal_calculations_py_15,
                 test_gdal_calculations_py_16,
                ]

if __name__ == '__main__':
    gdaltest.setup_run( 'test_gdal_calculations_py' )
    gdaltest.run_tests( gdaltest_list )
    gdaltest.summarize()
