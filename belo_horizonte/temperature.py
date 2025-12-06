import ee


def extract_bits(img: ee.image.Image, from_bit: int, to_bit: int) -> ee.image.Image:
    mask_size = ee.ee_number.Number(1).add(to_bit).subtract(from_bit)
    mask = ee.ee_number.Number(1).leftShift(mask_size).subtract(1)
    return img.rightShift(from_bit).bitwiseAnd(mask)


def mask_clouds(img: ee.image.Image) -> ee.image.Image:
    qa = img.select("QA_PIXEL")
    mask = extract_bits(qa, 1, 4).eq(0)
    return img.updateMask(mask)


def get_lst(
    col_name: str,
    *,
    year: int,
    temp_band: str,
    qa_band: str,
    bounds: ee.geometry.Geometry,
) -> ee.image.Image:
    col = (
        ee.imagecollection.ImageCollection(col_name)
        .filterBounds(bounds)
        .filterDate(f"{year}-12-21", f"{year + 1}-03-21")
        .select([temp_band, qa_band])
    )

    return (
        col.map(mask_clouds)
        .select(temp_band)
        .map(lambda img: img.multiply(0.00341802).add(149 - 273.15))
        .mean()
        .rename(f"b{year}")
    )
