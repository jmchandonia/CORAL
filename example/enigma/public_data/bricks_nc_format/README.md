# NetCDF4 format files:

The files in this directory were made using a Jupyter notebook.  Each
Brick was loaded and then the underlying xarray Dataset object was
saved to NetCDF4 format.  This was complicated by the fact that the
library doesn't know how to serialize arbitrary Python objects.
Therefore, each Brick had to be fixed up by converting objects (mostly
Terms) into strings.  The "None" attributes also had to be removed
because they couldn't be serialized.

Here is sample code:
```
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import math
from coral.ontology import Term
from coral.brick import PropertyValue
from coral.dataprovider import DataProvider
dp = DataProvider()

def stringify(obj):
    return obj.__str__()
	
dp.genx_types.Brick.find( )
	
brick = dp.genx_types.Brick.load('Brick0000001')
xds = brick._Brick__xds
for k,v in xds.attrs.items():
    if isinstance(v,Term) or isinstance(v,PropertyValue):
        xds.attrs[k]=v.__str__()
for variable in xds.variables.values():
    for k,v in list(variable.attrs.items()):
        if isinstance(v,Term) or isinstance(v,PropertyValue):
            variable.attrs[k]=v.__str__()
        if v is None:
            del variable.attrs[k]
xds2 = xr.apply_ufunc(stringify, xds, vectorize=True, keep_attrs=True)
xds2.to_netcdf(path='generic_otu_id_zhou_100ws.nc')
```
