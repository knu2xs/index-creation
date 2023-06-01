# -*- coding: utf-8 -*-

from pathlib import Path
import pkgutil
import sys

import arcpy

if pkgutil.find_loader('index_creation') is not None:
    from index_creation import add_simpsons_diversity_index_feature_class

elif (Path(__file__).parent.parent / 'src' / 'index_creation').exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    from index_creation import add_simpsons_diversity_index_feature_class

else:
    raise EnvironmentError('Cannot locate index_creation pacakge. Please ensure it is either installed, or this toolbox is'
                           'not moved from the downloaded repo.')


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Index Toolbox"
        self.alias = "index_toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [SimpsonsDiversityIndex]


class SimpsonsDiversityIndex(object):
    def __init__(self):
        """Calculate Simpson's Diversity Index from existing fields."""
        self.label = "Calculate Simpson's Diversity Index"
        self.description = "Calculate Simpson's Diversity Index from existing fields"
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
