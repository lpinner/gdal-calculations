# GDAL Calculations #

This package enables simple tiled (or untiled if desired) raster calculations (AKA "map algebra") from the commandline or from within your python scripts. The package can reproject, resample and clip/snap extents on-the-fly so supports rasters with different extents, cellsizes and coordinate systems as long as they overlap.

The package includes a [commandline raster calculator](CommandlineCalculator.md) and a [raster calculations library](CalculationsLibrary.md).

### News ###
Version 1.1 (12/02/2015) released [release notes](http://goo.gl/NGSVlR) [![](https://api.bintray.com/packages/lukepinnerau/generic/gdal-calculations/images/download.svg)](http://goo.gl/MsMXj4)

### Notes ###
If extents/cellsizes/coordinate systems differ, the output extent/cellsize will be the MINOF/MAXOF of input datasets, while the output coordinate system will be that of the leftmost Dataset in the expression unless Env.extent/Env.cellsize/Env.srs are specified.

gdal.Dataset and gdal.RasterBand and numpy.ndarray method and attribute calls are passed down to the underlying gdal.Dataset, gdal.RasterBand and ndarray objects.

If numexpr is installed, it can be used to evaluate your expressions as it is much faster.  However, numexpr expressions are very limited: tiled processing, on-the-fly reprojection, extent clipping/snapping, method/function calls and subscripting are not supported.

### Installation ###

  * Windows: Download and run the 32bit or 64bit installer as appropriate.
  * All: Download and extract the gdal-calculations-{version}.tar.gz and run `python setup.py install` with administrative or root privileges.

### Requirements ###

  * [Python](http://www.python.org) 2.6+
  * [GDAL](http://www.gdal.org) with python bindings
  * [numpy](http://www.numpy.org)