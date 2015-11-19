# Type conversion helper functions #

The following type conversion functions can be imported from the gdal\_calculations package or used in the gdal\_calculate script.  They return a gdal\_calculations.Dataset object.  They don't convert scalar values.
```
from gdal_calculations import *
Byte(dataset_or_band)
UInt16(dataset_or_band)
Int16(dataset_or_band)
UInt32(dataset_or_band)
Int32(dataset_or_band)
Float32(dataset_or_band)
Float64(dataset_or_band)
```
<pre>gdal_calculate --calc='Float32(araster)' --araster='int.tif' --outfile='float.tif'</pre>