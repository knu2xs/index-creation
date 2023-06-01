__title__ = 'index-creation'
__version__ = '0.0.0'
__author__ = 'Joel McCune'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2023 by Joel McCune'

__all__ = ['add_simpsons_diversity_index_feature_class', 'get_simpsons_diversity_index']

from typing import Union, List, Iterable
from pathlib import Path
import pkgutil

# provide variable indicating if arcpy is available
has_arcpy: bool = pkgutil.find_loader('arcpy') is not None


def get_percent_of_n(n: Union[int, float], N: Union[int, float]) -> float:
    p_n = 0.0 if n == 0 else float(n) / N
    return p_n


def get_simpsons_diversity_index(data: Iterable[Union[int, float]]) -> float:
    """
    Get the Simpson's Diversity Index based on input scalar values.

    Args:
        data: Iterable of scalar values as either integers or floating point numbers.

    .. code-block:: python

        # assuming all columns are to be used for the diversity index
        df['simpsons_diversity_index'] = df.apply(lambda r:  get_simpsons_diversity_index(r), axis=1)

    """
    # get the total population
    N = sum(data)

    # calculate simpson's diversity index using the helper function above
    sd_idx = sum(get_percent_of_n(n, N)**2 for n in data if n != 0)

    return sd_idx


def add_simpsons_diversity_index_feature_class(
        data: Union[str, Path, 'arcpy._mp.Layer'],
        input_fields: List[str],
        simpson_diversity_index_field: str = 'simpson_diversity_index'
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
        raise EnvironmentError('ArcPy is required to execute the add_simpsons_diversity_index_feature_class function.')
    else:
        import arcpy

    # ensure, if a path is provided, it is converted to a string for arcpy functions
    data = str(data) if isinstance(data, Path) else data

    # get a list of field names
    obs_flds = [f.name for f in arcpy.ListFields(data)]

    # check to ensure the column to be added, does not already exist
    if simpson_diversity_index_field in obs_flds:
        raise ValueError(f"It appears the field to be added for the Simpson's Diversity Index, "
                         f"{simpson_diversity_index_field}, already exists in the Feature Class attribute table.")

    # ensure the source fields exist in the feature class
    missing_cols = [c for c in input_fields if c not in obs_flds]
    if len(missing_cols):
        raise ValueError(f'Cannot locate all input_fields. Not detecting the following fields in the Feature Class - '
                         f'{missing_cols}.')

    # add a new field for the new index
    arcpy.management.AddField(data, field_name=simpson_diversity_index_field, field_type='FLOAT')

    # create an update cursor for index calculation
    with arcpy.da.UpdateCursor(data, input_fields + [simpson_diversity_index_field]) as update_cursor:

        # iterate the rows
        for r in update_cursor:

            # using just the values from the input fields, calculate Simpson's Diversity Index
            idx = get_simpsons_diversity_index(r[:-1])

            # populate the value for Simpson's Diversity Index
            r[-1] = idx

            # write the update
            update_cursor.updateRow(r)

    return data
