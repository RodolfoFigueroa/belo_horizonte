import os
from pathlib import Path

import ee
import geemap
import geopandas as gpd


def load_bounds(data_path: os.PathLike) -> ee.geometry.Geometry:
    data_path = Path(data_path)

    df_bounds = (
        gpd.read_file(
            data_path
            / "Areas de intervencion"
            / "Mancha Urbana"
            / "MANCHA_URBANA_2018",
        )
        .pipe(lambda df: df.to_crs(df.estimate_utm_crs()))
        .explode()
        .assign(area=lambda df: df["geometry"].area)
        .sort_values("area", ascending=False)
        .head(1)
        .assign(geometry=lambda df: df["geometry"].simplify(10))
        .filter(["geometry"])
        .to_crs("EPSG:4326")
    )

    return geemap.geopandas_to_ee(df_bounds).first().geometry()  # pyright: ignore[reportAttributeAccessIssue]
