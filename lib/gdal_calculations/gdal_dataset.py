# -*- coding: UTF-8 -*-
'''
Name: gdal_dataset.py
Purpose: GDAL Dataset and Band abstraction for simple tiled raster calculations
         (AKA "map algebra")

Author: Luke Pinner
Contributors: Matt Gregory

Notes:
       - Can handle rasters with different extents,cellsizes and coordinate systems
         as long as they overlap. If cellsizes/coordinate systems differ, the output 
         cellsize/coordinate system will be that of the leftmost Dataset in the expression.
       - gdal.Dataset and gdal.RasterBand and numpy.ndarray method and attribute calls are 
         passed down to the underlying gdal.Dataset, gdal.RasterBand and ndarray objects.
       - If numexpr is installed, it can be used to evaluate your expressions, but note 
         the limitations specified in the examples below.
To Do:
          Add environment setting to allow specifying cellsize handling when they
          differ. i.e. MAXOF, MINOF, number, Dataset

Examples:

    from gdal_calculations import *

    Env.extent = [xmin, ymin, xmax, ymax] # Other acceptable values:
                                          #  'INTERSECT' or 'MINOF' (default)
                                          #  'UNION' or 'MAXOF'
    Env.resampling = 'CUBIC'              # Other acceptable values:
                                          #  'NEAREST' (default)
                                          #  'AVERAGE'|'BILINEAR'|'CUBIC'
                                          #  'CUBICSPLINE'|'LANCZOS'|'MODE'
                                          #   gdal.GRA_* constant

    Env.reproject=True  #reproject on the fly if required

    Env.nodata=True  #Use a numpy.ma.MaskedArray to handle NoData values
                      #Note MaskedArrays are much slower...

    Env.overwrite=True

    gdal.UseExceptions()

    ds1=Dataset('../testdata/landsat_utm50.tif')#Projected coordinate system
    ds2=Dataset('../testdata/landsat_geo.tif')  #Geographic coordinate system

    #red=ds1[2].astype(np.float32) #You can use numpy type conversion (is slower)
    red=Float32(ds1[2]) #or use one of the provided type conversion functions (quicker as they use VRT's)
    nir=ds2[3]

    ndvi=(nir-red)/(nir+red)

    #Or in one go
    #ndvi=(ds2[3]-Float32(ds1[2])/(ds2[3]+Float32(ds1[2]))

    #Save the output
    ndvi=ndvi.save(r'../testdata/ndvi1.tif',options=['compress=LZW','TILED=YES'])

    #If you want to speed things up, use numexpr!
    #but there are a few limitations...
    import numexpr as ne

    #Must not be tiled for numexpr
    Env.tiled=False

    #No subscripting or methods in the expression
    #red=ds1[2].astype(np.float32)
    red=Float32(ds1[2])
    nir=ds2[3] #Some Int*/UInt* datasets cause segfaults, workaround is cast to Float32

    #Must be same coordinate systems and dimensions
    #The check_extent method will reproject and clip if required
    #This is done using virtual rasters (VRT) so is very quick
    nir,red=nir.check_extent(red)

    expr='(nir-red)/(nir+red)'
    ndvi=ne.evaluate(expr)

    #evaluate returns an ndarray not a Dataset
    #So need to write to a Temporary ArrayDataset
    ndvi=ArrayDataset(ndvi,prototype_ds=nir)
    ndvi=ndvi.save(r'../testdata/ndvi2.tif',options=['compress=LZW','TILED=YES'])

    #Get the raw numpy array data
    for block in red.ReadBlocksAsArray():
        print block.x_off,block.y_off,block.data.shape

    rawdata=red.ReadAsArray()
    print rawdata.shape

'''
# Copyright: (c) Luke Pinner 2013
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
#-------------------------------------------------------------------------------
__all__ = [ "Env", "Progress",
            "Dataset", "ArrayDataset",
            "ClippedDataset", "WarpedDataset",
            "Block", "Byte",
            "UInt16", "Int16",
            "UInt32", "Int32",
            "Float32", "Float64"
          ]

import numpy as np
from osgeo import gdal, gdal_array, osr
import os, tempfile, operator, itertools, sys
import geometry

# Processing environment
class Env(object):
    ''' Class for setting various environment properties
        Currently the following properties are supported:
            extent
              - one of "MINOF", "INTERSECT", "MAXOF", "UNION", [xmin,ymin,xmax,ymax]
              - Default = "MINOF"
            nodata
              - handle nodata using masked arrays - True/False
              - Default = False
            overwrite
              - overwrite if required - True/False
              - Default = False
            reproject
              - reproject if required - True/False
              - datasets are projected to the SRS of the first input dataset in an expression
              - Default = False
            resampling
              - one of "AVERAGE"|"BILINEAR"|"CUBIC"|"CUBICSPLINE"|"LANCZOS"|"MODE"|"NEAREST"|gdal.GRA_*)
              - Default = "NEAREST"
            tempdir
              - temporary working directory
              - Default = tempfile.tempdir
            tiled
              - use tiled processing - True/False
              - Default = True
    '''

    #Properties
    nodata=False
    overwrite=False
    progress=False
    reproject=False
    tiled=True

    @property
    def extent(self):
        try:return self._extent
        except AttributeError:
            self._extent='MINOF'
            return self._extent

    @extent.setter
    def extent(self, value):
        try:
            if value.upper() in ['MINOF','MAXOF','INTERSECT','UNION']:
                self._extent = value.upper()
        except AttributeError:
            try:xmin,ymin,xmax,ymax=[float(i) for i in value]
            except: raise AttributeError('%s not one of "MINOF"|"INTERSECT"|"MAXOF"|"UNION"|[xmin,ymin,xmax,ymax]'%repr(value))
            else:self._extent = [xmin,ymin,xmax,ymax]

    @property
    def resampling(self):
        try:return self._resampling
        except AttributeError:
            self._resampling=gdal.GRA_NearestNeighbour
            return self._resampling

    @resampling.setter
    def resampling(self, value):
        _lut={'AVERAGE': gdal.GRA_Average,
              'BILINEAR':gdal.GRA_Bilinear,
              'CUBIC':gdal.GRA_Cubic,
              'CUBICSPLINE':gdal.GRA_CubicSpline,
              'LANCZOS':gdal.GRA_Lanczos,
              'MODE':gdal.GRA_Mode,
              'NEAREST':gdal.GRA_NearestNeighbour}
        try:value=value.upper()
        except:pass
        if value in _lut:  #string
            self._resampling=_lut[value]
        elif value in _lut.values(): #gdal.GRA_*
            self._resampling=value
        else:raise AttributeError('%s not one of "AVERAGE"|"BILINEAR"|"CUBIC"|"CUBICSPLINE"|"LANCZOS"|"MODE"|"NEAREST"|gdal.GRA_*'%repr(value))

    @property
    def tempdir(self):
        return tempfile.tempdir

    @tempdir.setter
    def tempdir(self, value):
        if not os.path.isdir(value):raise RuntimeError('%s is not a directory'%value)
        tempfile.tempdir=value

