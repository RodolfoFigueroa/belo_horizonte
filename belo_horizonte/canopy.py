import ee
import ee.data
import pandas as pd


def get_canopy_area(
    img_canopy: ee.image.Image,
    regions: ee.featurecollection.FeatureCollection,
    *,
    index_col: str,
) -> pd.DataFrame:
    res = (
        ee.data.computeFeatures(
            {
                "expression": ee.image.Image.pixelArea()
                .addBands(img_canopy)
                .reduceRegions(
                    regions,
                    ee.reducer.Reducer.sum().group(groupField=1),
                    scale=2,
                ),
                "fileFormat": "GEOPANDAS_GEODATAFRAME",
            },
        )
        .set_index(index_col)
        .set_crs("EPSG:4326")
    )

    group_cols = [
        pd.DataFrame(group).set_index("group")["sum"].rename(idx)
        for idx, group in res["groups"].items()
    ]

    return pd.concat(group_cols, axis=1).transpose()
