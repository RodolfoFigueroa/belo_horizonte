import os
from pathlib import Path

import ee
import ee.data
import geemap
import geopandas as gpd
import pandas as pd
import rasterio as rio
import rasterio.sample as rio_sample


def sample_elevation(df_samples: gpd.GeoDataFrame, data_path: os.PathLike) -> pd.Series:
    data_path = Path(data_path)

    df_level = (
        gpd.read_file(
            data_path
            / "Areas de intervencion"
            / "Altimetria_MDT"
            / "CURVA_DE_NIVEL_5M",
        )
        .pipe(lambda df: df.to_crs(df_samples.crs))
        .filter(["COTA", "geometry"])
        .rename(columns={"COTA": "elevation"})
    )

    out = (
        df_samples[["geometry"]]
        .sjoin_nearest(df_level)
        .reset_index(names="index")
        .drop_duplicates(subset="index")
        .set_index("index")["elevation"]
    )

    if not isinstance(out, pd.Series):
        err = "Expected output to be a pandas Series."
        raise TypeError(err)

    return out


def sample_slope(df_samples: gpd.GeoDataFrame, data_path: os.PathLike) -> pd.Series:
    data_path = Path(data_path)

    with rio.open(
        data_path / "Ide_bhgeo_mosaico-declividade_curva_nivel_2015.tif",
    ) as ds:
        coords = [(geom.x, geom.y) for geom in df_samples.geometry]
        slope_values = list(rio_sample.sample_gen(ds, coords))
        return pd.Series(
            [val[0] for val in slope_values],
            index=df_samples.index,
            name="slope",
        )


def sample_lights(
    col_samples: ee.featurecollection.FeatureCollection,
    bounds: ee.geometry.Geometry,
    *,
    index_col: str,
) -> pd.Series:
    img_lights = (
        ee.imagecollection.ImageCollection(
            "projects/sat-io/open-datasets/srunet-npp-viirs-ntl",
        )
        .filterBounds(bounds)
        .filter(ee.filter.Filter.eq("id_no", "SRUNet_NPP_VIIRS_V2_Like_2020"))
        .first()
    )

    return (
        ee.data.computeFeatures(
            {
                "expression": img_lights.sampleRegions(col_samples, scale=500),
                "fileFormat": "GEOPANDAS_GEODATAFRAME",
            },
        )
        .set_index(index_col)["b1"]
        .rename("lights")
    )


def sample_lots(
    df_samples: gpd.GeoDataFrame,
    data_path: os.PathLike,
    *,
    buffer: float = 50,
) -> pd.DataFrame:
    data_path = Path(data_path)

    crs = df_samples.crs
    if crs is None:
        err = "Input GeoDataFrame must have a defined CRS."
        raise ValueError(err)

    df_lots = (
        gpd.read_file(
            data_path
            / "Areas de intervencion"
            / "Uso y Ocupacion de Suelo"
            / "TIPOLOGIA_USO_OCUPACAO_LOTE_2022",
        )
        .to_crs(crs)
        .query("TIPOLOGIA_ != 'SEM INFORMACAO'")
    )

    return (
        df_samples[["geometry"]]
        .assign(
            geometry=lambda df: df["geometry"].buffer(buffer),
            orig_area=lambda df: df["geometry"].area,
        )
        .reset_index(names="index")
        .overlay(df_lots[["TIPOLOGIA_", "geometry"]], how="intersection")
        .assign(area_frac=lambda df: df["geometry"].area / df["orig_area"])
        .groupby(["index", "TIPOLOGIA_"])["area_frac"]
        .sum()
        .unstack()
        .fillna(0)
        .pipe(lambda df: df.div(df.sum(axis=1), axis=0))
        .rename(
            columns={
                "LOTE VAGO": "landuse_vacant_lot",
                "MISTO": "landuse_mixed_use",
                "NAO RESIDENCIAL": "landuse_non_residential",
                "PARQUE": "landuse_park",
                "RESIDENCIAL": "landuse_residential",
            },
        )
    )


def generate_full_samples(
    sample_points: gpd.GeoSeries,
    *,
    data_path: os.PathLike,
    bounds: ee.geometry.Geometry,
) -> gpd.GeoDataFrame:
    data_path = Path(data_path)

    df_samples = sample_points.to_frame().rename_axis("index")
    col_samples = geemap.geopandas_to_ee(df_samples.to_crs("EPSG:4326"))

    if not isinstance(col_samples, ee.featurecollection.FeatureCollection):
        err = "Expected output to be an Earth Engine FeatureCollection."
        raise TypeError(err)

    df_samples = df_samples.assign(
        elevation=lambda df: sample_elevation(df, data_path),
        slope=lambda df: sample_slope(df, data_path),
        lights=sample_lights(col_samples, bounds, index_col="index"),
    )

    out = df_samples.join(sample_lots(df_samples, data_path))

    if not isinstance(out, gpd.GeoDataFrame):
        err = "Expected output to be a GeoDataFrame."
        raise TypeError(err)

    return out