Env=Env()

class Progress(object):
    def __init__(self,total=0):
        self.total=float(total)
        self.progress=0
        self.enabled=total>0
        if self.enabled:
            gdal.TermProgress_nocb(0)

    def update_progress(self):
        if self.enabled:
            self.progress+=1.0
            gdal.TermProgress_nocb(self.progress/self.total)

Env.progress=Progress()

# Type conversion helper functions
def Byte(dataset_or_band):
    return ConvertedDataset(dataset_or_band, gdal.GDT_Byte)
def UInt16(dataset_or_band):
    return ConvertedDataset(dataset_or_band, gdal.GDT_UInt16)
def Int16(dataset_or_band):
    return ConvertedDataset(dataset_or_band, gdal.GDT_Int16)
def UInt32(dataset_or_band):
    return ConvertedDataset(dataset_or_band, gdal.GDT_UInt32)
def Int32(dataset_or_band):
    return ConvertedDataset(dataset_or_band, gdal.GDT_Int32)
def Float32(dataset_or_band):
    return ConvertedDataset(dataset_or_band, gdal.GDT_Float32)
def Float64(dataset_or_band):
    return ConvertedDataset(dataset_or_band, gdal.GDT_Float64)

# Calculations classes
class Block(object):
    '''Block class thanks to Matt Gregory'''
    def __init__(self, dataset_or_band, x_off, y_off, x_size, y_size,*args,**kwargs):
        self.x_off = x_off
        self.y_off = y_off
        self.x_size = x_size
        self.y_size = y_size
        self.data = dataset_or_band.ReadAsArray(x_off, y_off, x_size, y_size,*args,**kwargs)

