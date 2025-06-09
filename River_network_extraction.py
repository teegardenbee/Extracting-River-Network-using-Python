import rasterio
import numpy as np
import geopandas as gpd
from pysheds.grid import Grid
from shapely.geometry import shape
from rasterio.features import shapes


# File paths
point_shp_path = "Path"
dem_path = "Path"

grid = Grid.from_raster(dem_path)
dem = grid.read_raster(dem_path)

# Fill pits in DEM
pit_filled_dem = grid.fill_pits(dem)

# Fill depressions in DEM
flooded_dem = grid.fill_depressions(pit_filled_dem)

# Resolve flats in DEM
inflated_dem = grid.resolve_flats(flooded_dem)

# Specify directional mapping
dirmap = (1, 2, 4, 8, 16, 32, 64, 128)

# Compute flow directions
nodata_value = np.int16(-1)
fdir = grid.flowdir(inflated_dem, dirmap=dirmap, nodata_out = nodata_value)

# Calculate flow accumulation
nodata_value = np.int16(-1)
acc = grid.accumulation(fdir, dirmap=dirmap, nodata_out = nodata_value)

# Open the DEM to get metadata
with rasterio.open(dem_path) as dem_src:
    dem_meta = dem_src.meta.copy()
    dem_shape = dem_src.shape

# Update metadata with your accumulation array dtype
dem_meta.update({
    "dtype": acc.dtype,  # dtype of your accumulation array
    "count": 1
})

# Save the accumulation raster
with rasterio.open("Path for saving flow accumulation raster", "w", **dem_meta) as dst:
    dst.write(acc, 1)

acc_path = "Path for saving flow accumulation raster"

with rasterio.open(acc_path) as src:
    acc = src.read(1)
    transform = src.transform
    crs = src.crs
threshold = 30000  # adjust based on your DEM resolution and area
streams = (acc > threshold).astype(np.uint8)


shapes_generator = shapes(streams, mask=streams.astype(bool), transform=transform)
stream_geoms = [
    {"geometry": shape(geom), "properties": {"value": value}}
    for geom, value in shapes_generator if value == 1
]

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(stream_geoms)
gdf.crs = crs
gdf = gdf.explode(index_parts=False)  # optional, if shapes are multipart

# Save to file
gdf.to_file('Path for output river network geojson file', driver='GeoJSON')