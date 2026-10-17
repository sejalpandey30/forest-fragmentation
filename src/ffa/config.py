"""Run configuration (YAML-backed dataclass)."""
from dataclasses import dataclass, field, asdict, fields
from typing import List, Optional
import yaml


@dataclass
class Config:
    name: str = "valparai"
    bbox: List[float] = field(default_factory=lambda: [76.85, 10.25, 77.05, 10.45])  # lon/lat W,S,E,N
    crs: str = "EPSG:32643"           # metric UTM zone covering the AOI
    res: int = 30                     # pixel size (m)
    start_year: int = 2020
    end_year: int = 2025
    train_year: int = 2021            # year of the WorldCover v200 labels
    # imagery
    season_start: str = "01-01"       # dry-season window (fewer monsoon clouds)
    season_end: str = "04-30"
    max_cloud: int = 40               # scene-level cloud cover limit (%)
    use_terrain: bool = True          # Copernicus DEM elevation + slope
    # labels
    label_erode_px: int = 1           # drop mixed pixels at class borders
    forest_ndvi_floor: float = 0.35   # drop 'forest' labels that are bare/cleared in the image
    extra_labels: Optional[str] = None  # GeoJSON of hand-drawn polygons, property "class": 1 forest / 0 non-forest
    # model
    n_trees: int = 200
    n_per_class: int = 40000
    cv_block_km: float = 2.0          # spatial block size for cross-validation
    cv_folds: int = 5
    seed: int = 42
    # post-processing
    threshold: float = 0.5
    spatial_filter: int = 3           # majority-style smoothing window (pixels, 1 = off)
    temporal_window: int = 1          # median over neighbouring years (1 = off)
    min_patch_ha: float = 1.0
    hole_ha: float = 0.5
    edge_depth_m: float = 100.0       # edge-effect depth for core area
    # validation
    validate_worldcover_2020: bool = True
    validate_hansen: bool = True
    hansen_version: str = "GFC-2024-v1.12"
    # io
    out_dir: str = "outputs"
    cache_dir: str = "data/cache"


def load_config(path=None, **overrides):
    data = {}
    if path:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    data.update({k: v for k, v in overrides.items() if v is not None})
    valid = {f.name for f in fields(Config)}
    unknown = set(data) - valid
    if unknown:
        raise ValueError(f"Unknown config keys: {sorted(unknown)}")
    return Config(**data)


def to_dict(cfg):
    return asdict(cfg)