class RasterLike(object):
    '''Super class for Band and Dataset objects to avoid duplication '''

    def __init__(self):raise NotImplementedError

    def check_extent(self,other):
        ext=Env.extent

        srs1=osr.SpatialReference(self._srs)
        srs2=osr.SpatialReference(other._srs)

        reproj=(Env.reproject and not srs1.IsSame(srs2))              #Do we need to reproject?
        resamp=(self._gt[1],self._gt[5])!=(other._gt[1],other._gt[5]) #Do we need to resample?
        if  reproj or resamp:
            other=WarpedDataset(other,self._srs, self)

        geom1=geometry.GeomFromExtent(self.extent)
        geom2=geometry.GeomFromExtent(other.extent)

        if not geom1.Intersects(geom2):
            raise RuntimeError('Input datasets do not overlap')

        try:
            if ext.upper() in ['MINOF','INTERSECT']:
                ext=self.__minextent__(other)
            elif ext.upper() in ['MAXOF','UNION']:
                ext=self.__maxextent__(other)
        except AttributeError: pass #ext is [xmin,ymin,xmax,ymax]

        if self.extent!=ext: dataset1=ClippedDataset(self,ext)
        else: dataset1=self
        if other.extent!=ext: dataset2=ClippedDataset(other,ext)
        else: dataset2=other

        return dataset1,dataset2

    def __get_extent__(self):
        #Returns [(ulx,uly),(llx,lly),(lrx,lry),(urx,urx)]
        ext=geometry.GeoTransformToExtent(self._gt,self._x_size,self._y_size)
        return [ext[1][0],ext[1][1],ext[3][0],ext[3][1]]

    def __minextent__(self,other):
        ext1=self.extent
        ext2=geometry.SnapExtent(other.extent, other._gt, ext1, self._gt)
        return geometry.MinExtent(ext1,ext2)

    def __maxextent__(self,other):
        ext1=self.extent
        ext2=geometry.SnapExtent(other.extent, other._gt, ext1, self._gt)
        return geometry.MaxExtent(ext1,ext2)

    def getnodes(self, root, nodetype, name, index=True):
        '''Function for handling serialised VRT XML'''
        nodes=[]
        for i,node in enumerate(root[2:]):
            if node[0] == nodetype and node[1] == name:
                if index:nodes.append(i+2)
                else:nodes.append(node)
        return nodes

    def __read_vsimem__(self,fn):
        '''Read GDAL vsimem files'''
        vsifile = gdal.VSIFOpenL(fn,'r')
        gdal.VSIFSeekL(vsifile, 0, 2)
        vsileng = gdal.VSIFTellL(vsifile)
        gdal.VSIFSeekL(vsifile, 0, 0)
        return gdal.VSIFReadL(1, vsileng, vsifile)

    def __write_vsimem__(self,fn,data):
        '''Write GDAL vsimem files'''
        vsifile = gdal.VSIFOpenL(fn,'w')
        size = len(data)
        gdal.VSIFWriteL(data, 1, size, vsifile)
        return gdal.VSIFCloseL(vsifile)

    def read_blocks_as_array(self,nblocks=1):
        '''Read GDAL Datasets/Bands block by block'''

        ncols=self._x_size
        nrows=self._y_size
        xblock,yblock=self._block_size

        if xblock==ncols:
            yblock*=nblocks
        else:
            xblock*=nblocks

        for yoff in xrange(0, nrows, yblock):

            if yoff + yblock < nrows:
                ysize = yblock
            else:
                ysize  = nrows - yoff

            for xoff in xrange(0, ncols, xblock):
                if xoff + xblock < ncols:
                    xsize  = xblock
                else:
                    xsize = ncols - xoff

                yield Block(self, xoff, yoff, xsize, ysize )

    #CamelCase synonym
    ReadBlocksAsArray=read_blocks_as_array

    def __ndarrayattribute__(self,attr):
        '''Pass attribute gets down to ndarray'''
        if attr[:8] == '__array_' and Env.tiled:
            #raise RuntimeError('Env.tiled must be False to use numexpr.eval.')
            sys.stderr.write('Env.tiled must be False to use numexpr.eval.\n')
            return None
        if Env.tiled:
            '''Pass attribute gets down to the first block.
               Obviously won't work for b.shape etc...'''
            for b in self.ReadBlocksAsArray():
                return getattr(b.data,attr)
        else:
            return getattr(self.ReadAsArray(),attr)

    def __ndarraymethod__(self,attr):
        '''Pass method calls down to ndarrays and return a temporary dataset.'''

        def __method__(*args,**kwargs):
            if attr[:8] == '__array_' and Env.tiled:
                #raise RuntimeError('Env.tiled must be False to use numexpr.eval.')
                sys.stderr.write('Env.tiled must be False to use numexpr.eval.\n')
                return None

            if Env.tiled:
                tmpds=None
                for b in self.ReadBlocksAsArray():

                    if Env.nodata:
                        if b.data.ndim==2:mask=(b.data==self._nodata[0])
                        else:mask=np.array([b.data[i,:,:]==self._nodata[i] for i in range(b.data.shape[0])])
                        b.data=np.ma.MaskedArray(b.data,mask)
                        b.data.fill_value=self._nodata[0]
                        nodata=[self._nodata[0]]*self._nbands
                    else:nodata=self._nodata

                    data=getattr(b.data,attr)(*args,**kwargs)
                    datatype=gdal_array.NumericTypeCodeToGDALTypeCode(data.dtype.type)
                    if datatype is None:raise RuntimeError('Unsupported operation: %s'%attr)
                    if not tmpds:
                        tmpds=TemporaryDataset(self._x_size,self._y_size,self._nbands,
                                               datatype,self._srs,self._gt, nodata)

                    tmpds.write_data(data, b.x_off, b.y_off)

            else:
                data = self.ReadAsArray()
                if Env.nodata:
                    if data.ndim==2:mask=(data==self._nodata[0])
                    else:mask=np.array([data[i,:,:]==self._nodata[i] for i in range(data.shape[0])])
                    data=np.ma.MaskedArray(data,mask)
                    data.fill_value=self._nodata[0]
                    nodata=[self._nodata[0]]*self._nbands
                else:nodata=self._nodata

                data=getattr(data,attr)(*args,**kwargs)
                datatype=gdal_array.NumericTypeCodeToGDALTypeCode(data.dtype.type)
                if datatype is None:raise RuntimeError('Unsupported operation: %s'%attr)
                tmpds=TemporaryDataset(self._x_size,self._y_size,self._nbands,
                                       datatype,self._srs,self._gt, nodata)

                tmpds.write_data(data, 0, 0)

            tmpds.FlushCache()
            Env.progress.update_progress()
            return tmpds

        return __method__

    def __operation__(self,op,other=None,*args,**kwargs):
        ''' Perform basic calculations and return a temporary dataset'''

        if other and isinstance(other,RasterLike):
            dataset1,dataset2=self.check_extent(other)
        else:
            dataset1=self

        if Env.tiled:
            tmpds=None
            for b1 in dataset1.ReadBlocksAsArray():
                if Env.nodata:
                    if b1.data.ndim==2:mask=(b1.data==dataset1._nodata[0])
                    else:mask=np.array([b1.data[i,:,:]==dataset1._nodata[i] for i in range(b1.data.shape[0])])
                    b1.data=np.ma.MaskedArray(b1.data,mask)
                    b1.data.fill_value=dataset1._nodata[0]
                    nodata=[dataset1._nodata[0]]*dataset1._nbands
                else:nodata=dataset1._nodata

                if other:
                    if isinstance(other,RasterLike):
                        b2=Block(dataset2,b1.x_off, b1.y_off,b1.x_size, b1.y_size)

                        if Env.nodata:
                            if b2.data.ndim==2:mask=(b2.data==dataset2._nodata[0])
                            else:mask=np.array([b2.data[i,:,:]==dataset2._nodata[i] for i in range(b2.data.shape[0])])
                            b2.data=np.ma.MaskedArray(b2.data,mask)
                            b2.data.fill_value=dataset1._nodata[0]
                            nodata=[dataset1._nodata[0]]*dataset2._nbands
                        else:nodata=dataset1._nodata

                        data=op(b1.data, b2.data)
                    else: #Not a Band/Dataset, try the op directly
                        data=op(b1.data, other)
                else:
                    data=op(b1.data)

                if not tmpds:
                    datatype=gdal_array.NumericTypeCodeToGDALTypeCode(data.dtype.type)
                    if not datatype:datatype=gdal.GDT_Byte
                    tmpds=TemporaryDataset(dataset1._x_size,dataset1._y_size,dataset1._nbands,
                                           datatype,dataset1._srs,dataset1._gt,nodata)
                tmpds.write_data(data, b1.x_off, b1.y_off)
        else:
            a1 = dataset1.ReadAsArray()
            if Env.nodata:
                if a1.ndim==2:mask=(a1==dataset1._nodata[0])
                else:mask=np.array([a1[i,:,:]==dataset1._nodata[i] for i in range(a1.shape[0])])
                a1=np.ma.MaskedArray(a1,mask)
                a1.fill_value=dataset1._nodata[0]
                nodata=[dataset1._nodata[0]]*dataset1._nbands
            else:nodata=dataset1._nodata

            if other:
                if isinstance(other,RasterLike):
                    a2 = dataset2.ReadAsArray()

                    if Env.nodata:
                        if a2.ndim==2:mask=(a2==dataset2._nodata[0])
                        else:mask=np.array([a2[i,:,:]==dataset2._nodata[i] for i in range(a2.shape[0])])
                        a2=np.ma.MaskedArray(a2,mask)
                        a2.fill_value=dataset1._nodata[0]
                        nodata=[dataset1._nodata[0]]*dataset2._nbands
                    else:nodata=dataset1._nodata

                    data=op(a1, a2)
                else: #Not a Band/Dataset, try the op directly
                    data=op(a1, other)
            else:
                data=op(a1)

            datatype=gdal_array.NumericTypeCodeToGDALTypeCode(data.dtype.type)
            if not datatype:datatype=gdal.GDT_Byte
            tmpds=TemporaryDataset(dataset1._x_size,dataset1._y_size,dataset1._nbands,
                                   datatype,dataset1._srs,dataset1._gt,nodata)
            tmpds.write_data(data, 0, 0)

        #tmpds.FlushCache()
        Env.progress.update_progress()
        return tmpds

    #Basic arithmetic operations
    def __add__(self,other):
        return self.__operation__(operator.__add__,other)
    def __sub__(self,other):
        return self.__operation__(operator.__sub__,other)
    def __mul__(self,other):
        return self.__operation__(operator.__mul__,other)
    def __div__(self,other):
        return self.__operation__(operator.__div__,other)
    def __truediv__(self,other):
        return self.__operation__(operator.__truediv__,other)
    def __floordiv__(self,other):
        return self.__operation__(operator.__floordiv__,other)
    def __mod__(self,other):
        return self.__operation__(operator.__mod__,other)
    def __pow__(self,other):
        return self.__operation__(operator.__pow__,other)
    def __lshift__(self,other):
        return self.__operation__(operator.__lshift__,other)
    def __rshift__(self,other):
        return self.__operation__(operator.__rshift__,other)
    def __xor__(self,other):
        return self.__operation__(operator.__xor__,other)
    def __radd__(self,other):
        return self.__operation__(operator.__add__,other)
    def __rsub__(self,other):
        return self.__operation__(operator.__sub__,other)
    def __rmul__(self,other):
        return self.__operation__(operator.__mul__,other)
    def __rdiv__(self,other):
        return self.__operation__(operator.__div__,other)
    def __rtruediv__(self,other):
        return self.__operation__(operator.__truediv__,other)
    def __rfloordiv__(self,other):
        return self.__operation__(operator.__floordiv__,other)
    def __rmod__(self,other):
        return self.__operation__(operator.__mod__,other)
    def __rpow__(self,other):
        return self.__operation__(operator.__pow__,other)
    def __rlshift__(self,other):
        return self.__operation__(operator.__lshift__,other)
    def __rrshift__(self,other):
        return self.__operation__(operator.__rshift__,other)
    def __rxor__(self,other):
        return self.__operation__(operator.__xor__,other)

    #Boolean operations
    def __lt__(self,other):
        return self.__operation__(operator.__lt__,other)
    def __le__(self,other):
        return self.__operation__(operator.__le__,other)
    def __eq__(self,other):
        return self.__operation__(operator.__eq__,other)
    def __ne__(self,other):
        return self.__operation__(operator.__ne__,other)
    def __ge__(self,other):
        return self.__operation__(operator.__ge__,other)
    def __gt__(self,other):
        return self.__operation__(operator.__gt__,other)

