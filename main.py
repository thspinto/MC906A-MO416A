#!/usr/bin/env python3
#
# Copyright 2016 (C) Thiago Pinto.
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

"""Scrum story attribution algorithm

        Genetic algorithm that attributes stories to the next sprint of the development
    teams otimizing the project's cost and aggregated value.
"""
__author__ = "Thiago Pinto"

import sys
import csv
import json


def main():
    """Import information and execute algorithm

        Import scrum data, algorithm configuration and execute algorithm.

        Input:
            backlog: backlog in CSV
            team_specs: team specifications in CSV
            parameters: algorithm configuration in alg_config.json

        Output:

    """

    check_args()
    backlog = parse_csv(sys.argv[1])
    team_specs = parse_csv(sys.argv[2])
    parameters = parse_json(sys.argv[3])

    for config in parameters:
        #execute algorithm with configuration



def parse_json(file_name):
    """Parse JSON file
    """
    with open(file_name) as jfile:
        return json.loads(jfile.read())


def parse_csv(file_name):
    """Parse CSV file

        Parses de CSV file and returns the data without the header.
    """
    data = []
    with open(file_name, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            data.append(row)
    return data[1:]


def check_args():
    """Check command line arguments and print help text

        Expected call:
            ./main.py <backlog.csv> <teams.csv> <alg_config.json>

        File format example can be seen in /data directory
    """
    if len(sys.argv) != 4:
        print("Expected arguments: ./main.py <backlog.csv> <teams.csv> <alg_config.json>")
        exit(-1)


if __name__ == '__main__':
    sys.exit(main())
