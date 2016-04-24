# Copyright 2016 (C) Thiago Pinto.
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

"""Genetic algorithm implementation

        The algorithm consideres the following factors:
            - story priority;
            - story size in sprint points;
            - teams implementation speed in story points per hour;
            - story dependency (with other stories)
            - team cost (in $ per hour)
"""

__author__ = "Thiago Pinto"