class Band(RasterLike):
    ''' Subclass a GDALBand object without _actually_ subclassing it
        so we can add new methods.

        The 'magic' bit is using getattr to pass attribute or method calls
        through to the underlying GDALBand/ndarray objects
    '''
    def __init__(self,band,dataset,bandnum=0):
        self._band = band
        self.dataset=dataset #Keep a link to the parent Dataset object

        self._x_size=dataset._x_size
        self._y_size=dataset._y_size
        self._nbands=1
        self._bands=[bandnum]#Keep track of band number, zero based index
        self._data_type=self.DataType
        self._srs=dataset.GetProjectionRef()
        self._gt=dataset.GetGeoTransform()
        self._block_size=self.GetBlockSize()
        self._nodata=[band.GetNoDataValue()]

        self.extent=self.__get_extent__()

    def __getattr__(self, attr):
        '''Pass any other attribute or method calls
           through to the underlying GDALBand/ndarray objects'''
        if attr in dir(gdal.Band):return getattr(self._band, attr)
        elif attr in dir(np.ndarray):
            if callable(getattr(np.ndarray,attr)):return self.__ndarraymethod__(attr)
            else:return self.__ndarrayattribute__(attr)

    def get_raster_band(self,*args,**kwargs):
        '''So we can sort of treat Band and Dataset interchangeably'''
        return self
    GetRasterBand=get_raster_band

class Dataset(RasterLike):
    ''' Subclass a GDALDataset object without _actually_ subclassing it
        so we can add new methods.

        The 'magic' bit is using getattr to pass attribute or method calls
        through to the underlying GDALDataset/ndarray objects
    '''
    def __init__(self,filepath_or_dataset=None,*args):

        fp=filepath_or_dataset

        if type(fp) is gdal.Dataset:
            self._dataset = fp
        elif fp is not None:
            if os.path.exists(fp):
                self._dataset = gdal.Open(os.path.abspath(fp),*args)
            else:
                self._dataset = gdal.Open(fp,*args)

        self._x_size=self.RasterXSize
        self._y_size=self.RasterYSize
        self._nbands=self.RasterCount
        self._bands=range(self.RasterCount)
        self._data_type=self.GetRasterBand(1).DataType
        self._srs=self.GetProjectionRef()
        self._gt=self.GetGeoTransform()
        self._block_size=self.GetRasterBand(1).GetBlockSize()
        self._nodata=[b.GetNoDataValue() for b in self]

        self.extent=self.__get_extent__()

    def __del__(self):
        self._dataset=None
        del self._dataset

    def __getattr__(self, attr):
        '''Pass any other attribute or method calls
           through to the underlying GDALDataset object'''
        if attr in dir(gdal.Dataset):return getattr(self._dataset, attr)
        elif attr in dir(np.ndarray):
            if callable(getattr(np.ndarray,attr)):return self.__ndarraymethod__(attr)
            else:return self.__ndarrayattribute__(attr)

    def __getitem__(self, key):
        ''' Enable "somedataset[bandnum]" syntax'''
        b=self._dataset.GetRasterBand(key+1)
        return Band(self._dataset.GetRasterBand(key+1),self, key) #GDAL Dataset Band indexing starts at 1

    def __delitem__(self, key):
        ''' Enable "somedataset[bandnum]" syntax'''
        raise RuntimeError('Bands can not be deleted')

    def __setitem__(self, key):
        ''' Enable "somedataset[bandnum]" syntax'''
        raise RuntimeError('Bands can not be added or modifed')

    def __len__(self):
        ''' Enable "somedataset[bandnum]" syntax'''
        return self.RasterCount

    def __iter__(self):
        ''' Enable "for band in somedataset:" syntax'''
        for i in xrange(self.RasterCount):
            yield Band(self.GetRasterBand(i+1),self,i) #GDAL Dataset Band indexing starts at 1

    def get_raster_band(self,i=1): #GDAL Dataset Band indexing starts at 1
        return Band(self._dataset.GetRasterBand(i),self,i-1)

    #CamelCase synonym
    GetRasterBand=get_raster_band

    def band_read_blocks_as_array(self,i,*args,**kwargs):
        return Band(self.GetRasterBand(i), self, i-1).ReadBlocksAsArray(*args,**kwargs)

    #CamelCase synonym
    BandReadBlocksAsArray=band_read_blocks_as_array

    def Stack(self):
        return Stack([Band(self.GetRasterBand(i+1),self, i) for i in xrange(self.RasterCount)])

