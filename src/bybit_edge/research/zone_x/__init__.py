"""Zone X measurement programme 1 (DEC-104 E4 (c)): second-moment measurements on the daily panel.

IK-05 (``ik05_rmt``): random-matrix factor count of the residual correlation matrix of daily returns.
IK-04 (``ik04_moments``): moments for the minimal null world (tails, cross-sectional dispersion, clustering).
Shared pieces (zone guard, loader, panel arithmetic, output schema) live in ``common``; the command line
is ``run_zone_x_1``.

Zone X = data before 2024-07-01 (and from 2021-01-01 on for this stream).  The programme never outputs a mean
or a sign of a return and never a time series of returns; ``common.validate_output`` enforces that.
"""
