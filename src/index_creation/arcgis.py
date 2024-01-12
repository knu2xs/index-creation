import logging
from functools import lru_cache
from pathlib import Path
import pkgutil
from tempfile import gettempdir
from typing import Union, List

from . import config
from .stats import get_simpsons_diversity_index

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
    Add a preconfigured Simpson's Diversity Index to a Feature Class using one of the preconfigured indices. These
    preconfigured demographic indices are calculated using pre-selected variables from the ArcGIS Business Analyst
    United States dataset.

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

    The contributing variables from Business Analyst for each respective index are detailed below.

    Income
    ^^^^^^^

    .. list-table::
        :widths: 10 53
        :header-rows: 1

        * - variable_name
          - variable_alias
        * - HINC0_CY
          - 2022 HH Income <$15000
        * - HINC15_CY
          - 2022 HH Income $15000-24999
        * - HINC25_CY
          - 2022 HH Income $25000-34999
        * - HINC35_CY
          - 2022 HH Income $35000-49999
        * - HINC50_CY
          - 2022 HH Income $50000-74999
        * - HINC75_CY
          - 2022 HH Income $75000-99999
        * - HINC100_CY
          - 2022 HH Income $100000-149999
        * - HINC150_CY
          - 2022 HH Income $150000-199999
        * - HINC200_CY
          - 2022 HH Income $200000+

    Home Value
    ^^^^^^^^^^

    .. list-table::
        :widths: 10 53
        :header-rows: 1

        * - variable_name
          - variable_alias
        * - VAL0_CY
          - 2022 Home Value <$50000
        * - VAL50K_CY
          - 2022 Home Value $50K-99999
        * - VAL100K_CY
          - 2022 Home Value $100K-149999
        * - VAL150K_CY
          - 2022 Home Value $150K-199999
        * - VAL200K_CY
          - 2022 Home Value $200K-249999
        * - VAL250K_CY
          - 2022 Home Value $250K-299999
        * - VAL300K_CY
          - 2022 Home Value $300K-399999
        * - VAL400K_CY
          - 2022 Home Value $400K-499999
        * - VAL500K_CY
          - 2022 Home Value $500K-749999
        * - VAL750K_CY
          - 2022 Home Value $750K-999999
        * - VAL1M_CY
          - 2022 Home Value $1 Million-1499999
        * - VAL2M_CY
          - 2022 Home Value $2 Million+

    Wealth
    ^^^^^^^

    .. list-table::
        :widths: 10 53
        :header-rows: 1

        * - variable_name
          - variable_alias
        * - NW0_CY
          - 2022 Net Worth <$15000
        * - NW15_CY
          - 2022 Net Worth $15000-$34999
        * - NW35_CY
          - 2022 Net Worth $35000-$49999
        * - NW50_CY
          - 2022 Net Worth $50000-$74999
        * - NW75_CY
          - 2022 Net Worth $75000-$99999
        * - NW100_CY
          - 2022 Net Worth $100000-$149999
        * - NW150_CY
          - 2022 Net Worth $150000-$249999
        * - NW250_CY
          - 2022 Net Worth $250000-$499999
        * - NW500_CY
          - 2022 Net Worth $500000-$999999

    Age
    ^^^^

    .. list-table::
        :widths: 10 53
        :header-rows: 1

        * - variable_name
          - variable_alias
        * - POP0_CY
          - 2022 Population Age 0-4
        * - POP5_CY
          - 2022 Population Age 5-9
        * - POP10_CY
          - 2022 Population Age 10-14
        * - POP15_CY
          - 2022 Population Age 15-19
        * - POP20_CY
          - 2022 Population Age 20-24
        * - POP25_CY
          - 2022 Population Age 25-29
        * - POP30_CY
          - 2022 Population Age 30-34
        * - POP35_CY
          - 2022 Population Age 35-39
        * - POP40_CY
          - 2022 Population Age 40-44
        * - POP45_CY
          - 2022 Population Age 45-49
        * - POP50_CY
          - 2022 Population Age 50-54
        * - POP55_CY
          - 2022 Population Age 55-59
        * - POP60_CY
          - 2022 Population Age 60-64
        * - POP65_CY
          - 2022 Population Age 65-69
        * - POP70_CY
          - 2022 Population Age 70-74
        * - POP75_CY
          - 2022 Population Age 75-79
        * - POP80_CY
          - 2022 Population Age 80-84
        * - POP85_CY
          - 2022 Population Age 85+

    Home Age
    ^^^^^^^^

    .. list-table::
        :widths: 10 53
        :header-rows: 1

        * - variable_name
          - variable_alias
        * - ACSBLT2014
          - 2020 HUs/Year Built: 2014/Later (ACS 5-Yr)
        * - ACSBLT2010
          - 2020 HUs/Year Built: 2010-2013 (ACS 5-Yr)
        * - ACSBLT2000
          - 2020 HUs/Year Built: 2000-2009 (ACS 5-Yr)
        * - ACSBLT1990
          - 2020 HUs/Year Built: 1990-1999 (ACS 5-Yr)
        * - ACSBLT1980
          - 2020 HUs/Year Built: 1980-1989 (ACS 5-Yr)
        * - ACSBLT1970
          - 2020 HUs/Year Built: 1970-1979 (ACS 5-Yr)
        * - ACSBLT1960
          - 2020 HUs/Year Built: 1960-1969 (ACS 5-Yr)
        * - ACSBLT1950
          - 2020 HUs/Year Built: 1950-1959 (ACS 5-Yr)
        * - ACSBLT1940
          - 2020 HUs/Year Built: 1940-1949 (ACS 5-Yr)
        * - ACSBLT1939
          - 2020 HUs/Year Built: 1939 or Earlier (ACS 5-Yr)

    Employment Diversity
    ^^^^^^^^^^^^^^^^^^^^^

    .. list-table::
        :widths: 10 53
        :header-rows: 1

        * - variable_name
          - variable_alias
        * - INDAGRI_CY
          - 2022 Industry: Agriculture
        * - INDMIN_CY
          - 2022 Industry: Mining
        * - INDCONS_CY
          - 2022 Industry: Construction
        * - INDMANU_CY
          - 2022 Industry: Manufacturing
        * - INDWHTR_CY
          - 2022 Industry: Wholesale Trade
        * - INDRTTR_CY
          - 2022 Industry: Retail Trade
        * - INDTRAN_CY
          - 2022 Industry: Transportation
        * - INDUTIL_CY
          - 2022 Industry: Utilities
        * - INDINFO_CY
          - 2022 Industry: Information
        * - INDFIN_CY
          - 2022 Industry: Finance/Insurance
        * - INDRE_CY
          - 2022 Industry: Real Estate
        * - INDTECH_CY
          - 2022 Industry: Professional/Tech Svcs
        * - INDMGMT_CY
          - 2022 Industry: Management
        * - INDADMN_CY
          - 2022 Industry: Admin/Waste Mgmt
        * - INDEDUC_CY
          - 2022 Industry: Educational Services
        * - INDHLTH_CY
          - 2022 Industry: Health Care
        * - INDARTS_CY
          - 2022 Industry: Arts/Entertainment/Rec
        * - INDFOOD_CY
          - 2022 Industry: Accommodation/Food Svcs
        * - INDOTSV_CY
          - 2022 Industry: Other Services
        * - INDPUBL_CY
          - 2022 Industry: Public Administration

    Housing Diversity
    ^^^^^^^^^^^^^^^^^^

    .. list-table::
        :widths: 10 53
        :header-rows: 1

        * - variable_name
          - variable_alias
        * - ACSUNT1DET
          - 2020 Housing: 1 Detached Unit in Structure (ACS 5-Yr)
        * - ACSUNT1ATT
          - 2020 Housing: 1 Attached Unit in Structure (ACS 5-Yr)
        * - ACSUNT2
          - 2020 Housing: 2 Units in Structure (ACS 5-Yr)
        * - ACSUNT3
          - 2020 Housing: 3 or 4 Units in Structure (ACS 5-Yr)
        * - ACSUNT5
          - 2020 Housing: 5 to 9 Units in Structure (ACS 5-Yr)
        * - ACSUNT10
          - 2020 Housing: 10 to 19 Units in Structure (ACS 5-Yr)
        * - ACSUNT20
          - 2020 Housing: 20 to 49 Units in Structure (ACS 5-Yr)
        * - ACSUNT50UP
          - 2020 Housing: 50+ Units in Structure (ACS 5-Yr)
        * - ACSUNTMOB
          - 2020 Housing: Mobile Homes (ACS 5-Yr)
        * - ACSUNTOTH
          - 2020 Housing: Boat/RV/Van/etc. (ACS 5-Yr)
        * - ACSTOTHU
          - 2020 Total Housing Units (ACS 5-Yr)
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