class TemporaryDataset(Dataset):
    def __init__(self,cols,rows,bands,datatype,srs='',gt=[],nodata=[]):
        use_exceptions=gdal.GetUseExceptions()
        gdal.UseExceptions()

        #if cols,rows,bands,datatype==[None,None,None,None]

        try: #Test to see if enough memory
            tmpdriver=gdal.GetDriverByName('MEM')
            tmpds=tmpdriver.Create('',cols,rows,bands,datatype)
            tmpds=None
            del tmpds

            self._filedescriptor=-1
            self._filename='/vsimem/%s.tif'%tempfile._RandomNameSequence().next()

        except (RuntimeError,MemoryError):
            self._filedescriptor,self._filename=tempfile.mkstemp(suffix='.tif')

        self._driver=gdal.GetDriverByName('GTIFF')
        self._dataset=self._driver.Create (self._filename,cols,rows,bands,datatype,['BIGTIFF=IF_SAFER'])

        if not use_exceptions:gdal.DontUseExceptions()
        self._dataset.SetGeoTransform(gt)
        self._dataset.SetProjection(srs)
        for i,val in enumerate(nodata[:bands]):
            try:self._dataset.GetRasterBand(i+1).SetNoDataValue(val)
            except TypeError:pass
        Dataset.__init__(self)

    def save(self,outpath,outformat='GTIFF',options=[]):
        self.FlushCache()
        ok=(os.path.exists(outpath) and Env.overwrite) or (not os.path.exists(outpath))
        if ok:
            driver=gdal.GetDriverByName(outformat)
            ds=driver.CreateCopy(outpath,self._dataset,options=options)
            ds=None
            del ds
            return Dataset(outpath)
        else:raise RuntimeError('Output %s exists and overwrite is not set.'%outpath)

    def write_data(self, data, x_off, y_off):
        if data.ndim==2:
            tmpbnd=self._dataset.GetRasterBand(1)
            tmpbnd.WriteArray(data, x_off, y_off)
        else:
            for i in range(data.shape[0]):
                tmpbnd=self._dataset.GetRasterBand(i+1)
                tmpbnd.WriteArray(data[i,:,:], x_off, y_off)

    def __del__(self):
        self._dataset=None
        del self._dataset
        if self._filedescriptor>-1:os.close(self._filedescriptor)
        self._driver.Delete(self._filename)

class ArrayDataset(TemporaryDataset):
    def __init__(self,array,extent=[],srs='',gt=[],nodata=[],prototype_ds=None):
        use_exceptions=gdal.GetUseExceptions()
        gdal.UseExceptions()

        #datatype=gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype.type)
        #Work around numexpr issue #112 - http://code.google.com/p/numexpr/issues/detail?id=112
        #until http://trac.osgeo.org/gdal/ticket/5223 is implemented.
        datatype=gdal_array.NumericTypeCodeToGDALTypeCode(array.view(str(array.dtype)).dtype.type)

        if array.ndim==2:
            rows,cols=array.shape
            bands=1
        else:
            rows,cols,bands=array.shape

        if prototype_ds:
            if not gt:gt=prototype_ds._gt
            if not srs:srs=prototype_ds._srs
            if not nodata:nodata=prototype_ds._nodata

        if extent:
            xmin,ymin,xmax,ymax=extent
            px,py=(xmax-xmin)/cols,(ymax-ymin)/rows
            gt=[xmin,px,0,ymax,0,-py]

        TemporaryDataset.__init__(self,cols,rows,bands,datatype,srs,gt,nodata)
        self.write_data(array,0,0)

