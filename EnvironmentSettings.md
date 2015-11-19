# The raster calculations library environment settings #

<pre> Name:    gdal_calculations.Env<br>
Purpose: Object for setting various environment properties<br>
Author: Luke Pinner<br>
Notes:<br>
Currently the following properties are supported:<br>
cellsize<br>
- one of 'DEFAULT','MINOF','MAXOF', [xres,yres], xyres<br>
- Default = "DEFAULT"<br>
enable_numexpr<br>
- this can break core numpy methods, such as numpy.sum([Dataset(foo),Dataset(bar)]<br>
extent<br>
- one of "MINOF", "INTERSECT", "MAXOF", "UNION", [xmin,ymin,xmax,ymax]<br>
- Default = "MINOF"<br>
nodata<br>
- handle nodata using masked arrays - True/False<br>
- Default = False<br>
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
- supports GDAL /vsimem (in memory) virtual filesystem<br>
- Default = tempfile.tempdir<br>
tiled<br>
- use tiled processing - True/False<br>
- Default = True<br>
</pre>