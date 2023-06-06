__title__ = 'index-creation'
__version__ = '0.1.0'
__author__ = 'Joel McCune'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2023 by Joel McCune'

__all__ = ['arcgis', 'get_simpsons_diversity_index']

from typing import Union, Iterable


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
    sd_idx = 1 - (sum(get_percent_of_n(n, N)**2 for n in data if n != 0))

    return sd_idx