class ClippedDataset(Dataset):
    '''Use a VRT to "clip" to min extent of two rasters'''

    def __init__(self,dataset_or_band,extent):
        self._tmpds=None
        self._parentds=dataset_or_band #keep a reference so it doesn't get garbage collected
        use_exceptions=gdal.GetUseExceptions()
        gdal.UseExceptions()

        try:                   #Is it a Band
            orig_ds=dataset_or_band.dataset._dataset
        except AttributeError: #No, it's a Dataset
            orig_ds=dataset_or_band._dataset

        #Basic info
        bands=dataset_or_band._bands
        gt = dataset_or_band._gt
        xoff,yoff,clip_xsize,clip_ysize=self._extent_to_offsets(extent,gt)
        ulx,uly=geometry.PixelToMap(xoff,yoff,gt)
        clip_gt=(ulx,gt[1],gt[2],uly,gt[4],gt[5])

        #Temp in memory VRT file
        fn='/vsimem/%s.vrt'%tempfile._RandomNameSequence().next()
        driver=gdal.GetDriverByName('VRT')
        driver.CreateCopy(fn,orig_ds)

        #Read XML from vsimem, requires gdal VSIF*
        vrtxml = self.__read_vsimem__(fn)
        gdal.Unlink(fn)

        #Parse the XML,
        #use gdals built-in XML handling to reduce external dependencies
        vrttree = gdal.ParseXMLString(vrtxml)
        getnodes=self.getnodes
        rasterXSize = getnodes(vrttree, gdal.CXT_Attribute, 'rasterXSize')[0]
        rasterYSize = getnodes(vrttree, gdal.CXT_Attribute, 'rasterYSize')[0]
        GeoTransform = getnodes(vrttree, gdal.CXT_Element, 'GeoTransform')[0]

        #Set new values
        vrttree[rasterXSize][2][1]=str(clip_xsize)
        vrttree[rasterYSize][2][1]=str(clip_ysize)
        vrttree[GeoTransform][2][1]='%f, %f, %f, %f, %f, %f'%clip_gt

        #Loop through bands
        vrtbandnodes=getnodes(vrttree, gdal.CXT_Element, 'VRTRasterBand',False)
        vrtbandkeys=getnodes(vrttree, gdal.CXT_Element, 'VRTRasterBand')
        for key in reversed(vrtbandkeys): del vrttree[key]#Reverse so we can delete from the end
                                                          #Don't assume bands are the last elements...
        i=0
        for node in vrtbandnodes:

            #Skip to next band if required
            bandnum=getnodes(node, gdal.CXT_Attribute, 'band')[0]
            #GDAL band indexing starts at one, internal band counter is zero based
            #if not int(node[sourcekey][sourceband][2][1])-1 in bands:continue
            if not int(node[bandnum][2][1])-1 in bands:continue

            NoDataValue=getnodes(node, gdal.CXT_Element, 'NoDataValue')[0]
            nodata=node[NoDataValue][2][1]
            node[NoDataValue][2][1]='0' #if clipping results in a bigger XSize/YSize, gdal initialises with 0
            for source in ['SimpleSource','ComplexSource','AveragedSource','KernelFilteredSource']:
                try:
                    sourcekey=getnodes(node, gdal.CXT_Element, source)[0]
                    break
                except IndexError:pass
            if source=='SimpleSource':node[sourcekey][1]='ComplexSource' #so the <NODATA> element can be used
            sourcefilename=getnodes(node[sourcekey], gdal.CXT_Element, 'SourceFilename')[0]
            relativeToVRT=getnodes(node[sourcekey][sourcefilename], gdal.CXT_Attribute, 'relativeToVRT')[0]
            if node[sourcekey][sourcefilename][relativeToVRT][2][1]=='1':
                node[sourcekey][sourcefilename][relativeToVRT][2][1]='0'
                node[sourcekey][sourcefilename][3][1]=os.path.join(os.path.dirname(fn),node[sourcekey][sourcefilename][3][1])
            sourceband=getnodes(node[sourcekey], gdal.CXT_Element, 'SourceBand')[0]

            #Skip to next band if required
            #GDAL band indexing starts at one, internal band counter is zero based
            #if not int(node[sourcekey][sourceband][2][1])-1 in bands:continue

            i+=1 #New band num
            vrtbandnum=getnodes(node, gdal.CXT_Attribute, 'band')[0]
            node[vrtbandnum][2][1]=str(i)

            srcrect=getnodes(node[sourcekey], gdal.CXT_Element, 'SrcRect')[0]
            srcXOff = getnodes(node[sourcekey][srcrect], gdal.CXT_Attribute, 'xOff')[0]
            srcYOff = getnodes(node[sourcekey][srcrect], gdal.CXT_Attribute, 'yOff')[0]
            srcXSize = getnodes(node[sourcekey][srcrect], gdal.CXT_Attribute, 'xSize')[0]
            srcYSize = getnodes(node[sourcekey][srcrect], gdal.CXT_Attribute, 'ySize')[0]
            node[sourcekey][srcrect][srcXOff][2][1]=str(xoff)
            node[sourcekey][srcrect][srcYOff][2][1]=str(yoff)
            node[sourcekey][srcrect][srcXSize][2][1]=str(clip_xsize)
            node[sourcekey][srcrect][srcYSize][2][1]=str(clip_ysize)

            dstrect=getnodes(node[sourcekey], gdal.CXT_Element, 'DstRect')[0]
            dstXOff = getnodes(node[sourcekey][srcrect], gdal.CXT_Attribute, 'xOff')[0]
            dstYOff = getnodes(node[sourcekey][srcrect], gdal.CXT_Attribute, 'yOff')[0]
            dstXSize = getnodes(node[sourcekey][dstrect], gdal.CXT_Attribute, 'xSize')[0]
            dstYSize = getnodes(node[sourcekey][dstrect], gdal.CXT_Attribute, 'ySize')[0]
            node[sourcekey][dstrect][dstXOff][2][1]='0'
            node[sourcekey][dstrect][dstYOff][2][1]='0'
            node[sourcekey][dstrect][dstXSize][2][1]=str(clip_xsize)
            node[sourcekey][dstrect][dstYSize][2][1]=str(clip_ysize)

            try: #Populate <NODATA> element with band NoDataValue as it might not be 0
                NODATA=getnodes(node[sourcekey], gdal.CXT_Element, 'NODATA')[0]
                node[sourcekey][NODATA]=nodata
            except IndexError:
                node[sourcekey].append([gdal.CXT_Element, 'NODATA', [gdal.CXT_Text, nodata]])

            vrttree.insert(key,node)

        #Open new clipped dataset
        vrtxml=gdal.SerializeXMLTree(vrttree)
        self._dataset=gdal.Open(vrtxml)

        if not use_exceptions:gdal.DontUseExceptions()

        Dataset.__init__(self)

    def _extent_to_offsets(self,extent,gt):
        xoff,yoff=geometry.MapToPixel(extent[0],extent[3],gt) #xmin,ymax in map coords
        xmax,ymin=geometry.MapToPixel(extent[2],extent[1],gt) #
        xsize=xmax-xoff
        ysize=ymin-yoff #Pixel coords start from upper left
        return (int(xoff),int(yoff),int(xsize+0.5),int(ysize+0.5))

    def __del__(self):
        self._dataset.GetDriver().Delete(self._dataset.GetDescription())
        self._dataset=None
        del self._dataset
        self._parent=None
        del self._parent

