Simpson Index Documentation
=============================================================================================================

Gini-Simpson Index
------------------

Simpson's Index of diversity quantifies the probability of two randomly selected single samples from a
population will be the same. The formula for calculating Simpson's Index (:math:`D`) is:

.. math::

   D = \frac {\displaystyle \sum n_i (n_i - 1)} {N (N - 1)}

:math:`n_i` = count in the category

:math:`N` = entire population count

Applied to geographic analysis the entire population is the total count within a geographic area. In the United
States, typically this is a standard Census geographic area such as a block group or tract. Within these
geographic areas, the population is segmented into categories by some defining characteristic, with a count of
the population assigned to each of the categories. This is

Simpson's Index however, is somewhat counterintuitive. The lower the number, the higher the diversity.
Consequently, typically Simpson's Index is calculated using the *Gini-Simpson Index* formula, calculating the
*inverse* of Simpson's Index.

.. math::

   D = 1 - \left ( \frac {\displaystyle \sum n_i (n_i - 1)} {N (N - 1)} \right )

The Gini-Simpson Index is the implementation in the tooling included with this package.

Contents
========

.. toctree::
    :maxdepth: 3

    ArcGIS Pro Toolbox - Simpson Index Toolbox<simpson-index-toolbox>
    API - Python Package Documentation<api-index-creation>
