# -*- coding: utf-8 -*-
__title__ = 'simpson-index-toolbox'
__version__ = '0.1.0'
__author__ = 'Joel McCune'

from pathlib import Path

import arcpy

from typing import Union, Iterable, List


def get_percent_of_n(n: Union[int, float], N: Union[int, float]) -> float:
    p_n = 0.0 if n == 0 else float(n) / N
    return p_n


def get_simpsons_diversity_index(data: Iterable[Union[int, float]]) -> float:
    """
    Get the Gini-Simpson's Diversity Index based on input scalar values.

    Args:
        data: Iterable of scalar values as either integers or floating point numbers.

    .. code-block:: python

        # assuming all columns are to be used for the diversity index
        df['simpsons_diversity_index'] = df.apply(lambda r:  get_simpsons_diversity_index(r), axis=1)

    """
    # get the total population
    N = sum(data)

    # calculate simpson's diversity index using the helper function above
    sd_idx = 1 - (sum(get_percent_of_n(n, N)**2 for n in data if n != 0))

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


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Simpson Index Toolbox"
        self.alias = "simpson_index_toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [AddSimpsonsDiversityIndex]


class AddSimpsonsDiversityIndex(object):
    def __init__(self):
        """Calculate Simpson's Diversity Index from existing fields."""
        self.label = "Add Simpson's Diversity Index"
        self.description = "Calculate and Add Simpson's Diversity Index using existing fields."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        features = arcpy.Parameter(
            displayName='Features',
            name='features',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input'
        )

        input_fields = arcpy.Parameter(
            displayName='Input Fields',
            name='input_fields',
            datatype='Field',
            parameterType='Required',
            direction='Input',
            multiValue=True,
        )
        input_fields.parameterDependencies = [features.name]

        index_field = arcpy.Parameter(
            displayName='Simpson Diversity Index Field Name',
            name='index_field',
            datatype='GPString',
            parameterType='Required',
            direction='Input'
        )
        index_field.value = 'simpson_diversity_index'

        params = [features, input_fields, index_field]
        return params

    def execute(self, parameters, messages):
        """The source code of the tool."""
        features = parameters[0].value
        input_fields: arcpy.ValueTable = parameters[1].value
        index_field = parameters[2].valueAsText

        # get the list of fields from the parameter
        fld_lst = input_fields.exportToString().split(';')

        # add the simpsons diversity index to the input features
        add_simpsons_diversity_index_feature_class(features, fld_lst, index_field)

        return