class ConvertedDataset(Dataset):
    '''Use a VRT to "convert" between datatypes'''

    def __init__(self,dataset_or_band,datatype):
        self._parentds=dataset_or_band #keep a reference so it doesn't get garbage collected
        use_exceptions=gdal.GetUseExceptions()
        gdal.UseExceptions()

        try:                   #Is it a Band
            orig_ds=dataset_or_band.dataset._dataset
        except AttributeError: #No, it's a Dataset
            orig_ds=dataset_or_band._dataset

        #Temp in memory VRT file
        fn='/vsimem/%s.vrt'%tempfile._RandomNameSequence().next()
        driver=gdal.GetDriverByName('VRT')
        driver.CreateCopy(fn,orig_ds)

        #Read XML from vsimem, requires gdal VSIF*
        vrtxml =self.__read_vsimem__(fn)
        gdal.Unlink(fn)

        #Parse the XML,
        #use gdals built-in XML handling to reduce external dependencies
        vrttree = gdal.ParseXMLString(vrtxml)
        getnodes=self.getnodes

        #Loop through bands, remove the bands, modify
        #then reinsert in case we are dealing with a "Band" object
        vrtbandnodes=getnodes(vrttree, gdal.CXT_Element, 'VRTRasterBand',False)
        vrtbandkeys=getnodes(vrttree, gdal.CXT_Element, 'VRTRasterBand')
        for key in reversed(vrtbandkeys): del vrttree[key]#Reverse so we can delete from the end
                                                          #Don't assume bands are the last elements...
        for i,band in enumerate(dataset_or_band._bands):
            node=getnodes(vrtbandnodes[band], gdal.CXT_Attribute, 'dataType')[0]
            try:vrtbandnodes[band][node][2][1]=gdal.GetDataTypeName(datatype)
            except TypeError:vrtbandnodes[band][node][2][1]=datatype
            node=getnodes(vrtbandnodes[band], gdal.CXT_Attribute, 'band')[0]
            vrtbandnodes[band][node][2][1]=str(i+1)
            vrttree.insert(key,vrtbandnodes[band])

        vrtxml=gdal.SerializeXMLTree(vrttree)

        #Temp in memory VRT file
        self._fn='/vsimem/%s.vrt'%tempfile._RandomNameSequence().next()
        self.__write_vsimem__(self._fn, vrtxml)
        self._dataset=gdal.Open(self._fn)

        if not use_exceptions:gdal.DontUseExceptions()

        Dataset.__init__(self)

    def __del__(self):
        Dataset.__del__(self)
        gdal.Unlink(self._fn)

class WarpedDataset(Dataset):

    def __init__(self,dataset_or_band, wkt_srs, snap_ds=None):

        use_exceptions=gdal.GetUseExceptions()
        gdal.UseExceptions()

        self._simple_fn='/vsimem/%s.vrt'%tempfile._RandomNameSequence().next()
        self._warped_fn='/vsimem/%s.vrt'%tempfile._RandomNameSequence().next()

        try:                   #Is it a Band
            orig_ds=dataset_or_band.dataset._dataset
        except AttributeError: #No, it's a Dataset
            orig_ds=dataset_or_band._dataset

        try: #Generate a warped VRT
            warped_ds=gdal.AutoCreateWarpedVRT(orig_ds,orig_ds.GetProjection(),wkt_srs, Env.resampling)
            #AutoCreateWarpedVRT doesn't create a vsimem filename and we need one
            warped_ds=gdal.GetDriverByName('VRT').CreateCopy(self._warped_fn,warped_ds)

        except Exception as e:
            raise RuntimeError('Unable to project on the fly. '+e.message)

        #Disable the following check as this will allow us to use a WarpedDataset to
        #resample Datasets and creating an AutoCreateWarpedVRT where input srs==output srs
        #will allways fail the test below...
        #if warped_ds.GetGeoTransform()==orig_ds.GetGeoTransform():
        #    raise RuntimeError('Unable to project on the fly. Make sure all input datasets have projections set.')

        if snap_ds:warped_ds=self._modify_vrt(warped_ds, orig_ds, snap_ds)
        self._dataset=self._create_simple_VRT(warped_ds,dataset_or_band)

        if not use_exceptions:gdal.DontUseExceptions()
        Dataset.__init__(self)

    def _create_simple_VRT(self,warped_ds,dataset_or_band):
        ''' Create a simple VRT XML string from a warped VRT (GDALWarpOptions)'''

        vrt=[]
        vrt.append('<VRTDataset rasterXSize="%s" rasterYSize="%s">' % (warped_ds.RasterXSize,warped_ds.RasterYSize))
        vrt.append('<SRS>%s</SRS>' % warped_ds.GetProjection())
        vrt.append('<GeoTransform>%s</GeoTransform>' % ', '.join(map(str,warped_ds.GetGeoTransform())))
        for i,band in enumerate(dataset_or_band._bands):
            rb=warped_ds.GetRasterBand(band+1) #gdal band index start at 1
            nodata=rb.GetNoDataValue()
            vrt.append('  <VRTRasterBand dataType="%s" band="%s">' % (gdal.GetDataTypeName(rb.DataType), i+1))
            vrt.append('    <SimpleSource>')
            vrt.append('      <SourceFilename relativeToVRT="0">%s</SourceFilename>' % (self._warped_fn))
            vrt.append('      <SourceBand>%s</SourceBand>'%(band+1))
            vrt.append('      <SrcRect xOff="0" yOff="0" xSize="%s" ySize="%s" />' % (warped_ds.RasterXSize,warped_ds.RasterYSize))
            vrt.append('      <DstRect xOff="0" yOff="0" xSize="%s" ySize="%s" />' % (warped_ds.RasterXSize,warped_ds.RasterYSize))
            vrt.append('    </SimpleSource>')
            if nodata is not None: # 0 is a valid value
                vrt.append('    <NoDataValue>%s</NoDataValue>' % nodata)
            vrt.append('  </VRTRasterBand>')
        vrt.append('</VRTDataset>')

        vrt='\n'.join(vrt)
        self.__write_vsimem__(self._simple_fn,vrt)
        return gdal.Open(self._simple_fn)

    def _modify_vrt(self, warp_ds, orig_ds, snap_ds):
        '''Modify the warped VRT to control pixel size and extent'''

        orig_gt=orig_ds.GetGeoTransform()
        orig_invgt=gdal.InvGeoTransform(orig_gt)[1]
        orig_cols = orig_ds.RasterXSize
        orig_rows = orig_ds.RasterYSize
        orig_ext=geometry.GeoTransformToExtent(orig_gt,orig_cols,orig_rows)
        orig_ext=[orig_ext[1][0],orig_ext[1][1],orig_ext[3][0],orig_ext[3][1]]
        blocksize=orig_ds.GetRasterBand(1).GetBlockSize()

        warp_gt=warp_ds.GetGeoTransform()
        warp_cols = warp_ds.RasterXSize
        warp_rows = warp_ds.RasterYSize
        warp_ext=geometry.GeoTransformToExtent(warp_gt,warp_cols,warp_rows)
        warp_ext=geometry.GeoTransformToExtent(warp_gt,warp_cols,warp_rows)
        warp_ext=[warp_ext[1][0],warp_ext[1][1],warp_ext[3][0],warp_ext[3][1]]

        snap_gt=snap_ds._gt
        snap_cols = snap_ds._x_size
        snap_rows = snap_ds._y_size
        snap_px=snap_gt[1]
        snap_py=abs(snap_gt[5])
        snap_ext=geometry.GeoTransformToExtent(snap_gt,snap_cols,snap_rows)
        snap_ext=[snap_ext[1][0],snap_ext[1][1],snap_ext[3][0],snap_ext[3][1]]

        new_ext=geometry.SnapExtent(warp_ext, warp_gt, snap_ext, snap_gt)
        new_px=snap_px
        new_py=snap_py
        new_cols = round((new_ext[2]-new_ext[0])/new_px)
        new_rows = round((new_ext[3]-new_ext[1])/new_py)
        new_gt=(new_ext[0],new_px,0,new_ext[3],0,-new_py)
        new_invgt=gdal.InvGeoTransform(new_gt)[1]

        #Read XML from vsimem, requires gdal VSIF*
        vrtxml = self.__read_vsimem__(self._warped_fn)

        #Parse the XML,
        #use gdals built-in XML handling to reduce external dependencies
        vrttree = gdal.ParseXMLString(vrtxml)
        getnodes=self.getnodes

        #Set new values
        rasterXSize = getnodes(vrttree, gdal.CXT_Attribute, 'rasterXSize')[0]
        rasterYSize = getnodes(vrttree, gdal.CXT_Attribute, 'rasterYSize')[0]
        GeoTransform = getnodes(vrttree, gdal.CXT_Element, 'GeoTransform')[0]
        BlockXSize = getnodes(vrttree, gdal.CXT_Element, 'BlockXSize')[0]
        BlockYSize = getnodes(vrttree, gdal.CXT_Element, 'BlockYSize')[0]

        wo = getnodes(vrttree, gdal.CXT_Element, 'GDALWarpOptions')[0]
        tr = getnodes(vrttree[wo], gdal.CXT_Element, 'Transformer')[0]
        gi = getnodes(vrttree[wo][tr], gdal.CXT_Element, 'GenImgProjTransformer')[0]
        sgt = getnodes(vrttree[wo][tr][gi], gdal.CXT_Element, 'SrcGeoTransform')[0]
        sigt = getnodes(vrttree[wo][tr][gi], gdal.CXT_Element, 'SrcInvGeoTransform')[0]
        dgt = getnodes(vrttree[wo][tr][gi], gdal.CXT_Element, 'DstGeoTransform')[0]
        digt = getnodes(vrttree[wo][tr][gi], gdal.CXT_Element, 'DstInvGeoTransform')[0]

        vrttree[rasterXSize][2][1]=str(new_cols)
        vrttree[rasterYSize][2][1]=str(new_rows)
        vrttree[GeoTransform][2][1]='%f, %f, %f, %f, %f, %f'%new_gt
        vrttree[BlockXSize][2][1]=str(blocksize[0])
        vrttree[BlockYSize][2][1]=str(blocksize[1])
        vrttree[wo][tr][gi][sgt][2][1]='%f, %f, %f, %f, %f, %f'%orig_gt
        vrttree[wo][tr][gi][sigt][2][1]='%f, %f, %f, %f, %f, %f'%orig_invgt
        vrttree[wo][tr][gi][dgt][2][1]='%f, %f, %f, %f, %f, %f'%new_gt
        vrttree[wo][tr][gi][digt][2][1]='%f, %f, %f, %f, %f, %f'%new_invgt

        #Open new dataset
        vrtxml=gdal.SerializeXMLTree(vrttree)
        self.__write_vsimem__(self._warped_fn, vrtxml)
        return gdal.Open(self._warped_fn)

    def __del__(self):
        Dataset.__del__(self)
        gdal.Unlink(self._warped_fn)
        gdal.Unlink(self._simple_fn)

