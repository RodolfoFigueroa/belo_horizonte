import ee
import numpy as np


def get_collection_transforms(col: ee.ImageCollection) -> dict:
    crss = (
        col.map(lambda img: img.set("crs", img.projection().crs()))
        .aggregate_array("crs")
        .getInfo()
    )
    transforms = (
        col.map(lambda img: img.set("transform", img.projection().transform()))
        .aggregate_array("transform")
        .getInfo()
    )
    return {"crs": set(crss), "transforms": set(transforms)}


def clamp_bounds(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    *,
    scale: float,
) -> tuple[int, int, int, int]:
    return (
        int(np.floor(xmin / scale) * scale),
        int(np.floor(ymin / scale) * scale),
        int(np.ceil(xmax / scale) * scale),
        int(np.ceil(ymax / scale) * scale),
    )
