__title__ = "index-creation"
__version__ = "0.1.0"
__author__ = "Joel McCune"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2023 by Joel McCune"

"""
This package streamlines the creation of a Gini-Simpson Index with ArcGIS Feature Classes. The package
can be used standalone to automate data processing, and is the processing logic being used in the included
Python toolbox for use with ArcGIS Pro.
"""

__all__ = ["arcgis", "get_simpsons_diversity_index"]

from . import arcgis
from .stats import get_simpsons_diversity_index
