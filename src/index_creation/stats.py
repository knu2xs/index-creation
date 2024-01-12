from typing import Optional, Union, Iterable

import pandas as pd

__all__ = ["get_simpsons_diversity_index", "add_std_quartile_cols"]


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
        df['simpsons_diversity_index'] = df.apply(lambda r: get_simpsons_diversity_index(r), axis=1)

    """
    # get the total population
    N = sum(data)

    # calculate simpson's diversity index using the helper function above
    sd_idx = 1 - (sum(get_percent_of_n(n, N) ** 2 for n in data if n != 0))

    return sd_idx


def add_std_quartile_cols(
    data: Union[pd.DataFrame, pd.Series], column_name: Optional[str]
) -> pd.DataFrame:
    """
    Add standard deviation and quartile columns to describe column values to a Pandas data frame.

    Args:
        data: Pandas ``DataFrame`` or ``Series`` to get descriptive statistics for.
        column_name: Column name to get descriptive statistics for.
    """
    # create name for the columns to be added for standard deviation and quartile columns
    std_col = f"{column_name}_std"
    quartile_col = f"{column_name}_quartile"

    # if a data frame, extract the column as a series
    if isinstance(data, pd.DataFrame):
        col_srs = data[column_name]
        df = data

    # otherwise, use the series as a starting point for creating a data frame
    else:
        col_srs = data
        df = data.to_frame(name=column_name)

    # use describe to get descriptive statistics to use for column calculations
    desc = col_srs.describe()

    # assign the standard deviation for each of the literal values
    df[std_col] = (df[column_name] - desc["mean"]) / desc["std"]

    # assign the relevant quartile to each of the columns
    df.loc[df[column_name] <= desc["25%"], quartile_col] = 1
    df.loc[
        (df[column_name] > desc["25%"]) & (df[column_name] <= desc["50%"]), quartile_col
    ] = 2
    df.loc[
        (df[column_name] > desc["50%"]) & (df[column_name] <= desc["75%"]), quartile_col
    ] = 3
    df.loc[df[column_name] > desc["75%"], quartile_col] = 4

    # cast to integer
    df[quartile_col] = df[quartile_col].astype("int64")

    return df
