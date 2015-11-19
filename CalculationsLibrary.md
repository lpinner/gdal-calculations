# The raster calculations library #

<pre> Name:    gdal_calculations<br>
Purpose: GDAL Dataset and Band abstraction for simple tiled raster calculations<br>
(AKA "map algebra")<br>
Author: Luke Pinner<br>
Contributors: Matt Gregory<br>
Notes:<br>
- Can handle rasters with different extents,cellsizes and coordinate systems<br>
as long as they overlap. If extents/cellsizes/coordinate systems differ, the output<br>
extent/cellsize will the MINOF/MAXOF of input datasets, while the output<br>
coordinate system will be that of the leftmost Dataset in the expression<br>
unless Env.extent/Env.cellsize/Env.srs are specified.<br>
- gdal.Dataset and gdal.RasterBand and numpy.ndarray method and attribute calls are<br>
passed down to the underlying gdal.Dataset, gdal.RasterBand and ndarray objects.<br>
- If numexpr is installed, it can be used to evaluate your expressions, but note<br>
the limitations specified in the examples below.<br>
<br>
Classes/Objects:<br>
Dataset(filepath_or_dataset ,*args)<br>
- Base Dataset class.<br>
- Instantiate by passing a path or gdal.Dataset object.<br>
- Supports gdal.Dataset and numpy.ndarray method and attribute calls.<br>
- Supports arithmetic operations (i.e ds1 + ds2)<br>
Band<br>
- Returned from Dataset[i] (zero based) or Dataset.GetRasterBand(j) (1 based)<br>
methods, not instantiated directly.<br>
- Supports gdal.RasterBand and numpy.ndarray method and attribute calls.<br>
- Supports arithmetic operations (i.e ds1[0] + ds2.GetRasterBand(1))<br>
ClippedDataset(dataset_or_band, extent)<br>
- Subclass of Dataset.<br>
- Uses VRT functionality to modify extent.<br>
ConvertedDataset(dataset_or_band, datatype)<br>
- Subclass of Dataset.<br>
- Uses VRT functionality to modify datatype.<br>
- Returned by the type conversion functions, not instantiated directly.<br>
TemporaryDataset(cols,rows,bands,datatype,srs='',gt=[],nodata=[])<br>
- Subclass of Dataset.<br>
- A temporary raster that only persists until it goes out of scope.<br>
- Stored in the Env.tempdir directory, which may be on disk or in<br>
memory (/vsimem).<br>
- Can be made permanent with the save method.<br>
WarpedDataset(dataset_or_band, wkt_srs, snap_ds=None, snap_cellsize=None)<br>
- Subclass of Dataset.<br>
- Uses VRT functionality to warp Dataset.<br>
ArrayDataset(array,extent=[],srs='',gt=[],nodata=[], prototype_ds=None)<br>
- Subclass of TemporaryDataset.<br>
- Instantiate by passing a numpy ndarray and georeferencing information<br>
or a prototype Dataset.<br>
DatasetStack(filepaths, band=0)<br>
- Stack of bands from multiple datasets<br>
- Similar to gdalbuildvrt -separate etc... functionality, except the class<br>
can handle rasters with different extents,cellsizes and coordinate systems<br>
as long as they overlap.<br>
Env - Object for setting various environment properties.<br>
- This is instantiated on import.<br>
- The following properties are supported:<br>
cellsize<br>
- one of 'DEFAULT','MINOF','MAXOF', [xres,yres], xyres<br>
- Default = "DEFAULT"<br>
enable_numexpr<br>
- this can break core numpy methods, such as numpy.sum([Dataset(foo),Dataset(bar)]<br>
- Default = False<br>
extent<br>
- one of "MINOF", "INTERSECT", "MAXOF", "UNION", [xmin,ymin,xmax,ymax]<br>
- Default = "MINOF"<br>
nodata<br>
- handle nodata using masked arrays - True/False<br>
- Default = False<br>
ntiles<br>
- number of tiles to process at a time<br>
- Default = 1<br>
overwrite<br>
- overwrite if required - True/False<br>
- Default = False<br>
reproject<br>
- reproject if required - True/False<br>
- datasets are projected to the SRS of the first input dataset in an expression<br>
- Default = False<br>
resampling<br>
- one of "AVERAGE"|"BILINEAR"|"CUBIC"|"CUBICSPLINE"|"LANCZOS"|"MODE"|"NEAREST"|gdal.GRA_*)<br>
- Default = "NEAREST"<br>
snap<br>
- a gdal_calculations.Dataset/Band object<br>
- Default = None<br>
srs<br>
- the output spatial reference system<br>
- one of osgeo.osr.SpatialReference (object)|WKT (string)|EPSG code (integer)<br>
- Default = None<br>
tempdir<br>
- temporary working directory<br>
- Default = tempfile.tempdir<br>
tiled<br>
- use tiled processing - True/False<br>
- Default = True<br>
Byte, UInt16, Int16, UInt32, Int32, Float32, Float64<br>
- Type conversions functions<br>
- Returns a ConvertedDataset object<br>
</pre>
```
#Examples
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

#You can use dataset[subscript] to access bands
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

#Must enable numexpr
Env.enable_numexpr=True

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
```