class Stack(object):
    ''' Stub of basic implementation for a Stack of Band objects
    '''
    def __init__(self,bands):
        self._bands = bands

    def ReadBlocksAsArray(self,nblocks=1):
        for bands in itertools.izip(*[band.ReadBlocksAsArray(nblocks) for band in self._bands]):
            yield np.dstack(bands.data)

class DatasetStack(Stack):
    ''' Stub of basic implementation for a Stack of Band objects from multiple datasets
    '''
    def __init__(self,filepaths, band=1):
        self._bands = []
        for f in filepaths:
            d=Dataset(f)
            b=d.GetRasterBand(band)
            self._bands.append(b)

if __name__=='__main__':
    #Examples
    gdal.UseExceptions()

    Env.extent='MAXOF'
    Env.resampling='CUBIC'
    Env.overwrite=True
    Env.reproject=True
    Env.nodata=True

    ds1=Dataset('../testdata/landsat_utm50.tif')#Projected coordinate system
    ds2=Dataset('../testdata/landsat_geo.tif')  #Geographic coordinate system

    #red=ds1[2].astype(np.float32) #You can use numpy type conversion (is slower)
    red=Float32(ds1[2]) #or use one of the provided type conversion functions (quicker as they use VRT's)
    nir=ds2[3]

    ndvi=(nir-red)/(nir+red)

    #Or in one go
    #ndvi=(ds2[3]-Float32(ds1[2])/(ds2[3]+Float32(ds1[2]))
    ndvi=ndvi.save(r'../testdata/ndvi1.tif')

    #If you want to speed things up... use numexpr!
    #but there are a few limitations...
    import numexpr as ne

    #Must not be tiled for numexpr
    Env.tiled=False

    #No subscripting or methods in the expression
    #red=ds1[2].astype(np.float32)
    red=Float32(ds1[2])
    nir=ds2[3] #Some Int*/UInt* datasets cause segfaults, workaround is cast to Float32

    #Must be same coordinate systems and dimensions
    #The check_extent method will reproject and clip if required
    #This is done using virtual rasters (VRT) so is very quick
    nir,red=nir.check_extent(red)

    expr='(nir-red)/(nir+red)'
    ndvi=ne.evaluate(expr)

    #evaluate returns an ndarray not a Dataset
    #So need to write to a Temporary ArrayDataset
    ndvi=ArrayDataset(ndvi,prototype_ds=nir)
    ndvi=ndvi.save(r'../testdata/ndvi2.tif',options=['compress=LZW','TILED=YES'])

    ##Get the raw numpy array data
    #for block in red.ReadBlocksAsArray():
    #    print block.x_off,block.y_off,block.data.shape
    #
    #rawdata=red.ReadAsArray()
    #print rawdata.shape

