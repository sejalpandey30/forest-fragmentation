"""Open-data access (no accounts): Sentinel-2 L2A + Copernicus DEM via AWS Earth Search STAC,
ESA WorldCover and Hansen Global Forest Change via public HTTPS COGs. Heavy imports are lazy."""
import json
from pathlib import Path
import numpy as np

STAC_URL = "https://earth-search.aws.element84.com/v1"
BANDS = ["blue", "green", "red", "rededge1", "rededge2", "rededge3", "nir", "swir16", "swir22"]
OFFSET_FROM = np.datetime64("2022-01-25")   # processing baseline 04.00 introduced a -1000 offset
WC_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/{ver}/{year}/map/ESA_WorldCover_10m_{year}_{ver}_{tile}_Map.tif"
HANSEN_URL = "https://storage.googleapis.com/earthenginepartners-hansen/{v}/Hansen_{v}_{layer}_{tile}.tif"


def feature_names(cfg):
    n = BANDS + ["ndvi", "ndwi", "nbr", "ndmi", "ndvi_tstd", "ndvi_texture"]
    return n + (["elev", "slope"] if cfg.use_terrain else [])


def _nd(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        return (a - b) / (a + b)


def _local_std(a, size=3):
    from scipy import ndimage as ndi
    f = np.nan_to_num(a, nan=0.0)
    m = ndi.uniform_filter(f, size)
    return np.sqrt(np.clip(ndi.uniform_filter(f * f, size) - m * m, 0, None))


def _cache_path(cfg, year):
    tag = (f"{cfg.name}_{year}_{cfg.res}m_{cfg.season_start}_{cfg.season_end}_"
           f"c{cfg.max_cloud}_t{int(cfg.use_terrain)}").replace("-", "")
    return Path(cfg.cache_dir) / f"{tag}.tif"


def get_features(cfg, year):
    """(band, y, x) float32 DataArray of per-pixel features; cached on disk as GeoTIFF."""
    import rioxarray
    names, path = feature_names(cfg), _cache_path(cfg, year)
    if path.exists():
        da = rioxarray.open_rasterio(path, masked=True).load()
        if da.shape[0] == len(names):
            print(f"  {year}: loaded from cache")
            return da.assign_coords(band=names)
    da = _build_composite(cfg, year, names)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = da.assign_coords(band=np.arange(1, len(names) + 1)).rio.write_nodata(np.nan)
    tmp.rio.to_raster(path, dtype="float32", compress="deflate")
    return da


def _build_composite(cfg, year, names):
    import odc.stac, pystac_client, xarray as xr, rioxarray  # noqa: F401
    odc.stac.configure_rio(cloud_defaults=True, aws={"aws_unsigned": True})
    cat = pystac_client.Client.open(STAC_URL)
    items = list(cat.search(collections=["sentinel-2-l2a"], bbox=cfg.bbox,
                            datetime=f"{year}-{cfg.season_start}/{year}-{cfg.season_end}",
                            query={"eo:cloud_cover": {"lt": cfg.max_cloud}}).items())
    if not items:
        raise RuntimeError(f"No Sentinel-2 scenes for {year}; raise max_cloud or widen the season")
    print(f"  {year}: {len(items)} scenes -> downloading and compositing (several minutes)...")
    ds = odc.stac.load(items, bands=BANDS + ["scl"], bbox=cfg.bbox, crs=cfg.crs, resolution=cfg.res,
                       groupby="solar_day", resampling={"*": "bilinear", "scl": "nearest"})
    raw = ds[BANDS].to_array("band").astype("float32")
    raw = raw.where(raw > 0)
    off = xr.DataArray(np.where(ds.time.values >= OFFSET_FROM, 1000.0, 0.0), dims="time", coords={"time": ds.time})
    refl = ((raw - off) / 10000.0).clip(0, 1)
    good = ~ds["scl"].isin([0, 3, 8, 9, 10, 11])           # nodata, shadow, cloud, cirrus, snow
    refl = refl.where(good)
    med = refl.median("time", skipna=True)
    b = {n: med.sel(band=n).values for n in BANDS}
    ndvi_ts = _nd(refl.sel(band="nir", drop=True), refl.sel(band="red", drop=True))
    ndvi = _nd(b["nir"], b["red"])
    layers = [b[n] for n in BANDS] + [ndvi, _nd(b["green"], b["nir"]), _nd(b["nir"], b["swir22"]),
                                      _nd(b["nir"], b["swir16"]), ndvi_ts.std("time", skipna=True).values,
                                      _local_std(ndvi)]
    if cfg.use_terrain:
        layers += _terrain(cfg, cat, ds)
    arr = np.stack(layers).astype("float32")
    arr[:, ~np.isfinite(b["red"])] = np.nan
    arr[~np.isfinite(arr)] = np.nan
    return xr.DataArray(arr, dims=("band", "y", "x"), coords={"band": names, "y": med.y, "x": med.x}
                        ).rio.write_crs(cfg.crs)


def _terrain(cfg, cat, ds):
    import odc.stac
    items = list(cat.search(collections=["cop-dem-glo-30"], bbox=cfg.bbox).items())
    if not items:
        raise RuntimeError("No Copernicus DEM tiles found; set use_terrain: false")
    dem = odc.stac.load(items, bands=["data"], geobox=ds.odc.geobox, resampling="bilinear")
    elev = dem["data"].max("time").values.astype("float32")
    dzdy, dzdx = np.gradient(elev, cfg.res)
    return [elev, np.degrees(np.arctan(np.hypot(dzdx, dzdy))).astype("float32")]


def _tiles(bbox, step, fmt):
    lons = {int(np.floor(x / step) * step) for x in (bbox[0], bbox[2])}
    lats = {int(np.floor(y / step) * step) for y in (bbox[1], bbox[3])}
    return [fmt(la, lo) for la in sorted(lats) for lo in sorted(lons)]


def _open_match(urls, bbox, template, resampling):
    import rioxarray
    from rioxarray.merge import merge_arrays
    pad, parts = 0.01, []
    for u in urls:
        a = rioxarray.open_rasterio(u).squeeze("band", drop=True)
        parts.append(a.rio.clip_box(bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad))
    a = parts[0] if len(parts) == 1 else merge_arrays(parts)
    return a.rio.reproject_match(template, resampling=resampling).values


def worldcover(cfg, template, year=2021):
    from rasterio.enums import Resampling
    ver = {2020: "v100", 2021: "v200"}[year]
    urls = [WC_URL.format(ver=ver, year=year, tile=t)
            for t in _tiles(cfg.bbox, 3, lambda la, lo: f"N{la:02d}E{lo:03d}")]
    return _open_match(urls, cfg.bbox, template, Resampling.mode)


def hansen_layer(cfg, template, layer):
    from rasterio.enums import Resampling
    tiles = _tiles(cfg.bbox, 10, lambda la, lo: f"{la + 10:02d}N_{lo:03d}E")
    urls = [HANSEN_URL.format(v=cfg.hansen_version, layer=layer, tile=t) for t in tiles]
    return _open_match(urls, cfg.bbox, template, Resampling.nearest)


def load_extra_labels(path, template, crs):
    """Rasterise hand-drawn GeoJSON polygons (property 'class': 1 forest / 0 non-forest)."""
    import rasterio.features
    from rasterio.warp import transform_geom
    gj = json.load(open(path))
    shapes = [(transform_geom("EPSG:4326", crs, f["geometry"]), int(f["properties"]["class"]))
              for f in gj["features"]]
    return rasterio.features.rasterize(shapes, out_shape=template.shape, transform=template.rio.transform(),
                                       fill=-1, dtype="int16")
