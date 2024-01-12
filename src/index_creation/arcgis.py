import logging
from functools import lru_cache
from pathlib import Path
import pkgutil
from tempfile import gettempdir
from typing import Union, List

from .. import config
from ..stats import get_simpsons_diversity_index

__all__ = [
    "add_simpsons_diversity_index_feature_class",
    "add_preconfigured_simpsons_diversity_index_feature_class",
]

# provide variable indicating if arcpy is available
has_arcpy: bool = pkgutil.find_loader("arcpy") is not None


@lru_cache(16)
def get_temp_gdb() -> Path:
    # late import
    import arcpy

    # ensure can clobber previous data
    arcpy.env.overwriteOutput = True

    # create a temporary file geodatabase to store data
    gdb = arcpy.management.CreateFileGDB(
        out_folder_path=gettempdir(), out_name="tmpfgdb.gdb"
    )[0]

    # convert the path to a Path object instance
    gdb_pth = Path(gdb)

    return gdb_pth


def add_simpsons_diversity_index_feature_class(
    data: Union[str, Path, "arcpy._mp.Layer"],
    input_fields: List[str],
    simpson_diversity_index_field: str = "simpson_diversity_index",
) -> Path:
    """
    Add a new column with Simpson's Diversity Index calculated from existing columns already existing in the dataset.

    Args:
        data: Feature Class to use as input for calculating Simpson's Diversity Index.
        input_fields: Scalar fields (columns) in the input data to use for calculating the index.
        simpson_diversity_index_field: Field to add to the Feature Class with Simpson's Diversity Index. The default is
            ``simpson_diversity_index``.

    ..note ::

        If the output column already exists in the Feature Class, this function will throw an error to avoid overwriting
        existing data.
    """
    # ensure arcpy is available
    if not has_arcpy:
        raise EnvironmentError(
            "ArcPy is required to execute the add_simpsons_diversity_index_feature_class function."
        )
    else:
        import arcpy

    # ensure, if a path is provided, it is converted to a string for arcpy functions
    data = str(data) if isinstance(data, Path) else data

    # get a list of field names
    obs_flds = [f.name for f in arcpy.ListFields(data)]

    # check to ensure the column to be added, does not already exist
    if simpson_diversity_index_field in obs_flds:
        raise ValueError(
            f"It appears the field to be added for the Simpson's Diversity Index, "
            f"{simpson_diversity_index_field}, already exists in the Feature Class attribute table."
        )

    # ensure the source fields exist in the feature class
    missing_cols = [c for c in input_fields if c not in obs_flds]
    if len(missing_cols):
        raise ValueError(
            f"Cannot locate all input_fields. Not detecting the following fields in the Feature Class - "
            f"{missing_cols}."
        )

    # add a new field for the new index
    arcpy.management.AddField(
        data, field_name=simpson_diversity_index_field, field_type="FLOAT"
    )

    # create an update cursor for index calculation
    with arcpy.da.UpdateCursor(
        data, input_fields + [simpson_diversity_index_field]
    ) as update_cursor:

        # iterate the rows
        for r in update_cursor:

            # using just the values from the input fields, calculate Simpson's Diversity Index
            idx = get_simpsons_diversity_index(r[:-1])

            # populate the value for Simpson's Diversity Index
            r[-1] = idx

            # write the update
            update_cursor.updateRow(r)

    return data


def add_preconfigured_simpsons_diversity_index_feature_class(
    input_features: Union[str, Path],
    index_name: str,
    include_enrich_fields: bool = False,
) -> Union[Path, str]:
    """
    Add a preconfigured Simpson's Diversity Index to a Feature Class using one of the preconfigured indices.

    Currently, the preconfigured indices include:

    - ``income``
    - ``home_value``
    - ``wealth``
    - ``age``
    - ``home_age``
    - ``employment_diversity``
    - ``housing_diversity``

    Args:
        input_features: Feature Class to use as input for calculating Simpson's Diversity Index.
        index_name: Name of one of the available preconfigured indices.
        include_enrich_fields: Whether to leave the source fields for calculating the index. These fields are
            added using enrichment. The default is false, which removes these fields added through enrichment.
    """
    # late import
    import arcpy
    from arcgis.geoenrichment._business_analyst import Country

    # get a temp geodatabase
    tmp_gdb = get_temp_gdb()

    # ensure the features, if paths, are converted to strings for the Geoprocessing tools
    if isinstance(input_features, Path):
        input_features = str(input_features)

    # ensure the requested index is available
    idx_names = config.meta_variables.keys()
    if index_name not in idx_names:
        raise ValueError(
            f'Unfortunately, your requested index, "{index_name}," is not available. Please select '
            f"from {idx_names}"
        )

    # get the enrich variable names from the config
    var_name_lst = config.meta_variables[index_name]

    # create the country object for looking up values
    cntry = Country("USA", "local")

    # get the enrich strings and output field names to use
    ev_df = cntry.enrich_variables[cntry.enrich_variables["name"].isin(var_name_lst)]
    enrich_str_lst = list(ev_df["enrich_name"])
    enrich_fld_lst = list(ev_df["enrich_field_name"])
    enrich_str = ";".join(enrich_str_lst)

    # enrich the input data and save to a temporary output feature class
    enrich_fc = arcpy.ba.EnrichLayer(
        in_features=input_features,
        out_feature_class=str(tmp_gdb / "temp_enrich"),
        variables=enrich_str,
    )[0]

    # add the simpson index to the output fields
    simpson_field_name = f"simpson_diversity_index_{index_name}"

    # add the simpsons diversity index field onto the temp feature class
    add_simpsons_diversity_index_feature_class(
        enrich_fc, enrich_fld_lst, simpson_field_name
    )

    # create a list of fields to add...taking into account if adding the enrich fields or not
    if include_enrich_fields:
        fld_nm_add_lst = enrich_fld_lst + [simpson_field_name]
    else:
        fld_nm_add_lst = [simpson_field_name]
    fld_add_lst = [f for f in arcpy.ListFields(enrich_fc) if f.name in fld_nm_add_lst]

    # add the fields to the original feature class
    for fld in fld_add_lst:
        arcpy.management.AddField(
            in_table=input_features,
            field_name=fld.name,
            field_type=fld.type,
            field_precision=fld.precision,
            field_scale=fld.scale,
            field_length=fld.length,
            field_alias=fld.aliasName,
        )

    # create a comprehension generator to get the values from the enriched data to add to the original feature class
    enrich_rows = (r for r in arcpy.da.SearchCursor(enrich_fc, fld_nm_add_lst))

    # use an update cursor to update the values
    with arcpy.da.UpdateCursor(input_features, fld_nm_add_lst) as update_cur:

        # iterate the input rows
        for _ in update_cur:

            # get the next value from the enriched data
            enrich_row = next(enrich_rows)

            # push the update to the input table
            update_cur.updateRow(enrich_row)

    # provide status feedback
    logging.info(
        f"Calculated Simson's Diversity Index named {simpson_field_name} using {var_name_lst}"
    )

    return input_features
