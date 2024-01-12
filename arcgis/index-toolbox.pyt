# -*- coding: utf-8 -*-

from pathlib import Path
import pkgutil
import sys

import arcpy

if pkgutil.find_loader('index_creation') is not None:
    from index_creation import arcgis, config

elif (Path(__file__).parent.parent / 'src' / 'index_creation').exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    from index_creation import arcgis, config

else:
    raise EnvironmentError('Cannot locate index_creation pacakge. Please ensure it is either installed, or this '
                           'toolbox is not moved from the downloaded repo.')


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Index Toolbox"
        self.alias = "index_toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [AddSimpsonsDiversityIndex, AddPreconfiguredSimpsonsDiversityIndex]


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
        arcgis.add_simpsons_diversity_index_feature_class(features, fld_lst, index_field)

        return


class AddPreconfiguredSimpsonsDiversityIndex(object):
    def __init__(self):
        """Calculate Simpson's Diversity Index from existing fields."""
        self.label = "Add Preconfigured Simpson's Diversity Index"
        self.description = "Enrich, calculate and Add Simpson's Diversity Index using existing fields."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        features = arcpy.Parameter(
            displayName='Features',
            name='features',
            datatype='GPFeatureLayer',
            parameterType='Optional',
            direction='Input'
        )

        index_name = arcpy.Parameter(
            displayName='Index Name',
            name='index_name',
            datatype='GPString',
            parameterType='Required',
            direction='Input'
        )
        index_name.filter.type = 'ValueList'
        index_name.filter.list = list(config.meta_variables.keys())
        index_name.value = index_name.filter.list[0]

        all_indices = arcpy.Parameter(
            displayName='Add All Indices',
            name='all_indices',
            datatype='GPBoolean',
            parameterType='Optional',
            direction='Input',
            category='Advanced'
        )

        keep_enrich_fields = arcpy.Parameter(
            displayName='Keep Enrich Fields',
            name='keep_enrich_fields',
            datatype='GPBoolean',
            parameterType='Required',
            direction='Input',
            category='Advanced'
        )
        keep_enrich_fields.value = False

        params = [features, index_name, all_indices, keep_enrich_fields]
        return params

    def updateParameters(self, parameters):

        [_, index_name, all_indices, _] = parameters

        # if all indices are modified
        if all_indices.altered:

            # if the value is true, disable the single value
            if all_indices.value:
                index_name.enabled = False

            # if the value is false, enable the single value
            else:
                index_name.enabled = True

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        features = parameters[0].value
        index_name = parameters[1].valueAsText
        all_indices = parameters[2].value
        keep_enrich_fields = parameters[3].value

        # if adding all values, create a list of indices to add
        if all_indices:
            idx_lst = config.meta_variables.keys()
        else:
            idx_lst = [index_name]

        # add the preconfigured simpsons diversity index to the input features
        for idx in idx_lst:
            arcgis.add_preconfigured_simpsons_diversity_index_feature_class(features, idx, keep_enrich_fields)

        return
