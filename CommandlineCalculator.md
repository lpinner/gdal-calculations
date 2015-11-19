# The commandline raster calculator #
<pre> Name:    gdal_calculate<br>
Purpose: Perform simple tiled raster calculations (AKA "map algebra")<br>
from the commandline<br>
Notes:<br>
- Can handle rasters with different extents,cellsizes and coordinate<br>
systems as long as they overlap. If coordinate systems differ, the<br>
output coordinate system will be that of the leftmost Dataset<br>
in the expression.<br>
- GDALDataset and RasterBand and numpy method and attribute calls are<br>
passed down to the underlying GDALDataset, GDALRasterBand and ndarray<br>
objects.<br>
- If numexpr is installed, gdal_calculate will try to use numexpr.evaluate<br>
to process the expression as it is much faster. However, numexpr<br>
expressions are very limited: tiled processing, on-the-fly reprojection,<br>
extent clipping/snapping, method/function calls and subscripting are<br>
not supported.<br>
<br>
Required parameters:<br>
--calc     : calculation in numpy syntax, rasters specified as using<br>
any legal python variable name syntax, band numbers are<br>
specified using square brackets (zero based indexing)<br>
--outfile  : output filepath<br>
--{*}      : filepaths for raster variables used in --calc<br>
e.g. --calc='(someraster[0]+2)*c' --someraster='foo.tif' --c='bar.tif'<br>
<br>
Optional parameters:<br>
--of            : GDAL format for output file (default "GTiff")')<br>
--co            : Creation option to the output format driver.<br>
Multiple options may be listed.<br>
--cellsize      : one of DEFAULT|MINOF|MAXOF|"xres yres"|xyres<br>
(Default=DEFAULT, leftmost dataset in expression)<br>
--extent        : one of MINOF|INTERSECT|MAXOF|UNION|"xmin ymin xmax ymax"<br>
(Default=MINOF)<br>
--nodata        : handle nodata using masked arrays (Default=False)<br>
uses numpy.ma.MaskedArray to handle NoData values<br>
MaskedArrays can be much slower...<br>
--notile        : don't use tiled processing, faster but uses more memory (Default=False)<br>
--numexpr       : Enable numexpr evaluation (Default=False)<br>
--overwrite     : overwrite if required (Default=False)<br>
-q --quiet      : Don't display progress (Default=False)<br>
--reproject     : reproject if required (Default=False)<br>
datasets are projected to the SRS of the first input<br>
dataset in an expression<br>
--resampling    : one of "AVERAGE"|"BILINEAR"|"CUBIC"|"CUBICSPLINE"|<br>
"LANCZOS"|"MODE"|"NEAREST"|gdal.GRA_*)<br>
(Default="NEAREST")<br>
--snap           : filepath of a raster to snap extent coordinates to.<br>
--srs            : the output spatial reference system<br>
one of osgeo.osr.SpatialReference (object)|WKT (string)|EPSG code (integer)<br>
(Default = None)<br>
--tempdir        : filepath to temporary working directory<br>
<br>
Examples:<br>
gdal_calculate --outfile=../testdata/ndvi.tif       \<br>
--calc="((nir[3]-red[2].astype(numpy.float32))/(nir[3]+red[2].astype(numpy.float32)))" \<br>
--red=../testdata/landsat_utm50.tif  \<br>
--nir=../testdata/landsat_geo.tif    \<br>
--overwrite --reproject --extent=MAXOF<br>
<br>
#Using numexpr. Note limitations.<br>
gdal_calculate --outfile=../testdata/ndvi.tif       \<br>
--calc="((nir-red)/(nir+red))"                 \<br>
--red=../testdata/singleband_red_utm50.tif     \<br>
--nir=../testdata/singleband_nir_utm50.tif     \<br>
--overwrite --notile --numexpr<br>
</pre>